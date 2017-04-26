#!/usr/bin/env python
#encoding:utf-8

from datetime import *
import MySQLdb

#打开数据库连接
db = MySQLdb.connect(host = "localhost",user="root",passwd="root123456",db="weibo",port=3306,charset="utf8")
#使用cursor（）方法获取操作游标
cursor = db.cursor()

#评分方法
def score(a,b,c):
    uidlist=[]
    select_uidlist = 'select uid from weibouser'
    cursor.execute(select_uidlist)
    uidtuple = cursor.fetchall()
    sc_user = 0
    sc_ksum = 0
    #对每个用户进行评分
    for i in uidtuple:
        uid = i[0]
        #权重可以调整
        sc_user = score_user(uid,1.0/3,1.0/3,1.0/3) 
        sc_ksum = score_ksum(uid)
        #权重可以调整
        sc_time = score_time(uid,1.0/2,1.0/2)
        sc = (a*sc_user+b*sc_ksum+c*sc_time)*100
        if(sc_user!=0)and(sc_ksum!=0)and(sc_time!=0):
            print uid
            print 'sc_u:'
            print sc_user
            print 'sc_k'
            print sc_ksum
            print 'sc_t'
            print sc_time
            print 'sc'
            print sc
        update_score = 'update weibouser set score = %s where uid = %s'
        cursor.execute(update_score,(sc,uid))
        db.commit()
    #return sc_user
        
#用户评价指标
def score_user(uid,a,b,c):
    sc_fans = score_fans(uid)
    sc_forwarding = score_forwarding(uid)
    sc_comment = score_comment(uid)
    sc_user = a*sc_fans + b*sc_forwarding + c*sc_comment
    return sc_user


#根据粉丝数对用户得分
def score_fans(uid):
    #找出当前表中粉丝数的最大值
    cursor.execute('select max(fans) from weibouser')
    max_fans = cursor.fetchone()
    select_fans = 'select fans from weibouser where uid=%s'
    cursor.execute(select_fans,(uid,))
    fans = cursor.fetchone()
    if fans[0]>=0.001*max_fans[0]:
        sc_fans = fans[0]*1.0/max_fans[0]
    else: 
        sc_fans = 0
    return sc_fans

#根据转发数对用户得分
def score_forwarding(uid):
    #找出当前表中转发数的最大值
    cursor.execute('select max(forwarding_times) from weibopost')
    max_forwarding = cursor.fetchone()
    #取最近十条微博做分析
    select_forwarding_times = 'select forwarding_times from weibopost where uid = %s order by time desc limit 10'
    cursor.execute(select_forwarding_times,(uid,))
    forwarding_times = cursor.fetchall()
    sc_forwarding_each = []
    if len(forwarding_times)!= 0:
        for i in forwarding_times:
            sc_forwarding_each.append(i[0]*1.0/max_forwarding[0])
        sc_forwarding = sum(sc_forwarding_each)/len(sc_forwarding_each)
    else:
        sc_forwarding = 0
    return sc_forwarding
    
#根据评论数对用户得分
def score_comment(uid):
    #找出当前表中评论数的最大值
    cursor.execute('select max(comment_times) from weibopost')
    max_comment = cursor.fetchone()
    #取最近十条微博做分析
    select_comment_times = 'select comment_times from weibopost where uid = %s order by time desc limit 10'
    cursor.execute(select_comment_times,(uid,))
    comment_times = cursor.fetchall()
    sc_comment_each = []
    if len(comment_times)!= 0:
        for i in comment_times:
            sc_comment_each.append(i[0]*1.0/max_comment[0])
        sc_comment = sum(sc_comment_each)/len(sc_comment_each)
    else:
        sc_comment = 0
    return sc_comment
    
#网络结构评价指标
def score_ksum(uid):
    ksum_compute(uid)
    #找出当前表中用户ksum的最大值
    cursor.execute('select max(ksum) from weibouser')
    max_ksum = cursor.fetchone()
    select_ksum = 'select ksum from weibouser where uid=%s'
    cursor.execute(select_ksum,(uid,))
    ksum = cursor.fetchone()
    if ksum[0]>=0.001*max_ksum[0]:
        sc_ksum = ksum[0]*1.0/max_ksum[0]
    else: 
        sc_ksum = 0
    return sc_ksum
    
#ksum 计算和更新
def ksum_compute(uid):
    new_uid = []
    ksum_each = 0
    ksum = 0
    #查询uid用户为from的被转发微博的mid和to_uid
    select_forwarding_post = 'select mid,to_uid from weiboforwarding where from_uid = %s'
    cursor.execute(select_forwarding_post,(uid,))
    to_uid_tuple = cursor.fetchall()
    if len(to_uid_tuple)!=0:
        #遍历to_uid的用户
        for i in to_uid_tuple:
            mid1 = i[0]
            uid1 = i[1]
            #查询该用户最近十条微博
            select_latest_post = 'select mid from weibopost where uid = %s order by time desc limit 10'
            cursor.execute(select_latest_post,(uid1,))
            latest_post = cursor.fetchall()
            #判断该用户的转发微博是否在其发布的最近十条微博内
            if (mid1,) in latest_post:
                #该用户在计算范围内，加入new_uid
                if uid1 not in new_uid:
                    new_uid.append(uid)
            else:
                continue
        if len(new_uid)!=0:
            #遍历new_uid中的用户
            for i in new_uid:
                #查询该用户为from的被转发微博的mid和to_uid
                cursor.execute(select_forwarding_post,(i,))
                to_uid_tuple2 = cursor.fetchall()
                if len(to_uid_tuple2)!=0:
                    #遍历to_uid2中的用户
                    for j in  to_uid_tuple2:
                        mid2 = j[0]
                        uid2 = j[1]
                        #查询该用户最近十条微博
                        cursor.execute(select_latest_post,(uid2,))
                        latest_post2=cursor.fetchall()
                        #判断i的被转发微博是否在j发布的最近十条微博内
                        if (mid2,) in latest_post2 and i != uid2:
                            ksum_each += 1
                        else:
                            continue
                else:
                    ksum_each = 0
                ksum += ksum_each
        else:
            ksum = 0
    else:
        ksum = 0
    update_ksum = 'update weibouser set ksum = %s where uid = %s'
    cursor.execute(update_ksum,(ksum,uid))
    db.commit()

#时间评价指标
def score_time(uid,a,b):
    sc_latest_time = score_latest_time(uid)
    sc_over_time = score_over_time(uid)
    sc_time = a*sc_latest_time + b*sc_over_time
    return sc_time

#最新微博发布时间评分
def score_latest_time(uid):
    select_latest_time = 'select time from weibopost where uid = %s order by time desc limit 1'
    cursor.execute(select_latest_time,(uid,))
    latest_time = cursor.fetchall()
    if len(latest_time)!=0:
        time_now = datetime.now()
        #最新微博发布时间和现在时间的时间差
        diff_latest_time = (time_now - latest_time[0][0]).days*86400+(time_now - latest_time[0][0]).seconds
        if diff_latest_time > 2592000: #30天
            diff_latest_time = 2592000
        sc_latest_time = 1 - diff_latest_time*1.0/2592000
    else:
        sc_latest_time = 0
    return sc_latest_time
        
#微博时间跨度评分
def score_over_time(uid):
    select_ten_time = 'select time from weibopost where uid = %s order by time desc limit 10'
    cursor.execute(select_ten_time,(uid,))
    ten_time = cursor.fetchall()
    if len(ten_time)!=0:
        first_time = ten_time[-1][0]
        last_time = ten_time[0][0]
        diff_ten_time = (last_time - first_time).days*86400+(last_time - first_time).seconds
        if diff_ten_time > 2592000: #30天
            diff_ten_time = 2592000
        sc_over_time = 1 - diff_ten_time*1.0/2592000
    else:
        sc_over_time = 0
    return sc_over_time