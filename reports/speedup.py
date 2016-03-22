#!/usr/bin/python

import requests
import platform
if platform.system() != 'Windows':
    from termcolor import colored
else:
    def colored(string, color):
        return string
import json
    
print colored('Jiangsu Telecom Service Speed Up Script 1.0', 'yellow')
print colored('Author: i_82 <i.82@me.com>', 'yellow')
print colored('> Get PHPSESSID...', 'blue')
s = requests.session()
headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36',
    'Origin': 'http://114yeah.com',
    'Referer': 'http://114yeah.com/',
    'X-Requested-With': 'XMLHttpRequest',
}
r = s.get("http://www.114yeah.com/", headers=headers)
if r.status_code != 200:
    r.raise_for_status()
print colored('> PHPSESSID: ' + s.cookies['PHPSESSID'], 'green')
print colored('> Get Encrypted Token...', 'blue')
r = s.post('http://www.114yeah.com/Index/encrypchar.html', data={}, headers=headers)
if r.status_code != 200:
    r.raise_for_status()
j = json.loads(r.text)
token = j
print colored('> Token: ' + j, 'green')
print colored('> Signing...', 'blue')
r = s.get('http://61.160.183.220/jsts/ebit/sign', params={
    'k': j
}, headers=headers)
if r.status_code != 200:
    r.raise_for_status()
j = json.loads(r.text)
print colored('> Sign: ' + json.dumps(j), 'green')
print colored('> Recording...', 'blue')
r = s.post('http://www.114yeah.com/Index/record.html', data={
    'interuser': j['un']
})
if r.status_code != 200:
    r.raise_for_status()
print colored('> Record Result: ' + r.text, 'green')
headers['Referer'] = 'http://www.114yeah.com/Index/speedup.html'
# print colored('> Get Encrypted Token For Starting...', 'blue')
# r = s.post('http://114yeah.com/Index/encrypchar.html', data={}, headers=headers)
# if (r.status_code != 200):
#     r.raise_for_status()
# j = json.loads(r.text)
# token = j
# print colored('> Starting Token: ' + j, 'green')
print colored('> Speeding Up...', 'blue')
r = s.get('http://61.160.183.220/jsts/ebit/start', params={
    'k': token
}, headers=headers)
if r.status_code != 200:
    r.raise_for_status()
j = json.loads(r.text)
print colored('> Result: ' + json.dumps(j), 'green')
if j['code'] == '-21523':
    print colored('> Already speeded up.', 'red')
print colored('# Account: ' + j['un'], 'yellow')
print colored('# Base bandwidth: ' + str(j['base']) + ' kb/s', 'yellow')
print colored('# Up bandwidth: ' + str(j['up']) + ' kb/s', 'yellow')
raw_input()
