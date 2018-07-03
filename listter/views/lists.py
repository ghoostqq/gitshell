import json
import os

import oauth2 as oauth
import pandas as pd
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render, render_to_response

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
    'GET lists/members': 'https://api.twitter.com/1.1/lists/members.json',
    'POST lists/members/create': 'https://api.twitter.com/1.1/lists/members/create.json',
    'POST lists/members/create_all': '',
    'POST lists/members/destroy': 'https://api.twitter.com/1.1/lists/members/destroy.json',
    'POST lists/members/destroy_all': '',
    'POST lists/update': '',
    # Follows
    'GET friends/ids': 'https://api.twitter.com/1.1/friends/ids.json',
    # Users
    'GET users/lookup': 'https://api.twitter.com/1.1/users/lookup.json',
}


@login_required(login_url='top')
def listsView(request):
    token = oauth.Token(
        request.user.profile.oauth_token,
        request.user.profile.oauth_secret,
    )
    # token.set_verifier(request.GET['oauth_verifier'])
    client = oauth.Client(consumer, token)

    # GET lists/list
    resp, content = client.request(resource_urls['GET lists/list'], "GET")
    if resp['status'] != '200':
        print(content)
        raise Exception("Invalid response from Twitter.")
    if content.__class__ is bytes:
        content = content.decode('ascii')
    lists = json.loads(content)
    if settings.DEBUG:
        with open('./example_lists.json', 'w') as f:
            json.dump(lists, f, indent=4)

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

    LIST_ID = lists[0]['id']
    lists_members_url = resource_urls['GET lists/members'] + \
        '?list_id=' + str(LIST_ID)
    resp, content = client.request(lists_members_url, "GET")
    if resp['status'] != '200':
        print(content)
        raise Exception("Invalid response from Twitter.")
    if content.__class__ is bytes:
        content = content.decode('ascii')
    lists_members = json.loads(content)
    if settings.DEBUG:
        with open('./example_lists_members.json', 'w') as f:
            json.dump(lists_members, f, indent=4)

    friends_ids = [fid for fid in friends['ids']]
    lists_members_ids = [usr['id'] for usr in lists_members['users']]
    df = pd.DataFrame(index=friends_ids)
    df[str(LIST_ID)] = df.index.map(lambda x: x in lists_members_ids)

    return render(request, 'listter/lists.html', {
        'lists': lists, 'friends': friends, 'rich_friends': rich_friends, 'lists_members': lists_members, 'df': df.to_json(orient='index')})


def post_lists(request):
    if request.method == 'POST':
        return redirect('post_lists')
    else:
        return render(request, 'listter/post_lists.html', {'request': request})


def post_member(request):
    user_id, list_id, v = request.POST['user_id'], request.POST['list_id'], request.POST['v']
    token = oauth.Token(
        request.user.profile.oauth_token,
        request.user.profile.oauth_secret,
    )
    # token.set_verifier(request.GET['oauth_verifier'])
    client = oauth.Client(consumer, token)

    lists_members_url = resource_urls['POST lists/members/create' if v else 'POST lists/members/destroy'] + \
        f'?user_id={user_id}&list_id={list_id}'
    resp, content = client.request(lists_members_url, "POST")
    if resp['status'] != '200':
        print(content)
        raise Exception("Invalid response from Twitter.")
    if content.__class__ is bytes:
        content = content.decode('ascii')
    lists_members = json.loads(content)
    if settings.DEBUG:
        with open('./example_lists_members.json', 'w') as f:
            json.dump(lists_members, f, indent=4)

    return render(request, 'listter/post_lists.html')
