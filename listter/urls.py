from django.urls import path

from listter import views
from listter.views.login import (twitter_authenticated, twitter_login,
                                 twitter_logout)

urlpatterns = [
    path('', views.topView, name='top'),
    path('login/', twitter_login),
    path('logout/', twitter_logout),
    path('login/authenticated', twitter_authenticated),
]
