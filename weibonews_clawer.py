#!/usr/bin/env python
#coding:utf-8
import os
import urllib2
from lxml import etree

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

#html下载器
class HtmlDownloader(object):
    
    def download(self, url):
        #参数判断
        if url is None:
            return None
        response = urllib2.urlopen(page_url)
        #获取失败
        if response.getcode() != 200:
            return None
        return response.read()
        
class parser(object):

    def parse(self,html_cont):
        if html_cont is None:
            return
        dom = etree.HTML(html_cont)
        content_field = dom.xpath('//*[@id="content_all"]/div[@class = "wgtCell"]')
        for each in content_field:
            new_text = ' '.join(each.xpath('div[@class = "wgtCell_con"]/p/text()'))
            new_time = each.xpath('div[@class = "wgtCell_con"]/div[@class = "wgtCell_txtBot"]/span[@class = "wgtCell_tm"]/a')[0].text
            new_commentTimes = each.xpath('div[@class = "wgtCell_con"]/div[@class = "wgtCell_txtBot"]/span[@class = "wgtCell_cmt"]/a[1]')[0].text
            new_forwardingTimes = each.xpath('div[@class = "wgtCell_con"]/div[@class = "wgtCell_txtBot"]/span[@class = "wgtCell_cmt"]/a[2]')[0].text
            print new_text.encode("gb18030"),new_time,new_commentTimes,new_forwardingTimes
#Spider
class Spider(object):
    #构造函数
    def __init__(self):
        #初始化=下载器，解析器，输出器
        self.downloader = HtmlDownloader()
        self.parser = parser()
    
    def craw(self, page_url):
        #启动下载器，下载页面存储在html_cont中
        html_cont = self.downloader.download(page_url)
        #启动解析器，得到微博数据并打印
        news = self.parser.parse(html_cont)

#main函数
if __name__ == "__main__":
    
    try:
        f = open("uid.txt")
    except:
        print 'Open fail.'
    for line in f:
        uid = line.strip('\n')
        #爬虫入口url
        page_url = "http://service.weibo.com/widget/widget_blog.php?uid=%s&height=1700&skin=wd_01&showpic=1" % (uid)
        #创建爬虫对象
        obj_spider = Spider()
        #调用craw方法
        obj_spider.craw(page_url)
        
        if uid == None:
            f.close()
            break