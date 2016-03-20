# coding:utf-8
from __future__ import unicode_literals
import datetime
import time
import pytz
from django.db import models

# Create your models here.


class SiteConfigCategoryModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
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
        obj = SiteMessageModel.objects.filter(type=1, enabled=True).order_by('-id')[:1]
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
            return (req_pos + datetime.timedelta(-7)).strftime('%Y-%m-%d')

    @staticmethod
    def has_page_next_than_time(req_time):
        req_pos = datetime.datetime.fromtimestamp(req_time)
        obj = SiteMessageModel.objects.filter(created_at__gte=req_pos)[:1]
        if not obj:
            return None
        else:
            return req_pos.strftime('%Y-%m-%d')

    @staticmethod
    def get_weekly_messages_list(req_time):
        req_start = datetime.datetime.fromtimestamp(req_time)
        req_end = datetime.datetime.fromtimestamp(req_time + 604800)
        weekly_messages_list = SiteMessageModel.objects.filter(
            enabled=True,
            created_at__range=(req_start, req_end)
        ).extra(select={
            'date': "date(`created_at`)"
        }).values('type', 'status', 'content', 'date', 'created_at').order_by('-id')
        if not weekly_messages_list:
            return None
        new_messages_list = {}
        for weekly_message in weekly_messages_list:
            if weekly_message['type'] == 3:
                weekly_message['type'] = 'auto-message'
            else:
                weekly_message['type'] = ''
            weekly_message['status'] = SiteMessageModel.get_status_style_class_by_value(weekly_message['status'])
            if weekly_message['date']:
                if weekly_message['date'] not in new_messages_list:
                    tmp = datetime.datetime.strptime(weekly_message['date'], "%Y-%m-%d")
                    new_messages_list[weekly_message['date']] = {
                        'display': datetime.datetime.strftime(datetime.date(tmp.year, tmp.month, tmp.day), "%B %d, %Y"),
                        'list': []
                    }
                new_messages_list[weekly_message['date']]['list'].append(weekly_message)
        if not new_messages_list:
            return None
        return new_messages_list

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
    checked_count = models.IntegerField(default=0)
    random_id = models.CharField(max_length=6, default='')

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
    sent_count = models.IntegerField(default=0)
    frequency = models.IntegerField(default=900)
    secret = models.CharField(max_length=32, default='')

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
    checked_count = models.IntegerField(default=0)
    random_id = models.CharField(max_length=6, default='')

    @staticmethod
    def get_brief_hosts_arr():
        ping_hosts = PingHostModel.objects.filter(enabled=True).order_by('-id')
        arr = []
        for ping_host in ping_hosts:
            arr.append({
                'type': 'ping',
                'host': ping_host.host
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
    sent_count = models.IntegerField(default=0)
    frequency = models.IntegerField(default=900)
    secret = models.CharField(max_length=32, default='')

    @staticmethod
    def get_brief_origins_arr():
        ping_origins = PingOriginModel.objects.filter(enabled=True).order_by('-id')
        arr = []
        for ping_origin in ping_origins:
            arr.append({
                'type': 'ping',
                'host': ping_origin.origin,
                'power': ping_origin.power,
                'frequency': ping_origin.frequency,
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
    checked_count = models.IntegerField(default=0)
    random_id = models.CharField(max_length=6, default='')
    secure = models.BooleanField(default=False)
    port = models.IntegerField()

    @staticmethod
    def get_brief_hosts_arr():
        http_hosts = HttpHostModel.objects.filter(enabled=True).order_by('-id')
        arr = []
        for http_host in http_hosts:
            arr.append({
                'type': 'http',
                'host': http_host.host,
                'port': http_host.port,
                'secure': http_host.secure
            })
        return arr

    def __unicode__(self):
        return self.name


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
    checked_count = models.IntegerField(default=0)
    random_id = models.CharField(max_length=6, default='')
    url = models.CharField(max_length=255)
    expected_contents = models.TextField()

    @staticmethod
    def get_brief_hosts_arr():
        resp_hosts = RespHostModel.objects.filter(enabled=True).order_by('-id')
        arr = []
        for resp_host in resp_hosts:
            arr.append({
                'type': 'resp',
                'url': resp_host.url
            })
        return arr


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
    sent_count = models.IntegerField(default=0)
    frequency = models.IntegerField(default=900)
    secret = models.CharField(max_length=32, default='')
    ua = models.CharField(
        default='',
        max_length=512
    )

    @staticmethod
    def get_brief_origins_arr():
        http_origins = HttpOriginModel.objects.filter(enabled=True).order_by('-id')
        arr = []
        for http_origin in http_origins:
            arr.append({
                'type': 'http',
                'host': http_origin.origin,
                'power': http_origin.power,
                'frequency': http_origin.frequency,
                'ua': http_origin.ua
            })
        return arr

    def __unicode__(self):
        return self.name


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
    sent_count = models.IntegerField(default=0)
    frequency = models.IntegerField(default=900)
    secret = models.CharField(max_length=32, default='')
    ua = models.CharField(
        default='',
        max_length=512
    )
    bandwidth = models.FloatField()

    @staticmethod
    def get_brief_origins_arr():
        resp_origins = RespOriginModel.objects.filter(enabled=True).order_by('-id')
        arr = []
        for resp_origin in resp_origins:
            arr.append({
                'type': 'resp',
                'host': resp_origin.origin,
                'power': resp_origin.power,
                'frequency': resp_origin.frequency,
                'ua': resp_origin.ua
            })
        return arr


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


class SiteReportModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    started_at = models.DateTimeField()
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
    def generate_new_http_report(host_obj, start_at):
        last_time = 0
        tuple_obj = None
        generate_interval = int(SiteConfigModel.get_config('api_http_report_interval'))
        last_obj = HttpReportModel.objects.filter(
            host=host_obj
        ).order_by('-id')[:1]
        if last_obj:
            t_obj = last_obj[0].created_at
            tuple_obj = t_obj.timetuple()
        if tuple_obj is not None:
            last_time = time.mktime(SiteReportModel.get_latest_updated_tuple())
        if (last_time == 0) or (time.time() - last_time >= generate_interval):
            req_start = datetime.datetime.fromtimestamp(
                time.time() - generate_interval
            )
            recent_http_reports = HttpDataModel.objects.filter(
                host=host_obj,
                timestamp__gte=req_start
            ).values('succeed', 'delay_std').order_by('-id')
            succeed_rate = 0.0
            delay_avg = 9999.0
            total_num = len(recent_http_reports)
            if total_num != 0:
                total_delay = 0.0
                succeed_num = 0
                for report in recent_http_reports:
                    total_delay += report['delay_std']
                    if report['succeed']:
                        succeed_num += 1
                succeed_rate = float(succeed_num) / total_num
                delay_avg = float(total_delay) / total_num

            new_report = HttpReportModel()
            new_report.name = host_obj.name
            new_report.host = host_obj
            new_report.type = 3
            new_report.started_at = time.strftime('%Y-%m-%d %H:%M:%S',
                                                  time.localtime(start_at))
            new_report.value = succeed_rate
            new_report.save()

            new_report = HttpReportModel()
            new_report.name = host_obj.name
            new_report.host = host_obj
            new_report.type = 4
            new_report.started_at = time.strftime('%Y-%m-%d %H:%M:%S',
                                                  time.localtime(start_at))
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
    checked_count = models.IntegerField(default=0)
    random_id = models.CharField(max_length=6, default='')
    secure = models.BooleanField(default=False)
    port = models.IntegerField()
    framework = models.CharField(max_length=255)
    report_type = models.IntegerField(default=0, choices=(
        (0, 'exception'),
    ))
    package_count = models.IntegerField(default=0)


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


class RespDataModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    host = models.ForeignKey(RespHostModel)
    succeed = models.BooleanField(default=False)
    code = models.IntegerField(default=200)
    header = models.TextField()
    delay_std = models.FloatField()
    timestamp = models.DateTimeField(auto_now=True)
    origin = models.ForeignKey(RespOriginModel)
    passed = models.BooleanField(default=False)
    size = models.IntegerField(default=0)
    contents = models.TextField()
