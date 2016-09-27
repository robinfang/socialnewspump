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

import time
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

#用户名转uid处理
def nickname_to_uid(nickname):
    search_url = "http://s.weibo.com/user/%s"%nickname
    driver = webdriver.Chrome()
    #driver = webdriver.PhantomJS()
    driver.get(search_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//a[@class="W_texta W_fb"]')))
    uid = driver.find_elements_by_xpath('//a[@class="W_texta W_fb"]')[0].get_attribute('uid')
    driver.close()
    return uid

#下载html
def download(url):
    #参数判断
    if url is None:
        return None
    req = urllib2.Request(page_url)
    req.add_header("User-Agent","Mozilla/5.0 (Windows NT 6.1; rv:21.0) Gecko/20100101 Firefox/21.0")
    response = urllib2.urlopen(req)
    #获取失败
    if response.getcode() != 200:
        return None
    return response.read()
    
#解析html    
def parse(html_cont):
    if html_cont is None:
        return
    dom = etree.HTML(html_cont)
    content_field = dom.xpath('//*[@id="content_all"]/div[@class = "wgtCell"]')
    for each in content_field:
        new_text = ' '.join(each.xpath('div[@class = "wgtCell_con"]/p/text()'))
        new_text0 = each.xpath('div[@class = "wgtCell_con"]/p')[0].text
        if new_text0 == "转发了":
            source_href = each.xpath('div[@class = "wgtCell_con"]/p/a[1]/@href')[0]
            source_nickname = each.xpath('div[@class = "wgtCell_con"]/p/a[1]/@title')[0]
            if '/u/' in source_href:
                source_uid = source_href.split('/')[-1]

            else:
                source_uid = nickname_to_uid(source_nickname)
            user = (source_uid,source_nickname)
            insert_sql = 'INSERT IGNORE INTO weibouser(uid,username) VALUES (%s,%s)'
            cursor.execute(insert_sql,user)
            db.commit()
            print source_uid, source_nickname
        #new_time = each.xpath('div[@class = "wgtCell_con"]/div[@class = "wgtCell_txtBot"]/span[@class = "wgtCell_tm"]/a')[0].text
        #new_commentTimes = each.xpath('div[@class = "wgtCell_con"]/div[@class = "wgtCell_txtBot"]/span[@class = "wgtCell_cmt"]/a[1]')[0].text
        #new_forwardingTimes = each.xpath('div[@class = "wgtCell_con"]/div[@class = "wgtCell_txtBot"]/span[@class = "wgtCell_cmt"]/a[2]')[0].text
        #print new_text.encode("gb18030"),new_time,new_commentTimes,new_forwardingTimes


#main函数
if __name__ == "__main__":
    #打开数据库连接
    db = MySQLdb.connect(host = "localhost",user="root",passwd="root123456",db="weibo",port=3306,charset="utf8")
    #使用cursor（）方法获取操作游标
    cursor = db.cursor()
    cursor.execute('SELECT uid FROM weibouser')
    uid = cursor.fetchone()
    #爬虫入口url
    page_url = "http://service.weibo.com/widget/widget_blog.php?uid=%s&height=1700&skin=wd_01&showpic=1" % (uid)
    #下载html页面，下载页面存储在html_cont中
    html_cont =  download(page_url)
    #解析html，得到微博数据
    user = parse(html_cont)
