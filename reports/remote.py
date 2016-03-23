#!/usr/bin/python
# -*- coding:utf-8 -*- 

import os
import re
import sys
import json
import time
import datetime
import random
import string
import urllib2
import requests
import threading
import subprocess

g_debug = False
g_count = 5
g_origin = '127.0.0.1-ping-http'
g_secret = 'pappi-blockade-suspend'
g_session = requests.session()
g_url_json = 'https://status.touchsprite.com/api.json'
g_ua = 'StatusHub/1.0'


def restart_program():
    python = sys.executable
    os.execl(python, python, * sys.argv)


def ping_loop(host, freq, flag, s_url):
    global g_debug, g_count, g_origin, g_secret, g_session
    thread_time = time.time()
    # delay for a random seed time
    seed = random.randint(0, freq)
    if not g_debug:
        time.sleep(seed)
    print '(Ping) Thread ' + str(flag) + ' | ' + 'Seed = ' + str(seed) + ' | ' + 'Frequency = ' + str(freq)
    # init variables
    count = 4
    lifeline = re.compile(r"(\d) packets received")
    delay_line = re.compile(r"= (.+) ms")
    reports = []
    loop_times = 0
    # main loop
    while 1:
        print 'Thread ' + str(flag) + ' | ' + 'Ping ' + str(host) + ' | ' + 'Loop = ' + str(loop_times)
        # ping subprocess
        ping_ling = subprocess.Popen(
            ["ping", "-q", "-c " + str(count), host],
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        # ping variables
        received = 0
        delay = None
        delay_min = None
        delay_avg = None
        delay_max = None
        delay_std = None
        # get pipe outputs
        while 1:
            ping_ling.stdout.flush()
            line = ping_ling.stdout.readline()
            if not line:
                break
            rev = re.findall(lifeline, line)
            # get result via regexp
            if len(rev) == 1:
                received = int(rev[0])
            de = re.findall(delay_line, line)
            if len(de) == 1:
                delay = de[0]
        if delay is not None:
            delay_arr = string.split(delay, '/')
            if len(delay_arr) == 4:
                delay_min = float(delay_arr[0])
                delay_avg = float(delay_arr[1])
                delay_max = float(delay_arr[2])
                delay_std = float(delay_arr[3])
        # build result dict
        result = {
            'transmitted_times': count,
            'received_times': received,
            'delay_min': delay_min,
            'delay_avg': delay_avg,
            'delay_max': delay_max,
            'delay_std': delay_std,
            'timestamp': int(time.time()),
        }
        reports.append(result)
        if len(reports) >= g_count:
            request_data = {
                'type': 'ping',
                'origin': g_origin,
                'host': host,
                'secret': g_secret,
                'data': reports,
                'start': thread_time,
            }
            result = g_session.post(s_url, data={'request': json.dumps(request_data)})
            if g_debug:
                print result.text
            if result.status_code != 200:
                print '(Ping) Thread ' + str(flag) + ' | ' + 'Report Failed!'
            else:
                report_ret = json.loads(result.text)
                if report_ret['status'] == 'ok':
                    print '(Ping) Thread ' + str(flag) + ' | ' + 'Report Succeed: ' + str(result.text)
                    reports = []
                elif report_ret['status'] == 'error':
                    print '(Ping) Thread ' + str(flag) + ' | ' + 'Report Failed: ' + str(result.text)
                elif report_ret['status'] == 'restart':
                    print '(Ping) Thread ' + str(flag) + ' | ' + 'Restarted By Remote: ' + str(result.text)
                    restart_program()
                elif report_ret['status'] == 'shutdown':
                    print '(Ping) Thread ' + str(flag) + ' | ' + 'Terminated By Remote: ' + str(result.text)
                    os._exit(0)
        loop_times += 1
        # wait for next request
        if not g_debug:
            time.sleep(freq + random.randint(1, 5))


# use urllib to get http code, instead of urllib2 or requests, for a better performance?
def http_loop(host_dict, freq, flag, s_url):
    global g_debug, g_count, g_origin, g_secret, g_session
    thread_time = time.time()
    # delay for a random seed time
    seed = random.randint(0, freq)
    if not g_debug:
        time.sleep(seed)
    print '(Http) Thread ' + str(flag) + ' | ' + 'Seed = ' + str(seed) + ' | ' + 'Frequency = ' + str(freq)
    # init variables
    reports = []
    loop_times = 0
    # main loop
    while 1:
        uri = ''
        if host_dict['secure']:
            uri += 'https://'
        else:
            uri += 'http://'
        uri += host_dict['host'] + ':' + str(host_dict['port'])
        print 'Thread ' + str(flag) + ' | ' + 'GET ' + str(uri) + ' | ' + 'Loop = ' + str(loop_times)
        ret_delay = 12000
        ret_header = {}
        micro_start = datetime.datetime.utcnow()
        try:
            req = urllib2.Request(uri)
            req.add_header('User-Agent', host_dict['ua'])
            req = urllib2.urlopen(req, timeout=12)
            ret_code = req.getcode()
            ret_header = str(req.info())
        except Exception:
            ret_code = 0
        if ret_code == 200:
            ret_succeed = True
            micro_end = datetime.datetime.utcnow()
            micro_delay = (micro_end - micro_start)
            ret_delay = micro_delay.microseconds / 1000
        else:
            ret_succeed = False
        # build result dict
        result = {
            'succeed': ret_succeed,
            'code': ret_code,
            'header': ret_header,
            'delay_std': ret_delay,
            'timestamp': int(time.time()),
        }
        reports.append(result)
        if len(reports) >= g_count:
            request_data = {
                'type': 'http',
                'origin': g_origin,
                'host': host_dict['host'],
                'secret': g_secret,
                'data': reports,
                'start': thread_time,
            }
            result = g_session.post(s_url, data={'request': json.dumps(request_data)})
            if result.status_code != 200:
                print '(Http) Thread ' + str(flag) + ' | ' + 'Report Failed!'
            else:
                report_ret = json.loads(result.text)
                if report_ret['status'] == 'ok':
                    print '(Http) Thread ' + str(flag) + ' | ' + 'Report Succeed: ' + str(result.text)
                    reports = []
                elif report_ret['status'] == 'error':
                    print '(Http) Thread ' + str(flag) + ' | ' + 'Report Failed: ' + str(result.text)
                elif report_ret['status'] == 'restart':
                    print '(Http) Thread ' + str(flag) + ' | ' + 'Restarted By Remote: ' + str(result.text)
                    restart_program()
                elif report_ret['status'] == 'shutdown':
                    print '(Http) Thread ' + str(flag) + ' | ' + 'Terminated By Remote: ' + str(result.text)
                    os._exit(0)
        loop_times += 1
        # wait for next request
        if not g_debug:
            time.sleep(freq + random.randint(1, 5))


def resp_loop(host_dict, freq, flag, s_url):
    global g_debug, g_count, g_origin, g_secret, g_session
    thread_time = time.time()
    # delay for a random seed time
    seed = random.randint(0, freq)
    if not g_debug:
        time.sleep(seed)
    print '(Resp) Thread ' + str(flag) + ' | ' + 'Seed = ' + str(seed) + ' | ' + 'Frequency = ' + str(freq)
    # init variables
    reports = []
    loop_times = 0
    # main loop
    while 1:
        uri = host_dict['url']
        method_value = int(host_dict['method'])
        method_str = ''
        if method_value == 0:
            method_str = 'HEAD'
        elif method_value == 1:
            method_str = 'GET'
        elif method_value == 2:
            method_str = 'POST'
        print 'Thread ' + str(flag) + ' | ' + method_str + ' ' + str(uri) + ' | ' + 'Loop = ' + str(loop_times)
        ret_delay = 12000
        ret_header = {}
        micro_start = datetime.datetime.utcnow()


def main():
    global g_url_json, g_ua
    g_ping = {
        'enabled': False,
        'subtypes': [],
        'hosts': []
    }
    g_http = {
        'enabled': False,
        'subtypes': [],
        'hosts': []
    }
    g_resp = {
        'enabled': False,
        'subtypes': [],
        'hosts': []
    }
    g_header = {
        'User-Agent': g_ua
    }
    
    print 'StatusHub v1.0 - Client Sniffer'
    print 'Author: i_82 <i.82@me.com>'
    time.sleep(5)
    # init API URLs
    result = g_session.get(g_url_json)
    if result.status_code != 200:
        result.raise_for_status()
    _obj = json.loads(result.text)
    # get origins config
    result = g_session.get(_obj['origins_url'], headers=g_header, timeout=10)
    if result.status_code != 200:
        result.raise_for_status()
    # parse origins config
    origins = json.loads(result.text)
    for origin in origins:
        if origin['host'] == g_origin:
            if origin['type'] == 'ping':
                g_ping['enabled'] = True
            if origin['type'] == 'http':
                g_ua = origin['ua']
                g_http['enabled'] = True
            if origin['type'] == 'resp':
                g_resp['enabled'] = True
    # get types config
    result = g_session.get(_obj['types_url'], headers=g_header, timeout=10)
    if result.status_code != 200:
        result.raise_for_status()
    subtypes = json.loads(result.text)
    # parse types config
    for subtype in subtypes:
        if g_ping['enabled'] == True and subtype['type'] == 'ping':
            g_ping['subtypes'] = subtype['subtypes']
        if g_http['enabled'] == True and subtype['type'] == 'http':
            g_http['subtypes'] = subtype['subtypes']
        if g_resp['enabled'] == True and subtype['type'] == 'resp':
            g_resp['subtypes'] = subtype['subtypes']
    # get hosts config
    result = g_session.get(_obj['hosts_url'], headers=g_header, timeout=10)
    if result.status_code != 200:
        result.raise_for_status()
    hosts = json.loads(result.text)
    # parse hosts config
    for host in hosts:
        if g_ping['enabled'] == True and host['type'] == 'ping':
            g_ping['hosts'].append(host)
        if g_http['enabled'] == True and host['type'] == 'http':
            g_http['hosts'].append({
                'host': host['host'],
                'port': host['port'],
                'secure': host['secure'],
                'ua': g_ua,
                'frequency': host['frequency']
            })
        if g_resp['enabled'] == True and host['type'] == 'resp':
            g_resp['hosts'].append(host)
    # print enabled functions & append threads
    threads = []
    thread_count = 0
    if g_ping['enabled']:
        for host_dict in g_ping['hosts']:
            thread_count += 1
            threads.append(threading.Thread(target=ping_loop, args=(
                host_dict['host'], int(host_dict['frequency']), thread_count, _obj['submit_url']
            )))
    if g_http['enabled']:
        for host_dict in g_http['hosts']:
            thread_count += 1
            threads.append(threading.Thread(target=http_loop, args=(
                host_dict, int(host_dict['frequency']), thread_count, _obj['submit_url']
            )))
    if g_resp['enabled']:
        for host_dict in g_resp['hosts']:
            thread_count += 1
            threads.append(threading.Thread(target=resp_loop, args=(
                host_dict, int(host_dict['frequency']), thread_count, _obj['submit_url']
            )))
    # start daemon threads
    for t in threads:
        t.setDaemon(True)
        t.start()
    # keep main thread
    while 1:
        raw_input()
    return 0
        

if __name__ == '__main__':
    main()
