import json
import os
from logging import DEBUG, StreamHandler, getLogger
from threading import Thread

import requests

from .helper import ItemHelper
from .models import Item, Match, Participant, Player, Roster

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False


SHARDS = ['ea', 'na', 'sg', 'eu', 'sa', 'cn']
ih = ItemHelper()


class VainAPI:
    ''' vainglory api '''

    def __init__(self):
        self.apikey = os.getenv("VAIN_APIKEY", "")
        self.apikey_crawl = os.getenv("VAIN_APIKEY_CRAWL", "")

    def request(self, url, params):
        headers = {
            'Authorization': self.apikey,
            'X-TITLE-ID': 'semc-vainglory',
            'Accept': 'application/vnd.api+json',
            'Accept-Encoding': 'gzip',
        }
        return requests.get(url, headers=headers, params=params).json()

    def single_player(self, reg, ign):
        url = f'https://api.dc01.gamelockerapp.com/shards/{reg}/players'
        params = {
            'filter[playerNames]': [ign],
        }
        res = self.request(url, params)
        if res.get('errors', ''):
            wrapped = res
        else:
            _attributes = res['data'][0]['attributes']
            wrapped = {
                'id': res['data'][0]['id'],
                'time': _attributes['createdAt'],
                'shrd': _attributes['shardId'],
                'name': _attributes['name'],
                'elo8': _attributes['stats']['elo_earned_season_8'],
                'wstr': _attributes['stats']['winStreak'],
                'lstr': _attributes['stats']['lossStreak'],
                'wins': _attributes['stats']['wins'],
                'tier': _attributes['stats']['skillTier'],
                'rnkp': _attributes['stats']['rankPoints']['ranked'],
                'blzp': _attributes['stats']['rankPoints']['blitz'],
            }
        return wrapped

    def player_matches(self, reg, ign, debug=False):
        url = f'https://api.dc01.gamelockerapp.com/shards/{reg}/matches'
        params = {
            'filter[playerNames]': [ign],
            'sort': '-createdAt',
        }
        res = self.request(url, params)

        if debug:
            with open('./tmp', 'w') as f:
                json.dump(res, f, indent=4)
            return res

        # Exit if error
        if res.get('errors', ''):
            return res

        # ===============
        # Save to DB
        # ===============
        matches = list()
        ro2m = dict()
        ignore_ro = list()
        # Match
        for d in res['data']:
            for i in res['included']:
                if i['type'] == 'asset' and i['id'] == d['relationships']['assets']['data'][0]['id']:
                    # TODO: maybe no url exeption could happen.
                    telemetry_url = i['attributes']['URL']
            match = Match(
                id=d['id'],
                datetime=d['attributes']['createdAt'],
                mode=d['attributes']['gameMode'],
                version=d['attributes']['patchVersion'],
                telemetry_url=telemetry_url,
            )
            match.save()
            matches.append(match)
            for roster in d['relationships']['rosters']['data']:
                ro2m[roster['id']] = d['id']
        pa2r = dict()
        ignore_pa = list()
        # Roster -> Match
        for i in res['included']:
            if i['type'] == 'roster':
                r = Roster(
                    id=i['id'],
                    team_kill_score=i['attributes']['stats']['heroKills'],
                    side=i['attributes']['stats']['side'],
                    turret_kill=i['attributes']['stats']['turretKills'],
                    turret_remain=i['attributes']['stats']['turretsRemaining'],
                    match_id=ro2m[i['id']],
                )
                r.save()
                for participant in i['relationships']['participants']['data']:
                    pa2r[participant['id']] = i['id']
        # Player
        for i in res['included']:
            if i['type'] == 'player':
                p = Player(
                    id=i['id'],
                    name=i['attributes']['name'],
                    # slug=i['attributes']['name'],
                    shard=i['attributes']['shardId'],
                    elo=i['attributes']['stats'].get(
                        'rankPoints', {'ranked': 0})['ranked'],
                    tier=i['attributes']['stats'].get('skillTier', 0),
                    wins=i['attributes']['stats'].get('wins', 0),
                )
                p.save()
        # Participant -> Roster, Player
        for i in res['included']:
            if i['type'] == 'participant':
                # TODO: Do not use try and detect error individually
                try:
                    p = Participant(
                        id=i['id'],
                        actor=i['attributes']['actor'],
                        shard=i['attributes']['shardId'],
                        kills=i['attributes']['stats'].get('kills', 0),
                        deaths=i['attributes']['stats'].get('deaths', 0),
                        assists=i['attributes']['stats'].get('assists', 0),
                        # kda
                        gold=i['attributes']['stats'].get('gold', 0),
                        farm=i['attributes']['stats'].get('farm', 0),
                        items=json.dumps(i['attributes']['stats']
                                         .get('items', [])[::-1][:6][::-1]),
                        tier=i['attributes']['stats'].get('skillTier', 0),
                        won=i['attributes']['stats'].get('winner', False),
                        player_id=i['relationships']['player']['data']['id'],
                        match_id=ro2m[pa2r[i['id']]],
                        roster_id=pa2r[i['id']],
                    )
                    p.save()
                except Exception as e:
                    logger.debug(e)
                    continue
        # Matches =(many-to-many)=> Players
        for m in matches:
            for r in m.roster_set.all():
                for pa in r.participant_set.all():
                    m.players.add(pa.player)
        return

    def _request_without_region(self, ign, method):
        for r in SHARDS:
            res = method(r, ign)
            if res is not dict:
                break
            elif res.get('errors', ''):
                # もしエラーがあれば。
                continue
            else:
                break
        return res

    def single_player_without_region(self, ign):
        return self._request_without_region(ign, self.single_player)

    def matches_without_region(self, ign):
        return self._request_without_region(ign, self.matches)

    def player_matches_wo_region(self, ign):
        return self._request_without_region(ign, self.player_matches)


class MatchTelemetry:
    ''' Match Telemetry. Should be associated with a single Match object '''
    # https://vainglory-gamelocker-documentation.readthedocs.io/en/master/telemetry/telemetry.html

    def __init__(self, match):
        self.assets = None
        self.match = match

    # Public
    def daemon_process_match_obj(self):
        ''' Interface that runs daemon '''
        Thread(
            target=self.process_match_obj, daemon=True
        ).start()

    def process_match_obj(self):
        for participant in self.match.participant_set.all():
            self._participant_core_item_ids(participant.actor)

    def get_assets(self):
        if self.assets:
            return self.assets
        else:
            # Telemetry does not require api key
            headers = {
                'Accept': 'application/vnd.api+json',
                'Accept-Encoding': 'gzip',
            }
            self.assets = requests.get(
                self.match.telemetry_url, headers=headers).json()
            return self.assets

    # Private
    def _participant_buy_item(self, actor):
        timeline = []
        for a in self.get_assets():
            if a['type'] == 'BuyItem':
                if a['payload']['Actor'] == actor:
                    timeline.append([a['time'], a['payload']['Item']])
        return timeline

    def _participant_core_item_ids(self, actor):
        tl = self._participant_buy_item(actor)
        tier_3_item_ids_in_order = []
        for _, item_name in tl:
            tier = ih.item_tier.get(item_name, 0)
            if not tier:
                Item(name=item_name).save()
            if tier is 3:
                tier_3_item_ids_in_order.append(ih.item_t3id[item_name])
        return tier_3_item_ids_in_order


# ================
# Utilities
# ================
def cssreadable(name):
    return name.replace(' ', '-').replace("'", "").lower()


def particularplayer_from_singlematch(match, player_id):
    for r in match['rosters']:
        for p in r['participants']:
            if p['player_id'] == player_id:
                return p
