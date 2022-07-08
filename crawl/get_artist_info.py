from pycloudmusic163 import Music163
import cloudmusic
import requests
def artist_info(name):
    '''
    调用pycloudmusic163库，利用name爬取歌手信息

    :param name: 歌手名，通常为声纹识别结果
    :return:歌手图片url以及热门歌单歌曲
    '''
    # 默认请求头
    headers = Music163.music163_headers
    headers["cookie"] += "用户cookie"
    music163 = Music163(headers=headers)
    try:
        artist_info = music163.search(name, type_=100)
    except requests.exceptions.ConnectionError:# 网络连接error
        print('请检查网络连接是否正常......')
        return '',[]

    #字典列表，元素依次为：歌曲名song_name，歌曲urlsong_url
    song_list = []

    artist_id = artist_info['artists'][0]['id']
    artist_pic = artist_info['artists'][0]['picUrl']
    artist_page_url = "https://music.163.com/#/artist?id=" + str(artist_id)

    artist_page = music163.artist(artist_id)
    artist_page.song(limit = 10)#limit可以根据想要多少首歌的信息来改
    for item in artist_page.music_list:
        dict_element = {}
        song_name = item['al']['name']
        song_url = "https://music.163.com/#/song?id=" + str(item['id'])
        dict_element['song_name'] = song_name
        dict_element['song_id'] = song_url

        song_list.append(item['id'])

    #返回元素依次为：歌手姓名，歌手图片URL，歌手代表歌曲列表
    return artist_pic, song_list