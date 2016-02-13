from django.contrib import admin
from hello_app.models import *

# Register your models here.

admin.site.register(SiteReportModel)
admin.site.register(SiteMessageModel)
admin.site.register(SiteConfigModel)

admin.site.register(PingOriginModel)
admin.site.register(PingHostModel)
admin.site.register(PingDataModel)

admin.site.register(HttpOriginModel)
admin.site.register(HttpHostModel)
admin.site.register(HttpDataModel)
