from django.urls import path

from listter.views import (listsView, topView, twitter_authenticated,
                           twitter_login, twitter_logout)

urlpatterns = [
    path('', topView, name='top'),
    path('login/', twitter_login, name='login'),
    path('logout/', twitter_logout, name='logout'),
    path('login/authenticated', twitter_authenticated),
    path('lists/', listsView, name='lists'),
]
