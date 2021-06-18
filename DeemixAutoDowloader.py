import os
import queue
import subprocess
import json
import time
from datetime import datetime, timedelta
from threading import Thread

import deemix.app.cli as cli
import deezer
from html.parser import HTMLParser
from deemix.app.queuemanager import logger

encode_q = queue.Queue(1)
lock_encoder = None


def edit_config():
    f = open('config.json', )
    config = json.load(f)
    f.close()
    config['createArtistFolder'] = True
    config['albumNameTemplate'] = '%album%'
    config['createSingleFolder'] = True
    config['overwriteFile'] = 'e'
    with open("config.json", "w") as outfile:
        json.dump(config, outfile)


def q(job):
    global lock_encoder
    if not encode_q.full() and lock_encoder is False:
        lock_encoder = True
        encode_q.put(job.start())


class StartEncoder(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.run()

    def run(self):
        global lock_encoder
        subprocess.call(['./alac_convert.sh'])
        lock_encoder = False
        return


class Parse(HTMLParser):

    def __init__(self):
        super().__init__()
        self.reset()
        self.found_script = False
        self.albums = {}

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.found_script = True

    def handle_data(self, data):
        if self.found_script:
            try:
                albums_dict = json.loads(data.strip('window.__DZR_APP_STATE__ = '))
                self.albums = albums_dict
            except Exception as e:
                pass
            self.found_script = False


class ManualDownloader(Thread):

    def __init__(self, albumId):
        Thread.__init__(self)
        self.daemon = True
        self.albumId = albumId
        self.start()

    def run(self):
        setup()
        test = cli.cli('./music', './')
        edit_config()
        test.login()
        deezer_sesh = test.dz.session
        deezer_headers = test.dz.http_headers
        deezer_api = deezer.API(deezer_sesh, deezer_headers)
        if add_to_lib(id=self.albumId):
            global lock_encoder
            lock_encoder = True
            try:
                bitrate = os.environ['bitrate']
            except Exception as e:
                bitrate = 'flac'

            test.qm.addToQueue(dz=test.dz, url=f'https://www.deezer.com/en/album/{self.albumId}',
                               settings=test.set.settings, bitrate=bitrate)
            lock_encoder = False
            q(StartEncoder())


class Downloader(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def run(self):
        setup()
        urls = os.environ['urls']
        urls_list = urls.split(',')
        new = False
        while True:
            for url in urls_list:
                test = cli.cli('./music', './')
                edit_config()
                test.login()
                deezer_sesh = test.dz.session
                deezer_headers = test.dz.http_headers
                deezer_api = deezer.API(deezer_sesh, deezer_headers)
                albums = api_call_test(url.strip(), deezer_sesh, deezer_headers)
                for album in albums:
                    new = False
                    if add_to_lib(id=album):
                        new = True
                        global lock_encoder
                        lock_encoder = True
                        test.qm.addToQueue(dz=test.dz, url=f'https://www.deezer.com/en/album/{album}',
                                           settings=test.set.settings, bitrate=os.environ['bitrate'])
                        lock_encoder = False
                        q(StartEncoder())
                if not new:
                    logger.info('No new albums found today')

            logger.info('Running audio conversion')
            wait_to_tomorrow()


def album_id_stripper(albums_dict):
    id_list = []
    for item in albums_dict['sections'][0]['items']:
        id_list.append(item['id'])
    return id_list


def api_call_test(url, deezer_sesh, deezer_headers):
    result = deezer_sesh.get(
        url,
        headers=deezer_headers,
        timeout=30
    )
    json_ = result.text
    testParser = Parse()
    testParser.feed(json_)
    albums = testParser.albums
    return album_id_stripper(albums)


def add_to_lib(id):
    with open('deemix_db/library.json') as json_file:
        lib = json.load(json_file)
        for entries in lib:
            if lib[entries] == id:
                return False
        lib[len(lib) + 1] = id
    with open('deemix_db/library.json', 'w+') as outfile:
        json.dump(lib, outfile)
        return True


def setup():
    if not os.path.exists("deemix_db/library.json"):
        if not os.path.exists('deemix_db/'):
            os.system('mkdir deemix_db')
        f = open("deemix_db/library.json", "w")
        f.write('{}')
        f.close()


def wait_to_tomorrow():
    """Wait to tommorow 8:00 am"""

    tomorrow = datetime.replace(datetime.now() + timedelta(days=1),
                                hour=8, minute=0, second=0)
    delta = tomorrow - datetime.now()
    logger.info(f'Check was completed at {datetime.now()} sleeping for {delta}')
    time.sleep(delta.seconds)
