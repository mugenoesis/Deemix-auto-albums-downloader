import os
from shutil import copyfile
import ffmpeg
from pathlib import Path


def encoder(elem, dir_name):
    extension = ''.join(elem.split('.')[-1])
    file_path_no_extension = ''.join(elem.split(extension)[0])
    file_name_no_path = ''.join(elem.split('/')[-1])
    file_path_no_name = ''.join(elem.split(file_name_no_path)[0]).split(dir_name)[1]
    if extension == 'flac' or extension == 'm4a':
        probe = ffmpeg.probe(elem)
        if probe['streams'][0]['sample_rate'] > '44100' or probe['streams'][0]['bits_per_raw_sample'] > '16':
            Path(dir_name + "/../cd/" + file_path_no_name).mkdir(parents=True, exist_ok=True)
            Path(dir_name + "/../hi-res/" + file_path_no_name).mkdir(parents=True, exist_ok=True)
            copyfile(elem, dir_name + '/../hi-res/' + file_path_no_name + file_name_no_path)
            cd_location = dir_name + "/../cd/" + file_path_no_name + file_name_no_path

            if int(probe['streams'][0]['sample_rate']) >= 44100:
                sample_rate = 44100
            else:
                sample_rate = probe['streams'][0]['sample_rate']

            if int(probe['streams'][0]['bits_per_raw_sample']) >= 16:
                bit_rate = 16
            else:
                bit_rate = probe['streams'][0]['bits_per_raw_sample']

            os.system(
                f'ffmpeg -i "{elem}" -acodec alac -ar {sample_rate} -sample_fmt s{bit_rate}p -vn  "{cd_location}"')
            os.system(f'rm "{elem}"')
        elif extension == 'flac':
            os.system(
                f'ffmpeg -i "{elem}" -acodec alac -ar 44100 -sample_fmt s16p -vn  "{file_path_no_extension}m4a"')
            os.system(f'rm "{elem}"')


def encode_files():
    dir_name = './music'
    Path(dir_name + "/../hi-res ").mkdir(parents=True, exist_ok=True)
    Path(dir_name + "/../cd").mkdir(parents=True, exist_ok=True)

    list_of_files = list()
    for (dir_path, dir_names, filenames) in os.walk(dir_name):
        list_of_files += [os.path.join(dir_path, file) for file in filenames]

    for elem in list_of_files:
        encoder(elem, dir_name)
