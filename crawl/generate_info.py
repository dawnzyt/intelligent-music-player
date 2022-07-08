import time
import requests
import cloudmusic


def get_info(ids):
    '''
    调用cloudmusic库通过歌单id爬取歌曲并返回music实例对象

    :param ids: 歌单id列表[id1,id2]
    :return:
    '''
    music_info = []

    # https://music.163.com/playlist?id=6843808070
    playlists = []

    for id in ids:
        # print(id)
        ti = time.time()
        while 1:
            try:  # 这里是网络连接不正常的error
                playlist = cloudmusic.getPlaylist(str(id))
            except requests.exceptions.ConnectionError:
                playlist = []
                print('请检查网络连接是否正常......')
                break
            # 网络繁忙返回的是空list[],这里加个循环。
            if playlist != []:
                break
            print('歌单加载失败,网络繁忙....正在重试....')
        playlists.extend(playlist)
        # 打印歌单标题 歌单作者 歌单简介
        ti = time.time()
        for i in range(len(playlist)):
            music = playlist[i]
            music_url = "https://music.163.com/#/song?id=" + str(music.id)
            # music_info.append([music.name, music.artist[0], music.album,music_url,music.picUrl,music.type,music.id])
    return playlists
