from django.contrib import admin
from django.urls import path,include
from admins import views
urlpatterns = [
    path('',views.index,name='index'),
    path('admin/',include('admins.urls'))
]
