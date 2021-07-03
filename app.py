import os
import signal
import time
from threading import Thread
from time import sleep
from gevent.pywsgi import WSGIServer
import requests
from plexapi.server import PlexServer
from flask import Flask, render_template, request
import logging
import DeemixAutoDowloader
import FileEncoding

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True
album_image = ''
DeemixAutoDowloader.Downloader()


class AlbumDisplay(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def run(self):
        baseurl = ''
        token = ''
        player_name = ''
        previous_album_title = ''

        while True:

            plex = PlexServer(baseurl, token)
            sessions = plex.sessions()
            for session in sessions:
                for player in session.players:
                    if player.title == player_name:
                        if previous_album_title != session.parentTitle:
                            previous_album_title = session.parentTitle
                            x = requests.get(session.thumbUrl)

                            if not os.path.isdir('static'):
                                os.mkdir('static')

                            for filename in os.listdir('static/'):
                                if filename.startswith('album'):  # not to remove other images
                                    os.remove('static/' + filename)

                            file_name = f'static/album{str(time.time())}.jpg'
                            album_image = f'album{str(time.time())}.jpg'
                            print(album_image)
                            open(file_name, 'wb').write(x.content)

                            f = open("templates/album.html", "r")
                            test = f.read()

                            f = open("templates/album.html", "w")
                            f.write(test)
                            f.close()
            sleep(1)


class FlaskThread(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def run(self):
        http_server = WSGIServer(('localhost', 5000), app)
        http_server.serve_forever()


@app.route('/download', methods=['POST', 'GET'])
def download():
    album = request.args.get('album')
    DeemixAutoDowloader.ManualDownloader(album)
    return {'response': 200}


@app.route('/encode', methods=['POST', 'GET'])
def encode():
    # DeemixAutoDowloader.q(DeemixAutoDowloader.StartEncoder())
    FileEncoding.encode_files()
    return {'response': 200}


@app.route('/', methods=['POST', 'GET'])
def home():
    return render_template('album.html', album=album_image)


class ProgramStop:
    stop = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.stop = True
