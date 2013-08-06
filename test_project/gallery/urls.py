from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns('',
    url(r'^$', view=views.CeleryDownloadView.as_view(),
        name='celery_download'),
    url(r'^(?P<pk>[0-9]+)/$', view=views.CeleryResultView.as_view(),
        name='celery_result'),
)
