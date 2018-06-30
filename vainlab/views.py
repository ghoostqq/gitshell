from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic

from .forms import NameForm
from .models import Participant, Player, top_actor_win_rates
from .vain_api import VainAPI


def index(request, ):
    form = NameForm()
    return render(request, 'vainlab/index.html', {'form': form})


class PlayerView(generic.DetailView):
    model = Player
    slug_field = 'name'
    template_name = 'vainlab/player.html'

    def get_queryset(self):
        return Player.objects


class PlayersView(generic.ListView):
    template_name = 'vainlab/players.html'
    context_object_name = 'top_players_list'

    def get_queryset(self):
        return Player.objects.filter(
            elo__gte=1600
        ).order_by('-elo')[:10]


def player_matches(request, name):
    form = NameForm()
    # もしプレイヤーがDBに存在しない場合、APIリクエストを送る
    if not Player.objects.filter(name=name).exists():
        err = VainAPI().player_matches_wo_region(name)
        if err:
            return render(request, 'vainlab/player_matches.html', {'error': err, 'form': form})
    # もしプレイヤーがDBに存在して、最後の試合orリクエストから一定時間経過している場合、
    # APIリクエストを送る
    player = Player.objects.get(name=name)
    if player.spent_enough_cooldown_time():
        err = VainAPI().player_matches(player.shard, player.name)
        player.updated_now()
        if err:
            return render(request, 'vainlab/player_matches.html', {'error': err, 'form': form})
    matches = player.match_set.all().order_by('-datetime')[:50]

    return render(request, 'vainlab/player_matches.html',
                  {'player': player, 'matches': matches, 'form': form})


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
