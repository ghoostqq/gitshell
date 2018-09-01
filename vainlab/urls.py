"""vainlab URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from . import views

# appname = 'vainlab'
urlpatterns = [
    path('', views.index, name='index'),
    # path('player/', views.player_matches, name='player_matches'),
    path('single_player/<slug:slug>/', views.PlayerView.as_view(), name='player'),
    path('players/', views.PlayersView.as_view(), name='players'),
    path('player_matches/<str:name>/',
         views.player_matches, name='player_matches'),
    path('matches/', views.MatchesView.as_view(), name='matches'),
    path('match/<slug:slug>/', views.MatchView.as_view(), name='match'),
    path('match_telemetry/<str:match_id>/',
         views.match_telemetry, name='match_telemetry'),
    path('match_telemetry/<str:match_id>/<str:actor>/', views.match_telemetry_participant_items,
         name='match_telemetry_participant_items'),
    path('participants/', views.ParticipantsView.as_view(), name='participants'),
    path('search_player/', views.search_player, name='search_player'),
    # path('form/', views.form, name='form'),
    path('rankings/', views.ranking, name='rankings'),
]
