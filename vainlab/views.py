import json
from threading import Thread

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from .forms import NameForm
from .models import Match, Participant, Player, top_actor_win_rates
from .vain_api import MatchTelemetry, VainAPI

vg = VainAPI()


def index(request, ):
    form = NameForm()
    return render(request, 'vainlab/index.html', {'form': form})


class PlayerView(DetailView):
    model = Player
    slug_field = 'name'
    template_name = 'vainlab/player.html'


class PlayersView(ListView):
    template_name = 'vainlab/players.html'
    context_object_name = 'top_players_list'

    def get_queryset(self):
        return Player.objects.filter(
            elo__gte=1600
        ).order_by('-elo')[:10]


class MatchesView(ListView):
    model = Match


class MatchView(DetailView):
    model = Match
    slug_field = 'id'


class ParticipantsView(ListView):
    model = Participant


def play_log(request, name):
    form = NameForm()

    # See if name is in Player
    # If exists, return Player and its Participant list
    # If not (means first visit), use api to request Player


def player_matches(request, name):
    form = NameForm()
    # もしプレイヤーがDBに存在しない場合、APIリクエストを送る
    if not Player.objects.filter(name=name).exists():
        err = vg.player_matches_wo_region(name)
        if err:
            return render(request, 'vainlab/player_matches.html', {'error': err, 'form': form})
    # もしプレイヤーがDBに存在して、最後の試合orリクエストから一定時間経過している場合、
    # APIリクエストを送る
    player = Player.objects.get(name=name)
    if player.spent_enough_cooldown_time():
        err = vg.player_matches(player.shard, player.name)
        player.updated_now()
        if err:
            return render(request, 'vainlab/player_matches.html', {'error': err, 'form': form})
    matches = player.match_set.all().order_by('-datetime')[:50]
    player_matches = [(m.participant_set.get(player=player), m)
                      for m in matches]

    # Match Telemetry
    for match in matches:
        MatchTelemetry(match).daemon_process_match_obj()

    return render(request, 'vainlab/player_matches.html',
                  {'player': player, 'player_matches': player_matches, 'form': form})


def match_telemetry(request, match_id):
    # Should return error instead.
    m = Match.objects.get(id=match_id)
    t = MatchTelemetry(m)
    res = json.dumps(t.get_assets())
    t.daemon_process_match_obj()
    return HttpResponse(res)


def match_telemetry_participant_items(request, match_id, actor):
    m = Match.objects.get(id=match_id)
    t = MatchTelemetry(m)
    return HttpResponse([
        t._participant_buy_item(actor),
        # m.participant_set.get(actor=actor).items,
        t._participant_core_item_ids(actor)
    ])


def search_player(request, ):
    if request.method == 'POST':
        form = NameForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            return redirect('player_matches', name=name)


def ranking(request, ):
    form = NameForm()
    ranking_rows = top_actor_win_rates(Participant)
    return render(request, 'vainlab/ranking.html', {'rankings': ranking_rows, 'form': form})
