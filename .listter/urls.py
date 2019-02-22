from django.urls import path

from listter.views import (listsView, post_lists, post_member, topView,
                           twitter_authenticated, twitter_login,
                           twitter_logout)

urlpatterns = [
    path('', topView, name='top'),
    path('login/', twitter_login, name='login'),
    path('logout/', twitter_logout, name='logout'),
    path('login/authenticated', twitter_authenticated),
    path('lists/', listsView, name='lists'),
    path('post_lists/', post_lists, name='post_lists'),
    path('post_member/', post_member, name='post_member'),
]
