from bs4 import BeautifulSoup
import datetime
import os
import re
import pymongo
from config import *
from Download import request 
class mzitu():
    
    def __init__(self):
        client = pymongo.MongoClient(host='localhost', port=27017)
        db=client[MONGO_DB]
        self.meizitu_collection = db[MONGO_TABLE] ##在meizixiezhenji这个数据库中，选择一个集合
        self.title = '' ##用来保存页面主题
        self.url = '' ##用来保存页面地址
        self.img_urls = [] ##初始化一个 列表 用来保存图片地址
    def all_url(self, url):
        html =  request.get(url, 3) ##这儿更改了一下（是不是发现  self 没见了？）
        all_a = BeautifulSoup(html.text, 'lxml').find('div', class_='all').find_all('a')
        for a in all_a[1:]:
            title = a.get_text()
            self.title=title
            print(u'开始保存：', title) ##加点提示不然太枯燥了
            path = str(title).replace("？", ' ') ##我注意到有个标题带有 ？  这个符号Windows系统是不能创建文件夹的所以要替换掉
            self.mkdir(path)
            os.chdir('E:\图片\mzitu\\'+path)
            href=a['href']
            self.url = href ##将页面地址保存到self.url中
            if self.meizitu_collection.find_one({'主题页面': href}):  ##判断这个主题是否已经在数据库中、不在就运行else下的内容，在则忽略。
                print(u'这个页面已经爬取过了')
            else:
                self.html(href)
    def html(self, href):   ##这个函数是处理套图地址获得图片的页面地址
        html = request.get(href, 3) ##这儿更改了一下（是不是发现  self 没见了？）
        page_num=0
        max_span = BeautifulSoup(html.text, 'lxml').find('div', class_='pagenavi').find_all('span')[-2].get_text()
        for page in range(1, int(max_span) + 1):
            page_num=page_num+1
            page_url = href + '/' + str(page)
            self.img_save(page_url,max_span,page_num)

    def img_save(self, page_url,max_span,page_num): ##这个函数处理图片页面地址获得图片的实际地址
        img_html = request.get(page_url, 3) ##这儿更改了一下（是不是发现  self 没见了？）
        img_url = BeautifulSoup(img_html.text, 'lxml').find('div', class_='main-image').find('img')['src']
        name =BeautifulSoup(img_html.text, 'lxml').find('h2', class_='main-title').get_text()
        self.img_urls.append(img_url)
        if int(max_span)==page_num:
            post = {  ##这是构造一个字典，里面有啥都是中文，很好理解吧！
                '标题': self.title,
                '主题页面': self.url,
                '图片地址': self.img_urls,
                '获取时间': datetime.datetime.now()
            }
            result=self.meizitu_collection.insert_one(post) ##将post中的内容写入数据库。
            name = re.sub(r'[？\\*|“<>:/]', '', str(name))
            img = request.get(img_url,3,referer=page_url)
            f = open(name + '.jpg', 'ab')
            f.write(img.content)
            f.close()
        else:
            name = re.sub(r'[？\\*|“<>:/]', '', str(name))
            img = request.get(img_url,3,referer=page_url)
            f = open(name + '.jpg', 'ab')
            f.write(img.content)
            f.close()

    def mkdir(self, path): ##这个函数创建文件夹
        path = path.strip( )
        path = re.sub(r'[？\\*|“<>:/]', '', str(path))
        isExists = os.path.exists(os.path.join("E:\图片\mzitu", path))
        if not isExists:
            print(u'建了一个名字叫做', path, u'的文件夹！')
            os.makedirs(os.path.join("E:\图片\mzitu", path))
            os.chdir(os.path.join("E:\图片\mzitu", path)) ##切换到目录
            return True
        else:
            print(u'名字叫做', path, u'的文件夹已经存在了！')
            return False

            
Mzitu = mzitu() 
Mzitu.all_url('http://www.mzitu.com/all') ##给函数all_url传入参数  你可以当作启动爬虫（就是入口）
