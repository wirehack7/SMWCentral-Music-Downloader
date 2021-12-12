#!/bin/python3
# coding=utf8

from bs4 import BeautifulSoup
import logging
import requests
import urllib
import pprint
import datetime
import random
import re
import os
import pickle

pp = pprint.PrettyPrinter(indent=4)

logging.basicConfig(filename='runtime.log', filemode='w',
                    format='%(asctime)s %(process)d %(module)s:%(funcName)s %(levelname)s: %(message)s',
                    level=logging.DEBUG)

agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 '
    'Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 '
    'Safari/537.36 Edg/89.0.774.68',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 '
    'Safari/537.36 OPR/75.0.3969.149',
    'Mozilla/5.0 (Linux; Android 7.1.2; DSCS9 Build/NHG47L; wv) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Version/4.0 Chrome/80.0.3987.149 Safari/537.36 '
]
headers = {
    'User-Agent': random.choice(agents)
}


def get_songs(url):
    try:
        r = requests.get(url, headers=headers)
    except Exception as e:
        logging.error("Failed to load website: %s", e)
        return 0

    soup = BeautifulSoup(r.text, features="html.parser")
    if soup.find('div', id='list_content'):
        songs = []
        songs_children = soup.find('div', id='list_content').find_all("a", {'href': re.compile("a=details&id="
                                                                                              "[0-9]{1,}")})
        for link in songs_children:
            regex = re.compile("\[…\]")
            if not re.search(regex, str(link)):
                title = re.sub('<.*?>', "", str(link))
                print(title)
    else:
        return 0


def get_songlist(url):
    try:
        r = requests.get(url, headers=headers)
    except Exception as e:
        logging.error("Failed to load website: %s", e)
        return 0

    soup = BeautifulSoup(r.text, features="html.parser")
    if soup.find(id='menu'):
        item_numbers = soup.find(id='menu').findAll("span", {"class": "stats"}, text=True)
        total_songs = int(re.sub('<.*?>', "", str(item_numbers[2])))
        logging.info("Found total number of songs: %s", str(total_songs))
        menu_links = soup.find(id='menu').findAll("a", {'title': re.compile("^Go")}, text=True)
        max_page = int(re.sub('<.*?>', "", str(menu_links[4])))
        logging.info("Found total number of pages: %s", str(max_page))
        get_songs("https://www.smwcentral.net/?p=section&s=smwmusic&u=0&g=0&n=1&o=date&d=desc")
    else:
        return 0


if not os.path.isdir('songs'):
    os.mkdir('songs')

music = get_songlist('https://www.smwcentral.net/?p=section&s=smwmusic&u=0&g=0&n=1&o=date&d=desc')
