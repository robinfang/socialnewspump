#!/usr/bin/env python
#encoding:utf-8
from timeformat import *
import urllib2
import json
import re
from random import *
import MySQLdb
import time

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

class Sina_Spider():

    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    headers = {'User-Agent': user_agent}
    new_uid = [] #待爬取的uid列表
    old_uid = [] #已爬取的uid列表
    count = 20 #爬取微博用户的数量，可以调整
    uid = '2891529877'#爬虫入口uid
    
    def main(self):
        uid = self.uid
        self.craw_manager(uid)
        
    def craw_manager(self,uid):
        user_count = 0 #已爬取用户数量
        self.new_uid.append(uid)
        
        while len(self.new_uid)!=0: #如果有待爬取的uid
            uid = self.new_uid.pop(0)
            if uid in self.old_uid:
                continue
            self.old_uid.append(uid) #添加到已爬取的uid
            self.start_requests(uid)
            user_count = user_count + 1
            print user_count
            if user_count == self.count:
                break

    def start_requests(self,uid):
        # to get containerid
        url = 'http://m.weibo.cn/api/container/getIndex?type=uid&value={}'.format(uid)
        t=randint(1, 5)
        time.sleep(t)
        req_start = urllib2.Request(url=url, headers=self.headers)
        response_start = urllib2.urlopen(req_start)
        content_start = json.loads(response_start.read())
        uid = content_start.get('userInfo').get('id')
        username = content_start.get('userInfo').get('screen_name')
        userfans = content_start.get('userInfo').get('followers_count')
        print uid, username, userfans
        user0 = (uid,username,userfans,userfans)
        insert_user0 = 'INSERT INTO weibouser(uid,username,fans) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE fans = %s'
        cursor.execute(insert_user0,user0)
        # here, we can get containerid
        containerid = None
        for data in content_start.get('tabsInfo').get('tabs'):
            if data.get('tab_type') == 'weibo':
                containerid = data.get('containerid')
        if containerid:
            for i in range(1,3):
                weibo_url = response_start.url + '&containerid=%s&page=%d' % (containerid,i)
                #print weibo_url
                response_contain = urllib2.Request(url=weibo_url, headers=self.headers)
                content_contain = urllib2.urlopen(response_contain)
                self.get_weibo(uid,content_contain)
            
    def get_weibo(self,uid,response):
        content = json.loads(response.read())
        for data in content.get('cards'):
            if data.get('card_type') == 9:
                if data.get('mblog').has_key('title') == False:
                    p = re.compile('<[^>]+>')
                    new_time = data.get('mblog').get('created_at')#时间
                    time = time_format(new_time.encode('utf-8'))
                    weibo_id = data.get('mblog').get('bid')#微博id
                    if data.get('mblog').has_key('raw_text'):#转发微博
                        raw_text = p.sub('',data.get('mblog').get('raw_text'))#转发理由
                        if data.get('mblog').get('retweeted_status').get('user') != None: #原作者删除微博的情况
                            source_uid = data.get('mblog').get('retweeted_status').get('user').get('id')#源uid
                            self.new_uid.append(str(source_uid))
                            source_username = data.get('mblog').get('retweeted_status').get('user').get('screen_name')#源username
                            source_userfans = data.get('mblog').get('retweeted_status').get('user').get('followers_count')#源userfans
                            print source_uid,source_username,source_userfans
                            user = (source_uid,source_username,source_userfans,source_userfans) #用户
                            insert_user = 'INSERT INTO weibouser(uid,username,fans) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE fans = %s'
                            cursor.execute(insert_user,user)
                            db.commit()
                            source_text = p.sub('',data.get('mblog').get('retweeted_status').get('text'))#源微博内容
                            text = '转发了 '+source_username+' 的微博：'+source_text+'\n转发理由：'+raw_text
                            print weibo_id,source_uid,uid #转发关系
                            forwarding=(weibo_id,source_uid,uid)
                            insert_forwarding = 'INSERT IGNORE INTO weiboforwarding(mid,from_uid,to_uid) VALUES (%s,%s,%s)'
                            cursor.execute(insert_forwarding,forwarding)
                            db.commit()
                        else:
                            continue
                    elif data.get('mblog').has_key('text'):#原创微博
                        text = p.sub('',data.get('mblog').get('text')) #微博内容
                    comment_times = data.get('mblog').get('comments_count')#评论数
                    forwarding_times = data.get('mblog').get('reposts_count')#转发数
                    print weibo_id,time,text.encode("gb18030"),comment_times,forwarding_times
                    post = (weibo_id,uid,text.encode('utf-8'),time,forwarding_times,comment_times,forwarding_times,comment_times)
                    insert_post =  'INSERT IGNORE INTO weibopost(mid,uid,text,time,forwarding_times,comment_times) VALUES (%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE forwarding_times = %s,comment_times = %s'
                    cursor.execute(insert_post,post)

if __name__ == '__main__':
    #打开数据库连接
    db = MySQLdb.connect(host = "localhost",user="root",passwd="root123456",db="weibo",port=3306,charset="utf8")
    #使用cursor（）方法获取操作游标
    cursor = db.cursor()
    test = Sina_Spider()
    test.main()