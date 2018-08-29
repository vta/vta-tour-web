
from django.conf.urls import url,include	
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView
from vtatour import views

urlpatterns = [
    url(r'^$', views.index.as_view(template_name='base.html'), name='index'),
    url(r'^login/$', auth_views.login, {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'template_name': 'logged_out.html'}, name='logout'),
    url(r'^admin/', admin.site.urls),
    url(r'^$', include('vtatour.urls')), # tell django to read urls.py in example app
]
