# coding:utf-8
import datetime
import time
import json
import random
import urlparse
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseServerError, HttpResponseBadRequest
from hello_app.models import *
from django.views.decorators.cache import cache_page

# Create your views here.


def hello(request):
    return HttpResponse(json.dumps({
        'status': True,
        'message': 'Hello world!'
    }), content_type='application/json')


@cache_page(900)
def index(request, pattern):
    selected_today = ''
    selected_last_week = ''
    selected_last_month = ''
    if pattern == 'past_week':
        range_type = 1
        selected_last_week = 'selected'
    elif pattern == 'past_month':
        range_type = 2
        selected_last_month = 'selected'
    else:
        range_type = 0
        selected_today = 'selected'
    latest_message = SiteMessageModel.get_latest_message()
    if not latest_message:
        latest_message = {
            'latest_message_content': '暂时没有新消息',
            'latest_message_status': 'default',
        }
    latest_updated_time = {
        'last_updated_time': datetime.datetime.now()
    }
    graph_items = {
        'graph_items': SiteReportModel.generate_all_hosts_graph_data(range_type),
        'range_selected_today': selected_today,
        'range_selected_last_week': selected_last_week,
        'range_selected_last_month': selected_last_month
    }
    render_data = dict(
        latest_message.items() +
        latest_updated_time.items() +
        graph_items.items()
    )
    if '_pjax' in request.GET:
        return render(request, 'home/graph_data.html', render_data)
    return render(request, 'home/home.html', render_data)


@cache_page(3600)
def api(request):
    latest_updated_time = {
        'last_updated_time': datetime.datetime.now()
    }
    return render(request, 'api/api.html', latest_updated_time)


def messages(request, patterns):
    stamp = int(time.mktime(datetime.date.today().timetuple()))
    if patterns:
        stamp = int(time.mktime(time.strptime(patterns, '%Y-%m-%d')))
    messages_group_list = {
        'messages_group_list': SiteMessageModel.get_weekly_messages_list(stamp),
        'page_prev_arg': SiteMessageModel.has_page_prev_than_time(stamp - 518400),
        'page_next_arg': SiteMessageModel.has_page_next_than_time(stamp)
    }
    latest_message = SiteMessageModel.get_latest_message()
    if not latest_message:
        latest_message = {
            'latest_message_content': '暂时没有新消息',
            'latest_message_status': 'default',
        }
    latest_updated_time = {
        'last_updated_time': datetime.datetime.now()
    }
    render_data = dict(
        latest_updated_time.items() +
        messages_group_list.items() +
        latest_message.items()
    )
    return render(request, 'messages/messages.html', render_data)


@cache_page(3600)
def api_json(request):
    api_url = str(SiteConfigModel.get_config('api_url'))
    api_uri = urlparse.urlparse(api_url)
    request_uri = request.get_host()
    if api_uri.netloc != request_uri:
        return HttpResponseBadRequest(json.dumps({
            'status': 'error',
            'message': 'Invalid URI: ' + request_uri
        }), content_type='application/json')
    obj = {
        'submit_url': api_url + 'api/submit.json',
        'status_url': api_url + 'api/status.json',
        'messages_url': api_url + 'api/messages.json',
        'last_message_url': api_url + 'api/last-message.json',
        'hosts_url': api_url + 'api/hosts.json',
        'origins_url': api_url + 'api/origins.json',
        'types_url': api_url + 'api/types.json',
    }
    response = HttpResponse(json.dumps(obj), content_type="application/json")
    response['Access-Control-Allow-Origin'] = SiteConfigModel.get_config('Access-Control-Allow-Origin')
    return response


@cache_page(900)
def api_status(request):
    api_url = str(SiteConfigModel.get_config('api_url'))
    api_uri = urlparse.urlparse(api_url)
    request_uri = request.get_host()
    if api_uri.netloc != request_uri:
        return HttpResponseBadRequest(json.dumps({
            'status': 'error',
            'message': 'Invalid URI: ' + request_uri
        }), content_type='application/json')
    if int(SiteConfigModel.get_config('api_all_shutdown')) == 0:
        return HttpResponseServerError(json.dumps({
            "status": "shutdown",
            "message": "All servers should shutdown."
        }), content_type="application/json")
    return HttpResponse(u"Not ready")


@cache_page(900)
def api_last_message(request):
    api_url = str(SiteConfigModel.get_config('api_url'))
    api_uri = urlparse.urlparse(api_url)
    request_uri = request.get_host()
    if api_uri.netloc != request_uri:
        return HttpResponseBadRequest(json.dumps({
            'status': 'error',
            'message': 'Invalid URI: ' + request_uri
        }), content_type='application/json')
    if int(SiteConfigModel.get_config('api_all_shutdown')) == 0:
        return HttpResponseServerError(json.dumps({
            "status": "shutdown",
            "message": "All servers should shutdown."
        }), content_type="application/json")
    latest_message = SiteMessageModel.get_latest_message_model()
    obj = {
        'status': latest_message.get_status_style_class(),
        'body': latest_message.content,
        'created_on': latest_message.get_cst_time(),
    }
    response = HttpResponse(json.dumps(obj), content_type="application/json")
    response['Access-Control-Allow-Origin'] = SiteConfigModel.get_config('Access-Control-Allow-Origin')
    return response


@cache_page(900)
def api_messages(request):
    api_url = str(SiteConfigModel.get_config('api_url'))
    api_uri = urlparse.urlparse(api_url)
    request_uri = request.get_host()
    if api_uri.netloc != request_uri:
        return HttpResponseBadRequest(json.dumps({
            'status': 'error',
            'message': 'Invalid URI: ' + request_uri
        }), content_type='application/json')
    if int(SiteConfigModel.get_config('api_all_shutdown')) == 0:
        return HttpResponseServerError(json.dumps({
            "status": "shutdown",
            "message": "All servers should shutdown."
        }), content_type="application/json")
    obj = SiteMessageModel.get_recent_messages_list()
    response = HttpResponse(json.dumps(obj), content_type="application/json")
    response['Access-Control-Allow-Origin'] = SiteConfigModel.get_config('Access-Control-Allow-Origin')
    return response


@cache_page(900)
def api_hosts(request):
    api_url = str(SiteConfigModel.get_config('api_url'))
    api_uri = urlparse.urlparse(api_url)
    request_uri = request.get_host()
    if api_uri.netloc != request_uri:
        return HttpResponseBadRequest(json.dumps({
            'status': 'error',
            'message': 'Invalid URI: ' + request_uri
        }), content_type='application/json')
    if int(SiteConfigModel.get_config('api_all_shutdown')) == 0:
        return HttpResponseServerError(json.dumps({
            "status": "shutdown",
            "message": "All servers should shutdown."
        }), content_type="application/json")
    obj = CommonHostModel.get_all_hosts_arr()
    response = HttpResponse(json.dumps(obj), content_type="application/json")
    response['Access-Control-Allow-Origin'] = SiteConfigModel.get_config('Access-Control-Allow-Origin')
    return response


@cache_page(900)
def api_origins(request):
    api_url = str(SiteConfigModel.get_config('api_url'))
    api_uri = urlparse.urlparse(api_url)
    request_uri = request.get_host()
    if api_uri.netloc != request_uri:
        return HttpResponseBadRequest(json.dumps({
            'status': 'error',
            'message': 'Invalid URI: ' + request_uri
        }), content_type='application/json')
    if int(SiteConfigModel.get_config('api_all_shutdown')) == 0:
        return HttpResponseServerError(json.dumps({
            "status": "shutdown",
            "message": "All servers should shutdown."
        }), content_type="application/json")
    obj = CommonOriginModel.get_all_origins_arr()
    response = HttpResponse(json.dumps(obj), content_type="application/json")
    response['Access-Control-Allow-Origin'] = SiteConfigModel.get_config('Access-Control-Allow-Origin')
    return response


@cache_page(900)
def api_types(request):
    api_url = str(SiteConfigModel.get_config('api_url'))
    api_uri = urlparse.urlparse(api_url)
    request_uri = request.get_host()
    if api_uri.netloc != request_uri:
        return HttpResponseBadRequest(json.dumps({
            'status': 'error',
            'message': 'Invalid URI: ' + request_uri
        }), content_type='application/json')
    if int(SiteConfigModel.get_config('api_all_shutdown')) == 0:
        return HttpResponseServerError(json.dumps({
            "status": "shutdown",
            "message": "All servers should shutdown."
        }), content_type="application/json")
    obj = [
        {
            "type": "ping",
            "subtypes": [
                "ping-success-rate",
                "ping-delay-avg"
            ]
        },
        {
            "type": "http",
            "subtypes": [
                "http-success-rate",
                "http-delay-avg"
            ]
        },
        {
            "type": "resp",
            "subtypes": [
                "resp-match-rate",
                "resp-delay-avg"
            ]
        },
        {
            "type": "active",
            "subtypes": [
                "exception-rate"
            ]
        }
    ]
    response = HttpResponse(json.dumps(obj), content_type="application/json")
    response['Access-Control-Allow-Origin'] = SiteConfigModel.get_config('Access-Control-Allow-Origin')
    return response


def api_submit(request):
    api_url = str(SiteConfigModel.get_config('api_url'))
    api_uri = urlparse.urlparse(api_url)
    request_uri = request.get_host()
    if api_uri.netloc != request_uri:
        return HttpResponseBadRequest(json.dumps({
            'status': 'error',
            'message': 'Invalid URI: ' + request_uri
        }), content_type='application/json')
    if int(SiteConfigModel.get_config('api_all_shutdown')) == 0:
        return HttpResponse(json.dumps({
            "status": "shutdown",
            "message": "All servers should shutdown."
        }), content_type="application/json")
    SiteReportModel.generate_new_daily_message()
    obj = {}
    if len(request.POST) != 0:
        json_text = request.POST['request']
        json_obj = json.loads(json_text)
        req_type = json_obj['type']
        if req_type == 'ping':
            req_origin = json_obj['origin']
            req_secret = json_obj['secret']
            origin_obj = PingOriginModel.objects.get(origin=req_origin, enabled=True)
            if origin_obj:
                if origin_obj.secret == req_secret:
                    # Random dismiss packet
                    random_int = random.randint(1, 100)
                    if random_int <= int(origin_obj.power):
                        host_name = json_obj['host']
                        host_obj = PingHostModel.objects.get(host=host_name, enabled=True)
                        if host_obj:
                            req_data = json_obj['data']
                            for data_obj in req_data:
                                origin_time = time.mktime(origin_obj.edited_at.timetuple())
                                host_time = time.mktime(host_obj.edited_at.timetuple())
                                if origin_time <= json_obj['start'] and host_time <= json_obj['start']:
                                    new_data = PingDataModel()
                                    new_data.host = host_obj
                                    new_data.origin = origin_obj
                                    new_data.received_times = data_obj['received_times']
                                    new_data.transmitted_times = data_obj['transmitted_times']
                                    new_data.delay_avg = data_obj['delay_avg']
                                    new_data.delay_max = data_obj['delay_max']
                                    new_data.delay_min = data_obj['delay_min']
                                    new_data.delay_std = data_obj['delay_std']
                                    new_data.timestamp = time.strftime('%Y-%m-%d %H:%M:%S',
                                                                       time.localtime(int(data_obj['timestamp'])))
                                    new_data.save()
                                    obj = {
                                        "status": 'ok'
                                    }
                                    SiteReportModel.generate_new_ping_report(host_obj, int(json_obj['start']))
                                else:
                                    obj = {
                                        "status": 'restart',
                                        "message": 'Restart Program.'
                                    }
                                    break
                        else:
                            obj = {
                                "status": 'error',
                                "message": 'Unknown Host.'
                        }
                    else:
                        obj = {
                            "status": 'ok',
                            "message": 'Dismissed.'
                        }
                else:
                    obj = {
                        "status": 'error',
                        "message": 'Permission Denied.'
                    }
            else:
                obj = {
                    "status": 'error',
                    "message": 'Unknown Origin.'
                }
        elif req_type == 'http':
            req_origin = json_obj['origin']
            req_secret = json_obj['secret']
            origin_obj = HttpOriginModel.objects.get(origin=req_origin, enabled=True)
            if origin_obj:
                if origin_obj.secret == req_secret:
                    # Random dismiss packet
                    random_int = random.randint(1, 100)
                    if random_int <= int(origin_obj.power):
                        host_name = json_obj['host']
                        host_obj = HttpHostModel.objects.get(host=host_name, enabled=True)
                        if host_obj:
                            req_data = json_obj['data']
                            for data_obj in req_data:
                                origin_time = time.mktime(origin_obj.modified_at.timetuple())
                                host_time = time.mktime(host_obj.modified_at.timetuple())
                                if origin_time <= json_obj['start'] and host_time <= json_obj['start']:
                                    new_data = HttpDataModel()
                                    new_data.host = host_obj
                                    new_data.origin = origin_obj
                                    new_data.succeed = data_obj['succeed']
                                    new_data.code = data_obj['code']
                                    new_data.timestamp = time.strftime('%Y-%m-%d %H:%M:%S',
                                                                       time.localtime(int(data_obj['timestamp'])))
                                    new_data.delay_std = data_obj['delay_std']
                                    new_data.header = json.dumps(data_obj['header'])
                                    new_data.save()
                                    obj = {
                                        "status": 'ok'
                                    }
                                    SiteReportModel.generate_new_http_report(host_obj, int(json_obj['start']))
                                else:
                                    obj = {
                                        "status": 'restart',
                                        "message": 'Restart Program.'
                                    }
                                    break
                        else:
                            obj = {
                                "status": 'error',
                                "message": 'Unknown Host.'
                            }
                    else:
                        obj = {
                            "status": 'ok',
                            "message": 'Dismissed.'
                        }
                else:
                    obj = {
                        "status": 'error',
                        "message": 'Permission Denied.'
                    }
            else:
                obj = {
                    "status": 'error',
                    "message": 'Unknown Origin.'
                }
        elif req_type == 'resp':
            pass
        else:
            obj = {
                "status": 'error',
                "message": 'Invalid Data Type.'
            }
    else:
        obj = {
            "status": 'error',
            "message": 'POST Request Only.'
        }
    response = HttpResponse(json.dumps(obj), content_type="application/json")
    response['Access-Control-Allow-Origin'] = SiteConfigModel.get_config('Access-Control-Allow-Origin')
    return response
