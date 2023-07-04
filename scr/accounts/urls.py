from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from accounts.views import signup, logout_user, login_user

from fshop import settings

urlpatterns = [
    path('', signup, name='signup'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
]
