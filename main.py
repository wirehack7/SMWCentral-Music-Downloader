#!/bin/python3
# coding=utf8

from bs4 import BeautifulSoup
import logging
import requests
import pprint
import random
import re
import os
import time
from multiprocessing.pool import ThreadPool
from zipfile import ZipFile
import tqdm
from urllib.parse import urlparse

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

songs = []


def get_songs(url):
    try:
        r = requests.get(url, headers=headers)
    except Exception as e:
        logging.error("Failed to load website: %s", e)
        return 0

    soup = BeautifulSoup(r.text, features="html.parser")
    if soup.find('div', id='list_content'):
        songs_children = soup.find('div', id='list_content').find_all("a", {'href': re.compile("a=details&id="
                                                                                               "[0-9]{1,}")})
        for link in songs_children:
            regex = re.compile("\[…\]")
            if not re.search(regex, str(link)):
                title = re.sub('<.*?>', "", str(link))
                regex_id = re.compile("id=[0-9]{1,}")
                id = int(re.sub('id=', "", re.search(regex_id, str(link))[0]))
                song = {'id': id, 'title': title}
                songs.append(song)
                logging.info('Found song: ID: %s Title: %s', str(id), title)
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
        print("Found " + str(max_page) + " pages")
        i = 1
        while i < (max_page + 1):
            print("Getting songs for page:", str(i), '/', str(max_page))
            get_songs("https://www.smwcentral.net/?p=section&s=smwmusic&u=0&g=0&n=" + str(i) + "&o=date&d=desc")
            i = i + 1
        return songs
    else:
        return 0


def download_songs(item):
    logging.info("Run thread: %s", str(item['id']))
    if not os.path.isdir('songs/' + str(item['id'])):
        logging.info("Fetching data and downloading: %s", str(item['title']))
        try:
            r = requests.get('https://www.smwcentral.net/?p=section&a=details&id=' + str(item['id']),
                             headers=headers)
        except:
            return 0

        soup = BeautifulSoup(r.text, features="html.parser")
        table = soup.find('table', {'class': 'generic'}).findAll('td', {'class': 'cell2'})
        for row in table:
            regex = re.compile("0x[0-9a-fA-F]{1,10}")
            match = re.search(regex, str(row))
            if match:
                size = int(match[0], 16)
        for tag in soup.findAll('a', string='Download', href=True):
            link = tag['href']
            regex = re.compile("^http")
            if not re.search(regex, str(link)):
                link = 'https:' + link
            filename = os.path.basename(urlparse(link).path)
        if not size:
            size = 0
        save = str(item['id']) + ';' + item['title'] + ';' + str(size) + ';' + link
        os.mkdir('songs/' + str(item['id']))
        f = open('songs/' + str(item['id']) + '/info.txt', "w")
        f.write(save)
        f.close()

        r = requests.get(link, stream=True, headers=headers)
        if r.status_code == 200:
            with open('songs/' + str(item['id']) + '/' + filename, 'wb') as f:
                for chunk in r:
                    f.write(chunk)
            time.sleep(1)
            zf = ZipFile('songs/' + str(item['id']) + '/' + filename, 'r')
            if zf:
                zf.extractall('songs/' + str(item['id']) + '/extracted')
                zf.close()
            time.sleep(1)

        return item['id']


if __name__ == '__main__':
    if not os.path.isdir('songs'):
        os.mkdir('songs')

    music = get_songlist('https://www.smwcentral.net/?p=section&s=smwmusic&u=0&g=0&n=1&o=date&d=desc')

    pool = ThreadPool(processes=8)
    for _ in tqdm.tqdm(pool.imap_unordered(download_songs, music), total=len(music)):
        pass

    pool.terminate()
