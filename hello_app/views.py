# coding:utf-8
import datetime
import time
import json
from django.shortcuts import render
from django.http import HttpResponse
from hello_app.models import SiteMessageModel, SiteConfigModel, CommonHostModel, CommonOriginModel, PingOriginModel, PingHostModel, PingDataModel, HttpHostModel, HttpOriginModel, HttpDataModel


# Create your views here.

def hello(request):
    return HttpResponse(json.dumps({
        'status': True,
        'message': 'Hello world!'
    }), content_type='application/json')


def index(request, pattern):
    if pattern == 'past_day':
        pass
    elif pattern == 'past_week':
        pass
    elif pattern == 'past_month':
        pass
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
        latest_message.items() +
        latest_updated_time.items()
    )
    return render(request, 'home/home.html', render_data)


def api(request):
    latest_updated_time = {
        'last_updated_time': datetime.datetime.now()
    }
    return render(request, 'api/api.html', latest_updated_time)


def messages(request, patterns):
    stamp = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    if patterns:
        stamp = int(time.mktime(time.strptime(patterns, '%Y-%m-%d')))
    messages_group_list = {
        'messages_group_list': SiteMessageModel.get_weekly_messages_list(stamp),
        'page_prev_arg': SiteMessageModel.has_page_prev_than_time(stamp),
        'page_next_arg': SiteMessageModel.has_page_next_than_time(stamp + 604800)
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


def api_json(request):
    obj = {
        'submit_url': str(SiteConfigModel.get_config('api_submit_url')),
        'status_url': str(SiteConfigModel.get_config('api_status_url')),
        'messages_url': str(SiteConfigModel.get_config('api_messages_url')),
        'last_message_url': str(SiteConfigModel.get_config('api_last_message_url')),
        'hosts_url': str(SiteConfigModel.get_config('api_hosts_url')),
        'origins_url': str(SiteConfigModel.get_config('api_origins_url')),
        'types_url': str(SiteConfigModel.get_config('api_types_url'))
    }
    return HttpResponse(json.dumps(obj), content_type="application/json")


def api_status(request):
    return HttpResponse(u"Not ready")


def api_last_message(request):
    latest_message = SiteMessageModel.get_latest_message_model()
    obj = {
        'status': latest_message.get_status_style_class(),
        'body': latest_message.content,
        'created_on': latest_message.get_cst_time(),
    }
    return HttpResponse(json.dumps(obj), content_type="application/json")


def api_messages(request):
    obj = SiteMessageModel.get_recent_messages_list()
    return HttpResponse(json.dumps(obj), content_type="application/json")


def api_hosts(request):
    obj = CommonHostModel.get_all_hosts_arr()
    return HttpResponse(json.dumps(obj), content_type="application/json")


def api_origins(request):
    obj = CommonOriginModel.get_all_origins_arr()
    return HttpResponse(json.dumps(obj), content_type="application/json")


def api_types(request):
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
    return HttpResponse(json.dumps(obj), content_type="application/json")


def api_submit(request):
    obj = {}
    if len(request.POST) != 0:
        json_text = request.POST['request']
        json_obj = json.loads(json_text)
        type = json_obj['type']
        if type == 'ping':
            req_origin = json_obj['origin']
            req_secret = json_obj['secret']
            origin_obj = PingOriginModel.objects.get(origin=req_origin, enabled=True)
            if origin_obj.secret == req_secret:
                req_data = json_obj['data']
                for data_obj in req_data:
                    host_name = data_obj['host']
                    host_obj = PingHostModel.objects.get(host=host_name, enabled=True)
                    if host_obj:
                        new_data = PingDataModel()
                        new_data.host = host_obj
                        new_data.origin = origin_obj
                        new_data.received_times = data_obj['received_times']
                        new_data.transmitted_times = data_obj['transmitted_times']
                        new_data.delay_avg = data_obj['delay_avg']
                        new_data.delay_max = data_obj['delay_max']
                        new_data.delay_min = data_obj['delay_min']
                        new_data.delay_std = data_obj['delay_std']
                        new_data.timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(data_obj['timestamp'])))
                        new_data.save()
                        origin_obj.sent_count += 1
                        origin_obj.save()
                        host_obj.checked_count += 1
                        host_obj.save()
                        obj = {
                            "status": 'ok'
                        }
                    else:
                        obj = {
                            "status": 'error',
                            "message": 'Unknown Host.'
                        }
                        break
            else:
                obj = {
                    "status": 'error',
                    "message": 'Permission Denied.'
                }
        elif type == 'http':
            req_origin = json_obj['origin']
            req_secret = json_obj['secret']
            origin_obj = HttpOriginModel.objects.get(origin=req_origin, enabled=True)
            if origin_obj.secret == req_secret:
                req_data = json_obj['data']
                for data_obj in req_data:
                    host_name = data_obj['host']
                    host_obj = HttpHostModel.objects.get(host=host_name, enabled=True)
                    if host_obj:
                        new_data = HttpDataModel()
                        new_data.host = host_obj
                        new_data.origin = origin_obj
                        new_data.succeed = data_obj['succeed']
                        new_data.code = data_obj['code']
                        new_data.timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(data_obj['timestamp'])))
                        new_data.delay_std = data_obj['delay_std']
                        new_data.header = json.dumps(data_obj['header'])
                        new_data.save()
                        origin_obj.sent_count += 1
                        origin_obj.save()
                        host_obj.checked_count += 1
                        host_obj.save()
                        obj = {
                            "status": 'ok'
                        }
                    else:
                        obj = {
                            "status": 'error',
                            "message": 'Unknown Host.'
                        }
                        break
            else:
                obj = {
                    "status": 'error',
                    "message": 'Permission Denied.'
                }
        elif type == 'resp':
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
    return HttpResponse(json.dumps(obj), content_type="application/json")