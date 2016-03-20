from django.contrib import admin
from hello_app.models import *

# Register your models here.


class SiteConfigCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
admin.site.register(SiteConfigCategoryModel, SiteConfigCategoryAdmin)


class SiteConfigAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'category', 'modified_at')
    list_filter = ['category']
    search_fields = ['key']
admin.site.register(SiteConfigModel, SiteConfigAdmin)


class SiteReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'value', 'created_at')
    search_fields = ['name']
    list_filter = ['type']
admin.site.register(SiteReportModel, SiteReportAdmin)


class SiteMessageAdmin(admin.ModelAdmin):
    list_display = ('content', 'enabled', 'type', 'status', 'modified_at')
    search_fields = ['content']
    list_filter = ['type', 'status']
admin.site.register(SiteMessageModel, SiteMessageAdmin)


class SiteStatusAdmin(admin.ModelAdmin):
    pass
admin.site.register(SiteStatusModel, SiteStatusAdmin)


class PingOriginAdmin(admin.ModelAdmin):
    list_display = ('origin', 'name', 'power', 'enabled', 'modified_at')
    search_fields = ['origin', 'name']
    list_filter = ['enabled']
admin.site.register(PingOriginModel, PingOriginAdmin)


class PingHostAdmin(admin.ModelAdmin):
    list_display = ('host', 'name', 'enabled', 'modified_at')
    search_fields = ['host', 'name']
    list_filter = ['enabled']
admin.site.register(PingHostModel, PingHostAdmin)


class PingDataAdmin(admin.ModelAdmin):
    list_display = ('host', 'origin', 'transmitted_times', 'received_times', 'delay_avg', 'timestamp')
    search_fields = ['host', 'origin']
    list_filter = ['host', 'origin']
admin.site.register(PingDataModel, PingDataAdmin)


class HttpOriginAdmin(admin.ModelAdmin):
    list_display = ('origin', 'name', 'power', 'enabled', 'modified_at')
    search_fields = ['origin', 'name']
    list_filter = ['enabled']
admin.site.register(HttpOriginModel, HttpOriginAdmin)


class HttpHostAdmin(admin.ModelAdmin):
    list_display = ('host', 'port', 'name', 'enabled', 'secure', 'modified_at')
    search_fields = ['host', 'name']
    list_filter = ['enabled', 'secure']
admin.site.register(HttpHostModel, HttpHostAdmin)


class HttpDataAdmin(admin.ModelAdmin):
    list_display = ('host', 'origin', 'succeed', 'code', 'delay_std', 'timestamp')
    search_fields = ['host', 'origin']
    list_filter = ['host', 'origin', 'succeed']
admin.site.register(HttpDataModel, HttpDataAdmin)

admin.site.register(RespOriginModel)
admin.site.register(RespHostModel)
admin.site.register(RespDataModel)

admin.site.register(ActiveExceptionModel)
admin.site.register(ActiveExceptionPackageModel)
admin.site.register(ActiveHttpHostModel)
