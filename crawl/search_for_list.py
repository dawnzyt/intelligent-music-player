import random
import re

import cv2
import numpy as np
import requests
from selenium import webdriver
import PIL
from selenium.webdriver.chrome.options import Options
import urllib.request
import time


# 输入描述歌单类别的字符串
def get_playlist(genre, listnum=1):
    '''
    利用selenium爬取genre分类标签对应listnum数目的歌单id

    :param genre: str类型的分类标签
    :param listnum: 歌单爬取数目限制
    :return: ids，歌单id的列表
    '''
    # selenium隐藏chrome
    ti = time.time()
    driver_exe = 'chromedriver'
    options = Options()
    options.add_argument("--headless")
    url = "https://music.163.com/#/discover/playlist/?cat=" + genre

    page = webdriver.Chrome(driver_exe, options=options)
    # page = webdriver.Chrome()
    page.get(url)
    print('打开chrome用时: %.3fs' % (time.time() - ti))
    # selenium
    ti = time.time()
    iframe = page.find_element_by_id('g_iframe')
    page.switch_to.frame(iframe)
    playlists = [page.find_element_by_xpath(f'//ul[@class="m-cvrlst f-cb"]/li[{num}]/div/div/a') for
                 num in range(1, 1 + listnum)]
    # photolists = [page.find_element_by_xpath(f'//ul[@class="m-cvrlst f-cb"]/li[{num}]/div/img') for num
    #               in range(1, 33)]
    ids = [playlist.get_attribute("data-res-id") for playlist in playlists]
    # pic_url = [photolist.get_attribute("src") for photolist in photolists]
    page.close()
    print('selenium爬取id用时: %.3fs' % (time.time() - ti))
    # 通过request下载imgs_list
    # pics = []
    # for each in pic_url:
    #     pic = requests.get(each, timeout=10).content
    #     nparr = np.frombuffer(pic, np.uint8)
    #     img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    #     pics.append(img)
    return ids
