from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import include
from . import views


urlpatterns = [
    url(r'index$', views.index, name='index'),
    url(r'release_signature$', views.release_signature, name='release_signature'),
]

