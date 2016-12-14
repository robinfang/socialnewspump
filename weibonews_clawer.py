#!/usr/bin/env python
#encoding:utf-8
import os
import urllib2
import MySQLdb
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import *
import re

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

#下载html
def download(page_url):
    #参数判断
    if page_url is None:
        return None
    req = urllib2.Request(page_url)
    req.add_header("User-Agent","Mozilla/5.0 (Windows NT 6.1; rv:21.0) Gecko/20100101 Firefox/21.0")
    response = urllib2.urlopen(req)
    #获取失败
    if response.getcode() != 200:
        return None
    return response.read()
    
#用户名转uid处理
def nickname_to_uid(nickname,driver):
    search_url = "http://s.weibo.com/user/%s"%nickname
    driver.get(search_url)
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="pl_user_noResult"]')))
    warning = driver.find_element_by_xpath('//*[@id="pl_user_noResult"]').text
    print "warning:"+warning
    if len(warning) != 0:
        print "1------"
        return None
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//a[@class="W_texta W_fb"]')))
    uid = driver.find_elements_by_xpath('//a[@class="W_texta W_fb"]')[0].get_attribute('uid')
    return uid

def get_userfans(uid):
    page_url = "http://service.weibo.com/widget/widget_blog.php?uid=%s&height=1700&skin=wd_01&showpic=1" % (uid)
    html_cont =  download(page_url)
    dom = get_dom(html_cont)
    userfans = dom.xpath('//*[@class="userfans"]/a/text()')[0]
    userfans_num = re.findall(r'\d+',userfans)[0]
    return userfans_num
 
def get_dom(html_cont):
    if html_cont is None:
        return
    return etree.HTML(html_cont)

def time_format(new_time):
    time_model1 = datetime.now().strftime('%Y-%m-%d')
    time_model2 = datetime.now().strftime('%Y-%m-%d %H:')
    time_model3 = datetime.now().strftime('%Y-')
    
    if '今天' in new_time:
        time0 = new_time.split('今天')[-1]
        time0 = time_model1 + time0
    elif '分钟' in new_time:
        time0 = new_time.split('分钟前')[0]
        if int(datetime.now().strftime('%M'))-int(time0)>0:
            time_m = int(datetime.now().strftime('%M'))-int(time0)
            if time_m < 10:
                time_m = '0' + str(time_m)
            time0 = time_model2 + str(time_m)
        else:
            time_m = (int(datetime.now().strftime('%M'))-int(time0))%60
            time_h = int(datetime.now().strftime('%H'))-1
            if time_m < 10:
                time_m = '0' + str(time_m)
            if time_h < 10:
                time0 = time_model1 + ' 0' + str(time_h) + ':' +str(time_m)
            time0 = time_model1 + ' ' + str(time_h) + ':' +str(time_m)
    elif "月" in new_time:
        time_mon = new_time.split('月')[0]
        if int(time_mon) < 10:
            time_mon = '0' +time_mon
        time_day = new_time.split('月')[1].split('日')[0]
        if int (time_day) < 10:
            time_day = '0' + time_day
        tm = new_time.split(' ')[1]
        time0 = time_model3+time_mon+'-'+time_day+' '+tm
    return time0

#解析html    
def parse(uid0,html_cont,new_urls,dirver):
    dom = get_dom(html_cont)
    username = dom.xpath('//div[@class="userNm txt_b"]/text()')[0]
    userfans = dom.xpath('//div[@class="userfans"]/a/text()')[0]
    userfans_num = int(re.findall(r'\d+',userfans)[0])
    user = (uid0,username,userfans_num)
    insert_sql0 = 'INSERT IGNORE INTO weibouser(uid ,username,fans) VALUES (%s,%s,%s)'
    cursor.execute(insert_sql0,user)
    content_field = dom.xpath('//*[@id="content_all"]/div[@class = "wgtCell"]')
    
    for each in content_field:
        new_text = ' '.join(each.xpath('div[@class = "wgtCell_con"]/p/text()|div[@class = "wgtCell_con"]/p/a/text()'))
        new_text0 = each.xpath('div[@class = "wgtCell_con"]/p')[0].text
        pid_href = each.xpath('div[@class = "wgtCell_con"]/div[@class = "wgtCell_txtBot"]/span[1]/a/@href')[0]
        pid = pid_href.split('/')[-1] #微博标识
        if new_text0 == "转发了":#转发微博
            source_href = each.xpath('div[@class = "wgtCell_con"]/p/a[1]/@href')[0]
            source_nickname = each.xpath('div[@class = "wgtCell_con"]/p/a[1]/@title')[0] 
            if '/u/' in source_href:
                source_uid = source_href.split('/')[-1].encode('utf-8')
            else:
                select_sql = 'SELECT uid from weibouser where username = %s'
                cursor.execute(select_sql,(source_nickname,))
                have_uid = cursor.fetchone() #用户在数据库已存在
                if have_uid != None:
                    source_uid = have_uid[0]
                elif len(source_nickname)!=0:
                    source_uid = nickname_to_uid(source_nickname,dirver)
                    if source_uid == None:
                        print "2------"
                        continue
                else:
                    continue
            source_url = "http://service.weibo.com/widget/widget_blog.php?uid=%s&height=1700&skin=wd_01&showpic=1" % (source_uid)
            new_urls.append(source_url)
            userfans = get_userfans(source_uid)
            user = (str(source_uid),source_nickname,userfans)
            insert_sql1 = 'INSERT IGNORE INTO weibouser(uid,username,fans) VALUES (%s,%s,%s)'
            cursor.execute(insert_sql1,user)
            db.commit()
            forwarding=(pid,source_uid,uid0)
            insert_sql3 = 'INSERT IGNORE INTO weiboforwarding(pid,from_uid,to_uid) VALUES (%s,%s,%s)'
            cursor.execute(insert_sql3,forwarding)
            db.commit()
        new_time = each.xpath('div[@class = "wgtCell_con"]/div[@class = "wgtCell_txtBot"]/span[@class = "wgtCell_tm"]/a')[0].text #微博发布时间
        time0 = time_format(str(new_time))
        new_comment_times = each.xpath('div[@class = "wgtCell_con"]/div[@class = "wgtCell_txtBot"]/span[@class = "wgtCell_cmt"]/a[1]')[0].text #微博评论数
        if len(re.findall(r'\d+',new_comment_times))!=0: #评论数为0的处理
            comment_times = re.findall(r'\d+',new_comment_times)[0]
        else:
            comment_times = 0
        new_forwarding_times = each.xpath('div[@class = "wgtCell_con"]/div[@class = "wgtCell_txtBot"]/span[@class = "wgtCell_cmt"]/a[2]')[0].text #微博转发数
        if len(re.findall(r'\d+',new_forwarding_times))!=0: #转发数为0的处理
            forwarding_times = re.findall(r'\d+',new_forwarding_times)[0]
        else:
            forwarding_times = 0
        post = (pid,uid0,new_text.encode('utf-8'),time0,comment_times,forwarding_times)
        insert_sql2 =  'INSERT IGNORE INTO weibopost(pid,uid,text,time,forwarding_times,comment_times) VALUES (%s,%s,%s,%s,%s,%s)'
        cursor.execute(insert_sql2,post)
        db.commit()
    return new_urls
        #print pid,uid0[0],new_text.encode("gb18030"),new_time,new_comment_times,comment_times,new_forwarding_times,forwarding_times

def craw(enter_url):
    new_urls = [] #待爬取的URL集合
    old_urls = [] #已爬取的URL集合
    user_count = 0 #已爬取用户数量
    new_urls.append(enter_url)
    driver = webdriver.Chrome()
    while len(new_urls)!=0: #如果有待爬取的URL
        new_url = new_urls.pop(0)
        print new_url
        if new_url in old_urls:
            continue
        uid0 = new_url.split('=')[1].split('&')[0]
        old_urls.append(new_url) #添加到已爬取的URL
        #下载html页面，下载页面存储在html_cont中
        html_cont = download(new_url)
        #解析html，得到微博数据
        user = parse(uid0,html_cont,new_urls,driver)
        user_count = user_count + 1
        print user_count
        #if user_count == count:
        #    break
    driver.close()

#main函数
if __name__ == "__main__":
    #打开数据库连接
    db = MySQLdb.connect(host = "localhost",user="root",passwd="root123456",db="weibo",port=3306,charset="utf8")
    #使用cursor（）方法获取操作游标
    cursor = db.cursor()
    cursor.execute('SELECT uid FROM weibouser')
    uid = '3217179555'
    #爬虫入口url
    enter_url = "http://service.weibo.com/widget/widget_blog.php?uid=%s&height=1700&skin=wd_01&showpic=1" % (uid)
    #count = 50 #爬取微博用户的数量
    craw(enter_url)
