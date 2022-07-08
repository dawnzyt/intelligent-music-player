import os

from pydub import AudioSegment


def trans_mp3_to_other(filepath, hz):
    song = AudioSegment.from_mp3(filepath)
    song.export("Newsound." + str(hz), format=str(hz))


def trans_wav_to_other(filepath, hz):
    song = AudioSegment.from_wav(filepath)
    song.export("Newsound." + str(hz), format=str(hz))


def trans_ogg_to_other(filepath, hz):
    song = AudioSegment.from_ogg(filepath)
    song.export("Newsound." + str(hz), format=str(hz))


def trans_flac_to_other(filepath, hz):
    song = AudioSegment.from_file(filepath)
    song.export("Newsound." + str(hz), format=str(hz))


def trans_m4a_to_other(rt_path,file_name, hz='mp3'):
    song = AudioSegment.from_file(rt_path+'/'+file_name)
    song.export(rt_path+'/'+file_name[:-3] + str(hz), format=str(hz))


