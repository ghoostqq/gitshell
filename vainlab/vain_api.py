import json
import os

import requests

from .models import Match, Participant, Player, Roster

# from .models import Item, Match, Participant, Player, Roster

SHARDS = ['ea', 'na', 'sg', 'eu', 'sa', 'cn']


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
            # 'Accept-Encoding': 'gzip',
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

    def player_matches(self, reg, ign):
        url = f'https://api.dc01.gamelockerapp.com/shards/{reg}/matches'
        params = {
            'filter[playerNames]': [ign],
            'sort': '-createdAt',
        }
        res = self.request(url, params)

        # Exit if error
        if res.get('errors', ''):
            return res

        # ===============
        # Save to DB
        # ===============
        matches = list()
        ro2m = dict()
        # Match
        for i in res['data']:
            match = Match(
                id=i['id'],
                datetime=i['attributes']['createdAt'],
                mode=i['attributes']['gameMode'],
                version=i['attributes']['patchVersion'],
            )
            match.save()
            matches.append(match)
            for roster in i['relationships']['rosters']['data']:
                ro2m[roster['id']] = i['id']
        pa2r = dict()
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
                    elo=i['attributes']['stats']['rankPoints']['ranked'],
                    tier=i['attributes']['stats']['skillTier'],
                    wins=i['attributes']['stats']['wins'],
                )
                p.save()
        # Participant -> Roster, Player
        for i in res['included']:
            if i['type'] == 'participant':
                p = Participant(
                    id=i['id'],
                    # Assuming like '*Vox*' -> 'Vox'
                    actor=i['attributes']['actor'][1:-1],
                    shard=i['attributes']['shardId'],
                    kills=i['attributes']['stats']['kills'],
                    deaths=i['attributes']['stats']['deaths'],
                    assists=i['attributes']['stats']['assists'],
                    # kda
                    gold=i['attributes']['stats']['gold'],
                    farm=i['attributes']['stats']['farm'],
                    items=json.dumps(i['attributes']['stats']
                                     ['items'][::-1][:6][::-1]),
                    tier=i['attributes']['stats']['skillTier'],
                    won=i['attributes']['stats']['winner'],
                    player_id=i['relationships']['player']['data']['id'],
                    match_id=ro2m[pa2r[i['id']]],
                    roster_id=pa2r[i['id']],
                )
                p.save()
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
