from django.urls import path
from . import views

urlpatterns = [
    path('',views.index,name='index'),
    path('register',views.register, name='register'),
    path('login/verify',views.verify_email, name='verify_email'),
    path('login', views.login,name='login'),
    path('home', views.home,name='home'),
    path('logout',views.logout,name='logout'),
    path('kids',views.kids,name='kids'),
    path('kids/new',views.add_kids,name='add_kids'),
    path('images/edit/<int:id>/',views.update_images,name='update_images')
]