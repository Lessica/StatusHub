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
global _origin, _secret, _url_json, _ping, _http, _resp, _header, _s, _obj, _debug, _count

_debug = False
_count = 1
_origin = '127.0.0.1-ping-http-resp'
_secret = 'binnacle-sluice-calling'
_url_json = 'https://status.touchsprite.com/api.json'

_ping = {
    'enabled': False,
    'subtypes': [],
    'hosts': []
}
_http = {
    'enabled': False,
    'subtypes': [],
    'hosts': []
}
_resp = {
    'enabled': False,
    'subtypes': [],
    'hosts': []
}
_header = {
    'User-Agent': 'StatusHub/1.0'
}
_obj = {}
_s = requests.session()


def restart_program():
    python = sys.executable
    os.execl(python, python, * sys.argv)


def ping_loop(host, freq, flag, s_url):
    thread_time = time.time()
    # delay for a random seed time
    seed = random.randint(0, freq)
    if (_debug == False):
        time.sleep(seed)
    print 'Thread ' + str(flag) + ' | ' + 'Seed = ' + str(seed) + ' | ' + 'Frequency = ' + str(freq)
    # init variables
    count = 4
    lifeline = re.compile(r"(\d) packets received")
    delayline = re.compile(r"= (.+) ms")
    reports = []
    loop_times = 0
    # main loop
    while 1:
        print 'Thread ' + str(flag) + ' | ' + 'Ping ' + str(host) + ' | ' + 'Loop = ' + str(loop_times)
        # ping subprocess
        pingaling = subprocess.Popen(["ping", "-q", "-c " + str(count), '-t 12', host], shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        # ping variables
        received = 0
        delay = None
        delay_min = None
        delay_avg = None
        delay_max = None
        delay_std = None
        # get pipe outputs
        while 1:
            pingaling.stdout.flush()
            line = pingaling.stdout.readline()
            if not line: break
            recv = re.findall(lifeline, line)
            # get result via regexp
            if len(recv) == 1:
                received = int(recv[0])
            de = re.findall(delayline, line)
            if len(de) == 1:
                delay = de[0]
        if delay != None:
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
        if len(reports) >= _count:
            request_data = {
                'type': 'ping',
                'origin': _origin,
                'host': host,
                'secret': _secret,
                'data': reports,
                'start': thread_time,
            }
            _r = _s.post(s_url, data={'request': json.dumps(request_data)})
            if _r.status_code != 200:
                print 'Thread ' + str(flag) + ' | ' + 'Report Failed!'
            else:
                report_ret = json.loads(_r.text)
                if report_ret['status'] == 'ok':
                    print 'Thread ' + str(flag) + ' | ' + 'Report Succeed: ' + str(_r.text)
                    reports = []
                elif report_ret['status'] == 'error':
                    print 'Thread ' + str(flag) + ' | ' + 'Report Failed: ' + str(_r.text)
                elif report_ret['status'] == 'restart':
                    print 'Thread ' + str(flag) + ' | ' + 'Restarted By Remote: ' + str(_r.text)
                    restart_program()
                elif report_ret['status'] == 'shutdown':
                    print 'Thread ' + str(flag) + ' | ' + 'Terminated By Remote: ' + str(_r.text)
                    os._exit(0)
        loop_times = loop_times + 1
        # wait for next request
        if (_debug == False):
            time.sleep(freq + random.randint(1, 5))


# use urllib to get http code, instead of urllib2 or requests, for a better performance?
def http_loop(host_dict, freq, flag, s_url):
    thread_time = time.time()
    # delay for a random seed time
    seed = random.randint(0, freq)
    if (_debug == False):
        time.sleep(seed)
    print 'Thread ' + str(flag) + ' | ' + 'Seed = ' + str(seed) + ' | ' + 'Frequency = ' + str(freq)
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
        print 'Thread ' + str(flag) + ' | ' + 'Try: ' + str(uri) + ' | ' + 'Loop = ' + str(loop_times)
        ret_code = 0
        ret_delay = 12000
        ret_header = {}
        micro_start = datetime.datetime.utcnow()
        try:
            requ = urllib2.Request(uri)
            requ.add_header('User-Agent', host_dict['ua'])
            req = urllib2.urlopen(requ, timeout=12)
            ret_code = req.getcode()
            ret_header = str(req.info())
        except Exception, e:
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
        if len(reports) >= _count:
            request_data = {
                'type': 'http',
                'origin': _origin,
                'host': host_dict['host'],
                'secret': _secret,
                'data': reports,
                'start': thread_time,
            }
            _r = _s.post(s_url, data={'request': json.dumps(request_data)})
            if _r.status_code != 200:
                print 'Thread ' + str(flag) + ' | ' + 'Report Failed!'
            else:
                report_ret = json.loads(_r.text)
                if report_ret['status'] == 'ok':
                    print 'Thread ' + str(flag) + ' | ' + 'Report Succeed: ' + str(_r.text)
                    reports = []
                elif report_ret['status'] == 'error':
                    print 'Thread ' + str(flag) + ' | ' + 'Report Failed: ' + str(_r.text)
                elif report_ret['status'] == 'restart':
                    print 'Thread ' + str(flag) + ' | ' + 'Restarted By Remote: ' + str(_r.text)
                    restart_program()
                elif report_ret['status'] == 'shutdown':
                    print 'Thread ' + str(flag) + ' | ' + 'Terminated By Remote: ' + str(_r.text)
                    os._exit(0)
        loop_times = loop_times + 1
        # wait for next request
        if (_debug == False):
            time.sleep(freq + random.randint(1, 5))


def resp_loop(url, freq, flag, s_url):
    pass


def main():
    print 'StatusHub v1.0 - Client Sniffer'
    print 'Author: i_82 <i.82@me.com>'
    time.sleep(5)
    # init API URLs
    _r = _s.get(_url_json)
    if _r.status_code != 200:
        _r.raise_for_status()
    _obj = json.loads(_r.text)
    # get origins config
    _r = _s.get(_obj['origins_url'], headers=_header, timeout=10)
    if _r.status_code != 200:
        _r.raise_for_status()
    # parse origins config
    origins = json.loads(_r.text)
    for origin in origins:
        if origin['host'] == _origin:
            if origin['type'] == 'ping':
                _ping['enabled'] = True
            if origin['type'] == 'http':
                _http['enabled'] = True
            if origin['type'] == 'resp':
                _resp['enabled'] = True
    # get types config
    _r = _s.get(_obj['types_url'], headers=_header, timeout=10)
    if _r.status_code != 200:
        _r.raise_for_status()
    subtypes = json.loads(_r.text)
    # parse types config
    for subtype in subtypes:
        if _ping['enabled'] == True and subtype['type'] == 'ping':
            _ping['subtypes'] = subtype['subtypes']
        if _http['enabled'] == True and subtype['type'] == 'http':
            _http['subtypes'] = subtype['subtypes']
        if _resp['enabled'] == True and subtype['type'] == 'resp':
            _resp['subtypes'] = subtype['subtypes']
    # get hosts config
    _r = _s.get(_obj['hosts_url'], headers=_header, timeout=10)
    if _r.status_code != 200:
        _r.raise_for_status()
    hosts = json.loads(_r.text)
    # parse hosts config
    for host in hosts:
        if _ping['enabled'] == True and host['type'] == 'ping':
            _ping['hosts'].append({
                'host': host['host'],
                'frequency': host['frequency']
            })
        if _http['enabled'] == True and host['type'] == 'http':
            _http['hosts'].append({
                'host': host['host'],
                'port': host['port'],
                'secure': host['secure'],
                'ua': origin['ua'],
                'frequency': host['frequency']
            })
        if _resp['enabled'] == True and host['type'] == 'resp':
            _resp['hosts'].append({
                'host': host['host'],
                'frequency': host['frequency']
            })
    # print enabled functions & append threads
    threads = []
    thread_count = 0
    if _ping['enabled'] == True:
        for host_dict in _ping['hosts']:
            thread_count = thread_count + 1
            threads.append(threading.Thread(target=ping_loop, args=(host_dict['host'], int(host_dict['frequency']), thread_count, _obj['submit_url'])))
    if _http['enabled'] == True:
        for host_dict in _http['hosts']:
            thread_count = thread_count + 1
            threads.append(threading.Thread(target=http_loop, args=(host_dict, int(host_dict['frequency']), thread_count, _obj['submit_url'])))
    if _resp['enabled'] == True:
        for host_dict in _resp['hosts']:
            thread_count = thread_count + 1
            threads.append(threading.Thread(target=resp_loop, args=(host_dict['host'], int(host_dict['frequency']), thread_count, _obj['submit_url'])))
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
