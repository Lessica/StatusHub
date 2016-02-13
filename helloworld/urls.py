"""helloworld URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.views.generic.base import RedirectView
from hello_app import views as hello_views

urlpatterns = [
    url(r'^$|^graphs/(past_day|past_week|past_month)', hello_views.index),
    url(r'^messages/$|^messages/(\d{4}-\d{2}-\d{2})$', hello_views.messages),
    url(r'^api/$', hello_views.api),
    url(r'^api.json$', hello_views.api_json),
    url(r'^api/status.json$', hello_views.api_status),
    url(r'^api/last-message.json$', hello_views.api_last_message),
    url(r'^api/messages.json$', hello_views.api_messages),
    url(r'^api/hosts.json$', hello_views.api_hosts),
    url(r'^api/origins.json$', hello_views.api_origins),
    url(r'^hello/$', hello_views.hello),
    url(r'^admin/', admin.site.urls),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/images/favicon.ico')),
]
