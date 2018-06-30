import json
import os

import oauth2 as oauth
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response

from listter.models import Profile

# It's probably a good idea to put your consumer's OAuth token and
# OAuth secret into your project's settings.
consumer = oauth.Consumer(
    os.environ.get('TWITTER_LISTTER_CONSUMER_KEY', ''),
    os.environ.get('TWITTER_LISTTER_CONSUMER_SECRET', ''),
)


# https://developer.twitter.com/en/docs/accounts-and-users/create-manage-lists/api-reference
resource_urls = {
    # Lists
    'GET lists/list': 'https://api.twitter.com/1.1/lists/list.json',
    'GET lists/members': '',
    'POST lists/members/create': '',
    'POST lists/members/create_all': '',
    'POST lists/members/destroy': '',
    'POST lists/members/destroy_all': '',
    'POST lists/update': '',
    # Follows
    'GET friends/ids': 'https://api.twitter.com/1.1/friends/ids.json',
    # Users
    'GET users/lookup': 'https://api.twitter.com/1.1/users/lookup.json',
}


@login_required(login_url='top')
def listsView(request):
    # GET lists/list
    token = oauth.Token(
        request.user.profile.oauth_token,
        request.user.profile.oauth_secret,
    )
    # token.set_verifier(request.GET['oauth_verifier'])
    client = oauth.Client(consumer, token)
    resp, content = client.request(resource_urls['GET lists/list'], "GET")
    if resp['status'] != '200':
        print(content)
        raise Exception("Invalid response from Twitter.")
    if content.__class__ is bytes:
        content = content.decode('ascii')
    lists = json.loads(content)

    resp, content = client.request(resource_urls['GET friends/ids'], "GET")
    if resp['status'] != '200':
        print(content)
        raise Exception("Invalid response from Twitter.")
    if content.__class__ is bytes:
        content = content.decode('ascii')
    friends = json.loads(content)

    users_lookup_url = resource_urls['GET users/lookup'] + \
        '?user_id=' + ','.join(map(str, friends['ids'][:2]))
    resp, content = client.request(users_lookup_url, "GET")
    if resp['status'] != '200':
        print(content)
        raise Exception("Invalid response from Twitter.")
    if content.__class__ is bytes:
        content = content.decode('ascii')
    rich_friends = json.loads(content)
    if settings.DEBUG:
        with open('./example_users_lookup.json', 'w') as f:
            json.dump(rich_friends, f, indent=4)

    return render(request, 'listter/lists.html', {'lists': lists, 'friends': friends, 'rich_friends': rich_friends})
