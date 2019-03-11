import os
import json
import requests
import pymongo
from  urllib.parse import urlencode
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import re
from config import *
from hashlib import md5
from multiprocessing import Pool
from json.decoder import JSONDecodeError

client = pymongo.MongoClient(MONGO_URL,connect=False)
db = client[MONGO_DB]
keyword='街拍'
def get_page_index(offset,keyword):
    params={
    'offset':offset,
     'format':'json',
     'keyword':keyword,
     'autoload':'true',
     'count':'20',
     'cur_tab':3,
     'from':'gallery'
    }
    url='http://www.toutiao.com/search_content/?'+urlencode(params)
    try:
        response=requests.get(url)
        if response.status_code==200:
            return response.text
        return None
    except RequestException:
        print('请求索引页出错')
        return None
def parse_page_index(html):
    try:
        data=json.loads(html)
        if data and 'data'in data.keys():
            for item in data.get('data'):
                yield item.get('article_url')
    except JSONDecodeError:
        pass
def get_page_detail(url):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36'}
    try:
        response=requests.get(url,headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求详情页出错')
        return None
def parse_page_detail(html,url):
    soup=BeautifulSoup(html,'lxml')
    title=soup.select('title')[0].get_text()
    images_pattern=re.compile('parse\((.*?)\)',re.S)
    result=re.search(images_pattern,html)
    if result:
        data=json.loads(json.loads(result.group(1)))
        if data and 'sub_images' in data.keys():
            sub_images=data.get('sub_images')
            images=[item.get('url')for item in sub_images]
            for image in images: download_image(image)
            return{
                'title':title,
                'url':url,
                'images':images,
                    }
def download_image(url):
    print('正在下载',url)
    try:
        response=requests.get(url)
        if response.status_code == 200:
            save_image(response.content)
        return None
    except RequestException:
        print('请求图片出错',url)
        return None
def save_image(content):
    file_path='{0}/{1}.{2}'.format('E:\\图片\\街拍',md5(content).hexdigest(),'jpg')
    if not os.path.exists(file_path):
        with open(file_path,'wb')as f:
            f.write(content)
            f.close()
def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        return True
    return False
def main(offset):
    html=get_page_index(offset,keyword)
    for url in parse_page_index(html):
        url='https://www.toutiao.com/a'+url[25:]
        html=get_page_detail(url)
        if html:
            result=parse_page_detail(html,url)
            if result:save_to_mongo(result)

if __name__=='__main__':
    pool = Pool()
    groups = [x * 20 for x in range(GROUP_START, GROUP_END + 1)]
    pool.map(main, groups)