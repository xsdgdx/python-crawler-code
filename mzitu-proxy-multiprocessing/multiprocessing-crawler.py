import threading
import multiprocessing
from mongodb_queue import MogoQueue
from Download import request
from bs4 import BeautifulSoup
import re
import time
import sys
import os
def restart_program():
  python = sys.executable
  os.execl(python, python, * sys.argv)

SLEEP_TIME = 1
L = threading.RLock()
def mzitu_crawler(max_threads=10):
    crawl_queue = MogoQueue('meinvxiezhenji','crawl_queue') ##这个是我们获取URL的队列
    img_queue = MogoQueue('meinvxiezhenji','img_queue') ##这个是图片实际URL的队列
    def pageurl_crawler():
        L.acquire()
        while True:
            try:
                url = crawl_queue.pop()
                print(url)
            except KeyError:
                print('队列没有数据')
                break
            else:
                img_urls = []
                req = request.get(url, 3).text
                title = crawl_queue.pop_title(url)
                path = str(title).replace('?', '')##测试过程中发现一个标题有问号
                path = re.sub(r'[？\\*|“<>:/]', '', str(path))
                mkdir(path)
                os.chdir('E:\图片\mzitu\\' + path)
                max_span = BeautifulSoup(req, 'lxml').find('div', class_='pagenavi').find_all('span')[-2].get_text()
                for page in range(1, int(max_span) + 1):
                    page_url = url + '/' + str(page)
                    img_html = request.get(page_url, 3)  ##这儿更改了一下（是不是发现  self 没见了？）
                    img_url = BeautifulSoup(img_html.text, 'lxml').find('div', class_='main-image').find('img')['src']
                    name = BeautifulSoup(img_html.text, 'lxml').find('h2', class_='main-title').get_text()
                    name = re.sub(r'[？\\*|“<>:/]', '', str(name))
                    img_urls.append(img_url)
                    print(u'开始保存：', img_url,name)
                    img = request.get(img_url, 3, referer=page_url)
                    f = open(name + '.jpg', 'ab')
                    f.write(img.content)
                    f.close()
                crawl_queue.complete(url) ##设置为完成状态
                img_queue.push_imgurl(title, img_urls)
                print('插入数据库成功')
        L.release()


    def mkdir(path):
        path = path.strip()
        path = re.sub(r'[？\\*|“<>:/]', '', str(path))
        isExists = os.path.exists(os.path.join("E:\图片\mzitu", path))
        if not isExists:
            print(u'建了一个名字叫做', path, u'的文件夹！')
            os.makedirs(os.path.join("E:\图片\mzitu", path))
            return True
        else:
            print(u'名字叫做', path, u'的文件夹已经存在了！')
            return False

    threads = []
    while threads or crawl_queue:
        """
        这儿crawl_queue用上了，就是我们__bool__函数的作用，为真则代表我们MongoDB队列里面还有数据
        threads 或者 crawl_queue为真都代表我们还没下载完成，程序就会继续执行
        """
        for thread in threads:
            if not thread.is_alive(): ##is_alive是判断是否为空,不是空则在队列中删掉
                threads.remove(thread)
        while len(threads) < max_threads or crawl_queue.peek(): ##线程池中的线程少于max_threads 或者 crawl_qeue时
            thread = threading.Thread(target=pageurl_crawler) ##创建线程
            thread.setDaemon(True) ##设置守护线程
            thread.start() ##启动线程
            threads.append(thread) ##添加进线程队列
        time.sleep(SLEEP_TIME)
def process_crawler():
    process = []
    num_cpus = multiprocessing.cpu_count()
    print('将会启动进程数为：', num_cpus)
    for i in range(num_cpus):
        p = multiprocessing.Process(target=mzitu_crawler) ##创建进程
        p.start() ##启动进程
        process.append(p) ##添加进进程队列
    for p in process:
        p.join() ##等待进程队列里面的进程结束

if __name__ == "__main__":
    process_crawler()
    time.sleep(300)
    restart_program()

