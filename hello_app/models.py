# coding:utf-8
from __future__ import unicode_literals
import datetime
import time
import pytz
from django.db import models

# Create your models here.


class SiteConfigModel(models.Model):
    key = models.CharField(max_length=64, unique=True)
    value = models.CharField(max_length=256)
    comments = models.TextField()

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

    # Shell Config Method
    @staticmethod
    def init_config():
        SiteConfigModel.add_config('default_site_message_content', 'All systems reporting at 100%')
        SiteConfigModel.add_config('default_site_recent_duration', str(604800))
        SiteConfigModel.add_config(
            'default_origin_user_agent',
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) " +
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36"
        )
        SiteConfigModel.add_config('api_status_url', 'https://status.play4u.cn/api/status.json')
        SiteConfigModel.add_config('api_messages_url', 'https://status.play4u.cn/api/messages.json')
        SiteConfigModel.add_config('api_last_message_url', 'https://status.play4u.cn/api/last-message.json')
        SiteConfigModel.add_config('api_hosts_url', 'https://status.play4u.cn/api/hosts.json')
        SiteConfigModel.add_config('api_origins_url', 'https://status.play4u.cn/api/origins.json')
        SiteConfigModel.add_config('global_good_percentage_threshold', '99.00')
        SiteConfigModel.add_config('global_minor_percentage_threshold', '90.00')
        SiteConfigModel.add_config('global_major_percentage_threshold', '80.00')

    def __unicode__(self):
        return self.key + ' = "' + self.value + '"'


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
    content = models.TextField(default=str(SiteConfigModel.get_config('default_site_message_content')))
    power = models.IntegerField(default=0)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "[" + self.get_type_display() + ", " + self.get_status_display() + "] " + self.content


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
            req_time - int(SiteConfigModel.get_config('default_site_recent_duration')),
            tz=pytz.utc
        )
        req_end = datetime.datetime.fromtimestamp(req_time, tz=pytz.utc)
        recent_messages_list = SiteMessageModel.objects.filter(
            enabled=True,
            created_at__range=(req_start, req_end)
        ).extra(select={
            'body': "`content`"
        }).values('status', 'body', 'created_at').order_by('-id')
        if not recent_messages_list:
            return None
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
        req_pos = datetime.datetime.fromtimestamp(req_time, tz=pytz.utc)
        obj = SiteMessageModel.objects.filter(created_at__lte=req_pos)[:1]
        if not obj:
            return None
        else:
            return (req_pos + datetime.timedelta(-7)).strftime('%Y-%m-%d')

    @staticmethod
    def has_page_next_than_time(req_time):
        req_pos = datetime.datetime.fromtimestamp(req_time, tz=pytz.utc)
        obj = SiteMessageModel.objects.filter(created_at__gte=req_pos)[:1]
        if not obj:
            return None
        else:
            return req_pos.strftime('%Y-%m-%d')

    @staticmethod
    def get_weekly_messages_list(req_time):
        req_start = datetime.datetime.fromtimestamp(req_time, tz=pytz.utc)
        req_end = datetime.datetime.fromtimestamp(req_time + 604800, tz=pytz.utc)
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
                        'display': datetime.datetime.strftime(tmp, "%B %d, %Y"),
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

    def __unicode__(self):
        return self.name


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
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name


class PingHostModel(CommonHostModel):
    pass


class PingOriginModel(CommonOriginModel):
    pass


class PingDataModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    host = models.ForeignKey(PingHostModel)
    transmitted_times = models.IntegerField()
    received_times = models.IntegerField()
    delay_min = models.FloatField()
    delay_avg = models.FloatField()
    delay_max = models.FloatField()
    delay_std = models.FloatField()
    timestamp = models.DateTimeField(auto_now=True)
    origin = models.ForeignKey(PingOriginModel)

    def percentage_loss(self):
        return float(self.transmitted_times - self.received_times) / float(self.transmitted_times) * 100.0

    def percentage_success(self):
        return float(self.received_times) / float(self.transmitted_times) * 100.0


class HttpHostModel(CommonHostModel):
    secure = models.BooleanField(default=False)
    port = models.IntegerField()


class HttpOriginModel(CommonOriginModel):
    ua = models.CharField(
        default=SiteConfigModel.get_config('default_origin_user_agent'),
        max_length=512
    )


class HttpDataModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    host = models.ForeignKey(HttpHostModel)
    succeed = models.BooleanField(default=False)
    code = models.IntegerField(default=200)
    header = models.TextField()
    delay_std = models.FloatField()
    timestamp = models.DateTimeField(auto_now=True)
    origin = models.ForeignKey(PingOriginModel)


class CommonReportModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    host = models.ForeignKey(CommonHostModel),
    started_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.IntegerField(default=0, choices=(
        (0, 'Custom'),
        (1, 'PingSuccess'),
        (2, 'PingDelay'),
        (3, 'HttpSuccess'),
        (4, 'HttpDelay'),
        (5, 'RespSuccess'),
        (6, 'RespDelay'),
        (7, 'Exceptions'),
    ))
    value = models.FloatField(default=0.0)
    comments = models.TextField(default='No comment')


class SiteReportModel(CommonReportModel):
    caches = models.TextField(blank=True)

    def __unicode__(self):
        title = '[SiteReportModel CustomObject]'
        if self.type == 1:
            title = 'Ping Success Percentage: ' + str(self.value) + '%'
        elif self.type == 2:
            title = 'Ping Average Delay: ' + str(self.value) + 'ms'
        elif self.type == 3:
            title = 'Http Response Success Percentage: ' + str(self.value) + '%'
        elif self.type == 4:
            title = 'Http Average Delay: ' + str(self.value) + 'ms'
        elif self.type == 5:
            title = 'Specific Response Success Percentage: ' + str(self.value) + '%'
        elif self.type == 6:
            title = 'Specific Response Delay: ' + str(self.value) + 'ms'
        elif self.type == 7:
            title = 'Exception Percentage: ' + str(self.value) + '%'
        return title

    @staticmethod
    def get_latest_updated_time():
        obj = SiteReportModel.objects.order_by('-id')[:1]
        if not obj:
            return None
        t_obj = obj[0].created_at
        return SiteMessageModel.get_cst_time_by_value(t_obj)


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
