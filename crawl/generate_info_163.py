from pycloudmusic163 import Music163


def get_info(id):
    # 默认请求头
    headers = Music163.music163_headers
    headers["cookie"] += "用户cookie"
    music163 = Music163(headers=headers)

    playlist_info = []
    music_info = []

    # https://music.163.com/playlist?id=6843808070
    playlist = music163.playlist(str(id))
    # 打印歌单标题 歌单作者 歌单简介
    playlist_info.append([playlist.name, playlist.user_str, playlist.description])

    for music in playlist:
        music_url = "https://music.163.com/#/song?id=" + str(music.id)
        music_info.append([music.name_str, music.artist_str, music_url])
    return playlist_info, music_info