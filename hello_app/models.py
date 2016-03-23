# coding:utf-8
from __future__ import unicode_literals
import datetime
import time
import json
from django.db import models

# Create your models here.


class SiteConfigCategoryModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name


class SiteConfigModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    key = models.CharField(max_length=64, unique=True)
    value = models.CharField(max_length=256)
    category = models.ForeignKey(SiteConfigCategoryModel)
    comments = models.TextField(blank=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.key

    @staticmethod
    def set_config(config_name, config_value):
        obj = SiteConfigModel.objects.filter(key=str(config_name)).update(value=str(config_value))
        if not obj:
            return False
        return True

    @staticmethod
    def get_config(config_name):
        obj = SiteConfigModel.objects.filter(key=str(config_name))
        if not obj:
            return None
        model = obj[0]
        return model.value

    @staticmethod
    def add_config(config_name, config_value):
        SiteConfigModel.objects.filter(key=str(config_name)).update_or_create(key=str(config_name), value=config_value)


class CommonMessageModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    type = models.IntegerField(default=0, choices=(
        (0, 'Custom'),
        (1, 'Brief Message'),
        (2, 'Detailed Message'),
        (3, 'Auto Message'),
    ))
    status = models.IntegerField(default=0, choices=(
        (0, 'Custom'),
        (1, 'Success'),
        (2, 'Warning'),
        (3, 'Notice'),
        (4, 'Error'),
    ))
    content = models.TextField(default='')
    power = models.IntegerField(default=0)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class SiteMessageModel(CommonMessageModel):
    @staticmethod
    def get_latest_message_model():
        obj = SiteMessageModel.objects.filter(
            type__in=[1, 3],
            enabled=True
        ).order_by('-id')[:1]
        if not obj:
            return None
        return obj[0]

    @staticmethod
    def get_latest_message():
        model = SiteMessageModel.get_latest_message_model()
        if not model:
            return None
        arr = {
            'latest_message_content': model.content,
            'latest_message_status': model.get_status_style_class(),
        }
        return arr

    @staticmethod
    def get_recent_messages_list():
        req_time = int(time.mktime(datetime.datetime.utcnow().timetuple()))
        req_start = datetime.datetime.fromtimestamp(
            req_time - int(SiteConfigModel.get_config('default_site_recent_duration'))
        )
        req_end = datetime.datetime.fromtimestamp(req_time)
        recent_messages_list = SiteMessageModel.objects.filter(
            enabled=True,
            created_at__range=(req_start, req_end)
        ).extra(select={
            'body': "`content`"
        }).values('status', 'body', 'created_at').order_by('-id')
        if not recent_messages_list:
            return []
        new_recent_messages = []
        for recent_message in recent_messages_list:
            new_recent_message = {
                'status': SiteMessageModel.get_status_style_class_by_value(recent_message['status']),
                'body': recent_message['body'],
                'created_at': SiteMessageModel.get_cst_time_by_value(recent_message['created_at'])
            }
            new_recent_messages.append(new_recent_message)
        return new_recent_messages

    @staticmethod
    def has_page_prev_than_time(req_time):
        req_pos = datetime.datetime.fromtimestamp(req_time)
        obj = SiteMessageModel.objects.filter(created_at__lte=req_pos)[:1]
        if not obj:
            return None
        else:
            return (req_pos + datetime.timedelta(-1)).strftime('%Y-%m-%d')

    @staticmethod
    def has_page_next_than_time(req_time):
        req_pos = datetime.datetime.fromtimestamp(req_time + 86400)
        obj = SiteMessageModel.objects.filter(created_at__gte=req_pos)[:1]
        if not obj:
            return None
        else:
            return (req_pos + datetime.timedelta(7)).strftime('%Y-%m-%d')

    @staticmethod
    def get_weekly_messages_list(req_time):
        req_start = datetime.datetime.fromtimestamp(req_time + 86400)
        req_end = datetime.datetime.fromtimestamp(req_time - 518400)
        weekly_messages_list = SiteMessageModel.objects.filter(
            enabled=True,
            created_at__range=(req_end, req_start)
        ).extra(select={
            'date': "date(`created_at`)"
        }).values('type', 'status', 'content', 'date', 'created_at').order_by('-id')
        if not weekly_messages_list:
            return None
        new_messages_list = {}
        for weekly_message in weekly_messages_list:
            weekly_message['type'] = ''
            weekly_message['status'] = SiteMessageModel.get_status_style_class_by_value(weekly_message['status'])
            if weekly_message['date']:
                if weekly_message['date'] not in new_messages_list:
                    tmp = datetime.datetime.strptime(weekly_message['date'], "%Y-%m-%d")
                    new_messages_list[weekly_message['date']] = {
                        'date': weekly_message['date'],
                        'display': datetime.datetime.strftime(datetime.date(tmp.year, tmp.month, tmp.day), "%B %d, %Y"),
                        'list': []
                    }
                new_messages_list[weekly_message['date']]['list'].append(weekly_message)
        if not new_messages_list:
            return None
        new_messages_arr = []
        for key in new_messages_list:
            new_messages_arr.append(new_messages_list[key])
        new_messages_arr.sort(reverse=True)
        return new_messages_arr

    @staticmethod
    def get_status_style_class_by_value(v):
        if v == 1:
            return 'good'
        elif v == 2:
            return 'minor'
        elif v == 4:
            return 'major'
        else:
            return 'default'

    @staticmethod
    def get_cst_time_by_value(v):
        return v.strftime('%Y-%m-%dT%H:%M:%SZ')

    def get_status_style_class(self):
        return SiteMessageModel.get_status_style_class_by_value(self.status)

    def get_cst_time(self):
        return SiteMessageModel.get_cst_time_by_value(self.created_at)


class CommonHostModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    host = models.CharField(
        max_length=255,
        unique=True
    )
    name = models.CharField(
        max_length=255,
        unique=True
    )
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    edited_at = models.DateTimeField()
    frequency = models.IntegerField(default=900)
    random_id = models.CharField(max_length=6, default='')
    comments = models.TextField(blank=True)

    @staticmethod
    def get_all_hosts_arr():
        ping_arr = PingHostModel.get_brief_hosts_arr()
        http_arr = HttpHostModel.get_brief_hosts_arr()
        resp_arr = RespHostModel.get_brief_hosts_arr()
        arr = []
        arr.extend(ping_arr)
        arr.extend(http_arr)
        arr.extend(resp_arr)
        return arr


class CommonOriginModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    origin = models.CharField(
        max_length=255,
        unique=True
    )
    name = models.CharField(
        max_length=255,
        unique=True
    )
    power = models.IntegerField()
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    edited_at = models.DateTimeField()
    secret = models.CharField(max_length=32, default='')
    comments = models.TextField(blank=True)

    @staticmethod
    def get_all_origins_arr():
        ping_arr = PingOriginModel.get_brief_origins_arr()
        http_arr = HttpOriginModel.get_brief_origins_arr()
        resp_arr = RespOriginModel.get_brief_origins_arr()
        arr = []
        arr.extend(ping_arr)
        arr.extend(http_arr)
        arr.extend(resp_arr)
        return arr


class PingHostModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    host = models.CharField(
        max_length=255,
        unique=True
    )
    name = models.CharField(
        max_length=255,
        unique=True
    )
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    edited_at = models.DateTimeField()
    random_id = models.CharField(max_length=6, default='')
    frequency = models.IntegerField(default=900)
    comments = models.TextField(blank=True)

    @staticmethod
    def get_brief_hosts_arr():
        ping_hosts = PingHostModel.objects.filter(enabled=True).order_by('-id')
        arr = []
        for ping_host in ping_hosts:
            arr.append({
                'type': 'ping',
                'host': ping_host.host,
                'frequency': ping_host.frequency
            })
        return arr

    def __unicode__(self):
        return self.name


class PingOriginModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    origin = models.CharField(
        max_length=255,
        unique=True
    )
    name = models.CharField(
        max_length=255,
        unique=True
    )
    power = models.IntegerField()
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    edited_at = models.DateTimeField()
    secret = models.CharField(max_length=32, default='')
    comments = models.TextField(blank=True)

    @staticmethod
    def get_brief_origins_arr():
        ping_origins = PingOriginModel.objects.filter(enabled=True).order_by('-id')
        arr = []
        for ping_origin in ping_origins:
            arr.append({
                'type': 'ping',
                'host': ping_origin.origin,
                'power': ping_origin.power
            })
        return arr

    def __unicode__(self):
        return self.name


class PingDataModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    host = models.ForeignKey(PingHostModel)
    transmitted_times = models.IntegerField()
    received_times = models.IntegerField()
    delay_min = models.FloatField()
    delay_avg = models.FloatField()
    delay_max = models.FloatField()
    delay_std = models.FloatField()
    timestamp = models.DateTimeField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    origin = models.ForeignKey(PingOriginModel)

    def percentage_loss(self):
        return float(self.transmitted_times - self.received_times) / float(self.transmitted_times) * 100.0

    def percentage_success(self):
        return float(self.received_times) / float(self.transmitted_times) * 100.0

    def __unicode__(self):
        return self.origin.origin + ' -> ' + self.host.host


class HttpHostModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    host = models.CharField(
        max_length=255,
        unique=True
    )
    name = models.CharField(
        max_length=255,
        unique=True
    )
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    edited_at = models.DateTimeField()
    random_id = models.CharField(max_length=6, default='')
    secure = models.BooleanField(default=False)
    port = models.IntegerField()
    frequency = models.IntegerField(default=900)
    comments = models.TextField(blank=True)

    @staticmethod
    def get_brief_hosts_arr():
        http_hosts = HttpHostModel.objects.filter(enabled=True).order_by('-id')
        arr = []
        for http_host in http_hosts:
            arr.append({
                'type': 'http',
                'host': http_host.host,
                'port': http_host.port,
                'secure': http_host.secure,
                'frequency': http_host.frequency
            })
        return arr

    def __unicode__(self):
        return self.name


class HttpOriginModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    origin = models.CharField(
        max_length=255,
        unique=True
    )
    name = models.CharField(
        max_length=255,
        unique=True
    )
    power = models.IntegerField()
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    edited_at = models.DateTimeField()
    secret = models.CharField(max_length=32, default='')
    ua = models.CharField(
        default='',
        max_length=512
    )
    comments = models.TextField(blank=True)

    @staticmethod
    def get_brief_origins_arr():
        http_origins = HttpOriginModel.objects.filter(enabled=True).order_by('-id')
        arr = []
        for http_origin in http_origins:
            arr.append({
                'type': 'http',
                'host': http_origin.origin,
                'power': http_origin.power,
                'ua': http_origin.ua
            })
        return arr

    def __unicode__(self):
        return self.name


class HttpDataModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    host = models.ForeignKey(HttpHostModel)
    succeed = models.BooleanField(default=False)
    code = models.IntegerField(default=200)
    header = models.TextField()
    delay_std = models.FloatField()
    timestamp = models.DateTimeField(auto_now=True)
    origin = models.ForeignKey(HttpOriginModel)

    def __unicode__(self):
        return self.host.host + ' [' + str(self.code) + ']'


class RespHostModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    host = models.CharField(
        max_length=255,
        unique=True
    )
    name = models.CharField(
        max_length=255,
        unique=True
    )
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    edited_at = models.DateTimeField()
    random_id = models.CharField(max_length=6, default='')
    url = models.CharField(max_length=255)
    method = models.IntegerField(default=0, choices=(
        (0, 'HEAD'),
        (1, 'GET'),
        (2, 'POST'),
    ))
    headers = models.TextField(blank=True)
    body = models.TextField(blank=True)
    match_method = models.IntegerField(default=0, choices=(
        (0, 'Simple'),
        (1, 'Regexp'),
    ))
    expected_headers = models.TextField(blank=True)
    expected_body = models.TextField(blank=True)
    frequency = models.IntegerField(default=900)
    comments = models.TextField(blank=True)

    @staticmethod
    def get_brief_hosts_arr():
        resp_hosts = RespHostModel.objects.filter(enabled=True).order_by('-id')
        arr = []
        for resp_host in resp_hosts:
            arr.append({
                'type': 'resp',
                'url': resp_host.url,
                'method': resp_host.method,
                'headers': resp_host.headers,
                'body': resp_host.body,
                'match_method': resp_host.match_method,
                'expected_headers': resp_host.expected_headers,
                'expected_body': resp_host.expected_body,
                'frequency': resp_host.frequency
            })
        return arr


class RespOriginModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    origin = models.CharField(
        max_length=255,
        unique=True
    )
    name = models.CharField(
        max_length=255,
        unique=True
    )
    power = models.IntegerField()
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    edited_at = models.DateTimeField()
    secret = models.CharField(max_length=32, default='')
    bandwidth = models.FloatField()
    comments = models.TextField(blank=True)

    @staticmethod
    def get_brief_origins_arr():
        resp_origins = RespOriginModel.objects.filter(enabled=True).order_by('-id')
        arr = []
        for resp_origin in resp_origins:
            arr.append({
                'type': 'resp',
                'host': resp_origin.origin,
                'power': resp_origin.power,
                'ua': resp_origin.ua
            })
        return arr


class RespDataModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    host = models.ForeignKey(RespHostModel)
    succeed = models.BooleanField(default=False)
    code = models.IntegerField(default=200)
    response_header = models.TextField()
    response_body = models.TextField()
    delay_std = models.FloatField()
    timestamp = models.DateTimeField(auto_now=True)
    origin = models.ForeignKey(RespOriginModel)
    passed = models.BooleanField(default=False)


class SiteHourlyReportModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.IntegerField(default=0, choices=(
        (0, 'Custom'),
        (1, 'Ping Success'),
        (2, 'Ping Delay'),
        (3, 'Http Success'),
        (4, 'Http Delay'),
        (5, 'Response Success'),
        (6, 'Response Delay'),
        (7, 'Exceptions'),
    ))
    value = models.FloatField(default=0.0)
    comments = models.TextField(default='No comment')


class HttpHourlyReportModel(SiteHourlyReportModel):
    host = models.ForeignKey(HttpHostModel)


class PingHourlyReportModel(SiteHourlyReportModel):
    host = models.ForeignKey(PingHostModel)


class RespHourlyReportModel(SiteHourlyReportModel):
    host = models.ForeignKey(RespHostModel)


class SiteReportModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.IntegerField(default=0, choices=(
        (0, 'Custom'),
        (1, 'Ping Success'),
        (2, 'Ping Delay'),
        (3, 'Http Success'),
        (4, 'Http Delay'),
        (5, 'Response Success'),
        (6, 'Response Delay'),
        (7, 'Exceptions'),
    ))
    value = models.FloatField(default=0.0)

    @staticmethod
    def generate_all_hosts_graph_data(start_type):
        all_ping_hosts = PingHostModel.objects.filter(
            enabled=True
        ).all()
        ping_arr = []
        for ping_host in all_ping_hosts:
            ping_arr += SiteReportModel.get_ping_host_graph_data(ping_host, start_type)
        all_http_hosts = HttpHostModel.objects.filter(
            enabled=True
        ).all()
        http_arr = []
        for http_host in all_http_hosts:
            http_arr += SiteReportModel.get_http_host_graph_data(http_host, start_type)
        arr = ping_arr + http_arr
        return arr

    @staticmethod
    def get_ping_host_graph_data(host_obj, start_type):
        host_status_arr = []
        ping_success_dict = SiteReportModel.get_graph_data(host_obj, start_type, 1)
        if ping_success_dict is not None:
            host_status_arr.append(ping_success_dict)
        ping_delay_dict = SiteReportModel.get_graph_data(host_obj, start_type, 2)
        if ping_delay_dict is not None:
            host_status_arr.append(ping_delay_dict)
        return host_status_arr

    @staticmethod
    def get_http_host_graph_data(host_obj, start_type):
        host_status_arr = []
        http_success_dict = SiteReportModel.get_graph_data(host_obj, start_type, 3)
        if http_success_dict is not None:
            host_status_arr.append(http_success_dict)
        http_delay_dict = SiteReportModel.get_graph_data(host_obj, start_type, 4)
        if http_delay_dict is not None:
            host_status_arr.append(http_delay_dict)
        return host_status_arr

    @staticmethod
    def get_graph_data(host_obj, start_type, graph_type=1):
        if start_type == 0:
            start = 86400
            start_at = datetime.datetime.fromtimestamp(start)
            end_at = datetime.datetime.fromtimestamp(time.time())
            if graph_type == 1 or graph_type == 2:
                range_report = PingReportModel.objects.filter(
                    host=host_obj,
                    type=graph_type,
                    created_at__range=(start_at, end_at)
                ).values('created_at', 'value').order_by('id')
            elif graph_type == 3 or graph_type == 4:
                range_report = HttpReportModel.objects.filter(
                    host=host_obj,
                    type=graph_type,
                    created_at__range=(start_at, end_at)
                ).values('created_at', 'value').order_by('id')
            elif graph_type == 5 or graph_type == 6:
                range_report = RespReportModel.objects.filter(
                    host=host_obj,
                    type=graph_type,
                    created_at__range=(start_at, end_at)
                ).values('created_at', 'value').order_by('id')
            else:
                return None
        elif start_type == 1 or start_type == 2:
            if start_type == 1:
                start = 604800
            else:
                start = 2592000
            start_at = datetime.datetime.fromtimestamp(start)
            end_at = datetime.datetime.fromtimestamp(time.time())
            if graph_type == 1 or graph_type == 2:
                range_report = PingHourlyReportModel.objects.filter(
                    host=host_obj,
                    type=graph_type,
                    created_at__range=(start_at, end_at)
                ).values('created_at', 'value').order_by('id')
            elif graph_type == 3 or graph_type == 4:
                range_report = HttpHourlyReportModel.objects.filter(
                    host=host_obj,
                    type=graph_type,
                    created_at__range=(start_at, end_at)
                ).values('created_at', 'value').order_by('id')
            elif graph_type == 5 or graph_type == 6:
                range_report = RespHourlyReportModel.objects.filter(
                    host=host_obj,
                    type=graph_type,
                    created_at__range=(start_at, end_at)
                ).values('created_at', 'value').order_by('id')
            else:
                return None
        else:
            return None
        report_nums = len(range_report)
        if report_nums == 0:
            return None
        data = []
        total_value = 0.0
        for report in range_report:
            total_value += report['value']
            data.append([time.mktime(report['created_at'].timetuple()), float(report['value'])])
        avg_value = float(total_value) / report_nums
        if len(data) == 0:
            return None
        last_created_at = data[-1][0]
        if graph_type == 2 or graph_type == 4 or graph_type == 6:
            unit = 'ms'
        else:
            unit = '%'
        if graph_type == 1:
            graph_name = ' 线路可用性'
        elif graph_type == 2:
            graph_name = ' 线路延迟'
        elif graph_type == 3:
            graph_name = ' 有效 Web 响应率'
        elif graph_type == 4:
            graph_name = ' 有效 Web 响应时间'
        elif graph_type == 5:
            graph_name = ' 有效 API 响应率'
        elif graph_type == 6:
            graph_name = '有效 API 响应时间'
        else:
            return None
        graph_item = {
            'title': host_obj.name + graph_name,
            'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_created_at)),
            'value': str('%.2f' % avg_value) + unit,
            'data_string': json.dumps(data),
            'unit': unit
        }
        return graph_item

    @staticmethod
    def get_latest_updated_tuple():
        obj = SiteReportModel.objects.order_by('-id')[:1]
        if not obj:
            return None
        t_obj = obj[0].created_at
        return t_obj.timetuple()

    @staticmethod
    def get_latest_updated_time():
        return SiteMessageModel.get_cst_time_by_value(SiteReportModel.get_latest_updated_tuple())

    @staticmethod
    def generate_new_daily_message():
        # Delete Old Records
        now = datetime.datetime.fromtimestamp(time.time() - 86400)
        PingDataModel.objects.filter(
            timestamp__lte=now
        ).delete()
        HttpDataModel.objects.filter(
            timestamp__lte=now
        ).delete()
        RespDataModel.objects.filter(
            timestamp__lte=now
        ).delete()
        PingReportModel.objects.filter(
            created_at__lte=now
        ).delete()
        HttpReportModel.objects.filter(
            created_at__lte=now
        ).delete()
        RespReportModel.objects.filter(
            created_at__lte=now
        ).delete()
        now = datetime.datetime.fromtimestamp(time.time() - 2678400)
        PingHourlyReportModel.objects.filter(
            created_at__lte=now
        ).delete()
        HttpHourlyReportModel.objects.filter(
            created_at__lte=now
        ).delete()
        RespHourlyReportModel.objects.filter(
            created_at__lte=now
        ).delete()
        # Generate Daily Message
        last_time = 0
        tuple_obj = None
        generate_interval = 86400
        last_obj = SiteMessageModel.objects.filter(
            type=3
        ).order_by('-id')[:1]
        if last_obj:
            t_obj = last_obj[0].created_at
            tuple_obj = t_obj.timetuple()
        if tuple_obj is not None:
            last_time = time.mktime(tuple_obj)
        if (last_time == 0) or (time.time() - last_time >= generate_interval):
            req_start = datetime.datetime.fromtimestamp(
                time.time() - generate_interval
            )
            error_level = 0
            final_message = ''
            global_major = float(SiteConfigModel.get_config('global_major_percentage_threshold'))
            global_minor = float(SiteConfigModel.get_config('global_minor_percentage_threshold'))
            global_good = float(SiteConfigModel.get_config('global_good_percentage_threshold'))

            all_ping_hosts = PingHostModel.objects.filter(
                enabled=True
            ).all()
            for ping_host in all_ping_hosts:
                today_ping_reports = PingReportModel.objects.filter(
                    host=ping_host,
                    created_at__gte=req_start,
                    type=1
                ).values('value')
                avg_ping_reports_rates = 0.0
                total_ping_reports_nums = len(today_ping_reports)
                if total_ping_reports_nums != 0:
                    total_ping_reports_rates = 0.0
                    for ping_report in today_ping_reports:
                        total_ping_reports_rates += float(ping_report['value'])
                    avg_ping_reports_rates = float(total_ping_reports_rates) / total_ping_reports_nums
                if avg_ping_reports_rates == 0.0:
                    break
                if avg_ping_reports_rates <= global_major and error_level < 3:
                    error_level = 3
                    final_message += ping_host.name + ' 网络线路发生故障'
                elif avg_ping_reports_rates <= global_minor and error_level < 2:
                    error_level = 2
                    final_message += ping_host.name + ' 网络线路出现异常'
                elif avg_ping_reports_rates <= global_good and error_level < 1:
                    error_level = 1

            all_http_hosts = HttpHostModel.objects.filter(
                enabled=True
            ).all()
            for http_host in all_http_hosts:
                today_http_reports = HttpReportModel.objects.filter(
                    host=http_host,
                    created_at__gte=req_start,
                    type=3
                ).values('value')
                avg_http_reports_rates = 0.0
                total_http_reports_nums = len(today_http_reports)
                if total_http_reports_nums != 0:
                    total_http_reports_rates = 0.0
                    for http_report in today_http_reports:
                        total_http_reports_rates += float(http_report['value'])
                    avg_http_reports_rates = float(total_http_reports_rates) / total_http_reports_nums
                if avg_http_reports_rates == 0.0:
                    break
                if avg_http_reports_rates <= global_major and error_level < 3:
                    error_level = 3
                    final_message += ping_host.name + ' 服务器发生故障'
                elif avg_http_reports_rates <= global_minor and error_level < 2:
                    error_level = 2
                    final_message += ping_host.name + ' 服务器出现异常'
                elif avg_http_reports_rates <= global_good and error_level < 1:
                    error_level = 1

            if error_level == 0:
                final_message = SiteConfigModel.get_config('default_site_message_content')

            new_auto_message = SiteMessageModel()
            new_auto_message.type = 3
            new_auto_message.status = error_level + 1
            new_auto_message.content = final_message
            new_auto_message.save()

    @staticmethod
    def generate_new_ping_report(host_obj, interval_type=1):
        last_time = 0
        tuple_obj = None
        if interval_type == 1:
            last_obj = PingReportModel.objects.filter(
                host=host_obj
            ).order_by('-id')[:1]
            generate_interval = int(SiteConfigModel.get_config('api_ping_report_interval'))
        else:
            last_obj = PingHourlyReportModel.objects.filter(
                host=host_obj
            ).order_by('-id')[:1]
            generate_interval = 3600
        if last_obj:
            t_obj = last_obj[0].created_at
            tuple_obj = t_obj.timetuple()
        if tuple_obj is not None:
            last_time = time.mktime(tuple_obj)
        if (last_time == 0) or (time.time() - last_time >= generate_interval):
            req_start = datetime.datetime.fromtimestamp(
                time.time() - generate_interval
            )
            recent_ping_reports = PingDataModel.objects.filter(
                host=host_obj,
                timestamp__gte=req_start
            ).values('transmitted_times', 'received_times', 'delay_avg').order_by('-id')
            total_num = len(recent_ping_reports)
            if total_num != 0:
                total_times = 0
                succeed_times = 0
                total_delay = 0.0
                for report in recent_ping_reports:
                    total_times += int(report['transmitted_times'])
                    succeed_times += int(report['received_times'])
                    total_delay += float(report['delay_avg'])
                succeed_rate = float(succeed_times) / total_times
                delay_avg = float(total_delay) / total_num
            else:
                return
            if interval_type == 1:
                new_report = PingReportModel()
            else:
                new_report = PingHourlyReportModel()
            new_report.name = host_obj.name
            new_report.host = host_obj
            new_report.type = 1
            new_report.value = succeed_rate * 100
            new_report.save()

            if interval_type == 1:
                new_report = PingReportModel()
            else:
                new_report = PingHourlyReportModel()
            new_report.name = host_obj.name
            new_report.host = host_obj
            new_report.type = 2
            new_report.value = delay_avg
            new_report.save()

    @staticmethod
    def generate_new_http_report(host_obj, interval_type=1):
        last_time = 0
        tuple_obj = None
        if interval_type == 1:
            last_obj = HttpReportModel.objects.filter(
                host=host_obj
            ).order_by('-id')[:1]
            generate_interval = int(SiteConfigModel.get_config('api_http_report_interval'))
        else:
            last_obj = HttpHourlyReportModel.objects.filter(
                host=host_obj
            ).order_by('-id')[:1]
            generate_interval = 3600
        if last_obj:
            t_obj = last_obj[0].created_at
            tuple_obj = t_obj.timetuple()
        if tuple_obj is not None:
            last_time = time.mktime(tuple_obj)
        if (last_time == 0) or (time.time() - last_time >= generate_interval):
            req_start = datetime.datetime.fromtimestamp(
                time.time() - generate_interval
            )
            recent_http_reports = HttpDataModel.objects.filter(
                host=host_obj,
                timestamp__gte=req_start
            ).values('succeed', 'delay_std').order_by('-id')
            total_num = len(recent_http_reports)
            if total_num != 0:
                total_delay = 0.0
                succeed_num = 0
                for report in recent_http_reports:
                    total_delay += float(report['delay_std'])
                    if report['succeed']:
                        succeed_num += 1
                succeed_rate = float(succeed_num) / total_num
                delay_avg = float(total_delay) / total_num
            else:
                return
            if interval_type == 1:
                new_report = HttpReportModel()
            else:
                new_report = HttpHourlyReportModel()
            new_report.name = host_obj.name
            new_report.host = host_obj
            new_report.type = 3
            new_report.value = succeed_rate * 100
            new_report.save()

            if interval_type == 1:
                new_report = HttpReportModel()
            else:
                new_report = HttpHourlyReportModel()
            new_report.name = host_obj.name
            new_report.host = host_obj
            new_report.type = 4
            new_report.value = delay_avg
            new_report.save()


class HttpReportModel(SiteReportModel):
    host = models.ForeignKey(HttpHostModel)


class PingReportModel(SiteReportModel):
    host = models.ForeignKey(PingHostModel)


class RespReportModel(SiteReportModel):
    host = models.ForeignKey(RespHostModel)


class SiteStatusModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    status = models.IntegerField(default=0, choices=(
        (0, 'Custom'),
        (1, 'Success'),
        (2, 'Warning'),
        (3, 'Notice'),
        (4, 'Error'),
    ))
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def handle_global_status():
        pass


class ActiveHttpHostModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    host = models.CharField(
        max_length=255,
        unique=True
    )
    name = models.CharField(
        max_length=255,
        unique=True
    )
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    edited_at = models.DateTimeField()
    random_id = models.CharField(max_length=6, default='')
    secure = models.BooleanField(default=False)
    port = models.IntegerField()
    framework = models.CharField(max_length=255)
    report_type = models.IntegerField(default=0, choices=(
        (0, 'exception'),
    ))
    package_count = models.IntegerField(default=0)
    comments = models.TextField(blank=True)


class ActiveExceptionModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    host = models.ForeignKey(ActiveHttpHostModel)
    class_name = models.CharField(max_length=255)
    method_name = models.CharField(max_length=255)
    route = models.TextField()
    log_data = models.BinaryField()
    submitted_at = models.DateTimeField(auto_now_add=True)


class ActivePackageModel(models.Model):
    pass


class ActiveExceptionPackageModel(ActivePackageModel):
    pass

