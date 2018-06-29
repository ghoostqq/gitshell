from django.urls import path

from listter import views

urlpatterns = [
    path('', views.topView, name='top'),
]
