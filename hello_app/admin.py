from django.contrib import admin
from hello_app.models import *

# Register your models here.


class SiteConfigCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
admin.site.register(SiteConfigCategoryModel, SiteConfigCategoryAdmin)


class SiteConfigAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'category', 'modified_at')
    search_fields = ['key']
admin.site.register(SiteConfigModel, SiteConfigAdmin)


class SiteReportAdmin(admin.ModelAdmin):
    list_display = ('host', 'type', 'value', 'created_at')
    search_fields = ['host']
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

admin.site.register(PingOriginModel)
admin.site.register(PingHostModel)
admin.site.register(PingDataModel)

admin.site.register(HttpOriginModel)
admin.site.register(HttpHostModel)
admin.site.register(HttpDataModel)

admin.site.register(RespOriginModel)
admin.site.register(RespHostModel)
admin.site.register(RespDataModel)

admin.site.register(ActiveExceptionModel)
admin.site.register(ActiveExceptionPackageModel)
admin.site.register(ActiveHttpHostModel)
