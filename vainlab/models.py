import datetime
import json
from logging import DEBUG, StreamHandler, getLogger

from django.db import models as m
from django.utils import timezone
from django_pandas.io import read_frame

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False


class Player(m.Model):
    id = m.CharField(max_length=100, unique=True, primary_key=True)
    name = m.CharField(max_length=50, db_index=True)
    # slug = m.SlugField(max_length=50)
    # name = m.SlugField(max_length=50)
    shard = m.CharField('region', max_length=10)
    elo = m.PositiveSmallIntegerField(default=0)  # 0 to 32767
    tier = m.PositiveSmallIntegerField(default=0)
    wins = m.PositiveIntegerField(default=0)

    last_update_at = m.DateTimeField(
        'last time searched for matches', default=timezone.now() - datetime.timedelta(minutes=1))

    def __str__(self):
        return self.name

    def tier_str(self):
        return str(self.tier)

    def spent_enough_cooldown_time(self):
        return self.last_update_at < (timezone.now() - datetime.timedelta(minutes=1))

    def updated_now(self):
        self.last_update_at = timezone.now()


class Match(m.Model):
    players = m.ManyToManyField(Player)

    id = m.CharField(max_length=100, unique=True, primary_key=True)
    datetime = m.DateTimeField('when a match is created')
    mode = m.CharField(max_length=50)
    version = m.CharField(max_length=10)
    # has two rosters.
    telemetry_url = m.URLField(null=True, max_length=200)

    def __str__(self):
        return self.mode

    def mode_ja(self):
        MODE_JA = {
            'casual':                           'カジュアル',
            'ranked':                           'ランク',
            'casual_aral':                      '大乱闘',
            'blitz_pvp_ranked':                 '電撃',
            'blitz_rounds_pvp_casual':          'ガチンコ',
            'private':                          'プラベカジュ',
            'private_party_draft_match':        'プラベドラフト',
            'private_party_aral_match':         'プラベ大乱闘',
            'private_party_blitz_match':        'プラベ電撃',
            'private_party_blitz_rounds_match': 'プラベガチンコ',
            'private_party_vg_5v5':             'プラベ5V5カジュ',
            'private_party_draft_match_5v5':    'プラベ5V5ドラフト',
            '5v5_pvp_casual':                   '5V5カジュ',
            '5v5_pvp_ranked':                   '5V5ランク',
        }
        return MODE_JA.get(self.mode, self.mode)


class Roster(m.Model):
    match = m.ForeignKey(Match, on_delete=m.CASCADE)

    id = m.CharField(max_length=100, unique=True, primary_key=True)
    team_kill_score = m.PositiveSmallIntegerField(default=0)
    side = m.CharField(max_length=10)
    turret_kill = m.PositiveSmallIntegerField(default=0)
    turret_remain = m.PositiveSmallIntegerField(default=0)
    # has 3 participants.

    def __str__(self):
        return self.side


class Participant(m.Model):
    player = m.ForeignKey(Player, on_delete=m.PROTECT)
    match = m.ForeignKey(Match, on_delete=m.PROTECT)
    roster = m.ForeignKey(Roster, on_delete=m.PROTECT)

    id = m.CharField(max_length=100, unique=True, primary_key=True)
    shard = m.CharField('region', max_length=10)
    kills = m.PositiveSmallIntegerField(default=0)
    deaths = m.PositiveSmallIntegerField(default=0)
    assists = m.PositiveSmallIntegerField(default=0)
    # kda
    gold = m.PositiveSmallIntegerField(default=0)
    farm = m.PositiveSmallIntegerField(default=0)
    items = m.CharField(max_length=200)
    tier = m.CharField(max_length=10)
    won = m.BooleanField()

    actor = m.CharField(max_length=50)

    # Telemetry
    items_core_3 = m.CharField(null=True, max_length=100)
    items_core_4 = m.CharField(null=True, max_length=100)

    items_buy_order = m.CharField(null=True, max_length=500)

    def __str__(self):
        return self.actor

    def save(self, *args, **kwargs):
        # Before save
        if False:
            items = json.loads(self.items)
            for item_name in items:
                item, created = Item.objects.get_or_create(name=item_name)
                if created:
                    logger.debug(f'Created: {item}')
        # Default save
        super(Participant, self).save(*args, **kwargs)
        # After save

    def won_ja(self):
        return ('敗北', '勝利')[self.won]

    def items_list(self):
        items = json.loads(self.items)
        css_readable_items = [
            i.replace(' ', '-').replace("'", "").lower() for i in items]
        return css_readable_items

    def actor_strip(self):
        return self.actor.replace('*', '')

    def kda(self):
        # KDA http://vainglory.pchw.io/entry/2016/02/29/092408
        return '%.2f' % ((self.kills + self.assists) / (self.deaths + 1))

    def side_color(self):
        return self.side.split('/')[1]

    def side_class(self):
        return self.side.replace('/', '-')


class Item(m.Model):
    name = m.CharField(max_length=100, unique=True, primary_key=True)
    tier = m.SmallIntegerField(null=True, default=0)

    def __str__(self):
        return f'[Tier: {self.tier}] {self.name}'


def top_actor_win_rates(participant_class):
    ''' returns generate index and row '''
    df = read_frame(participant_class.objects.all(), ['actor', 'won'])
    rank = df.groupby('actor', as_index=False).mean(
    ).sort_values(by='won', ascending=False)
    rank['win_rate'] = rank.won.apply(lambda x: '%.2f' % (x * 100))
    return rank.iterrows()
