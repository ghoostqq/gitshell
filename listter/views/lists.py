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


def client_request(client, url, method, example_file_name):
    resp, content = client.request(url, method)
    if resp['status'] != '200':
        print(content)
        raise Exception("Invalid response from Twitter.")
    if content.__class__ is bytes:
        content = content.decode('ascii')
    result = json.loads(content)
    if settings.DEBUG:
        with open(example_file_name, 'w') as f:
            json.dump(result, f, indent=4)
    return result


@login_required(login_url='top')
def listsView(request):
    token = oauth.Token(
        request.user.profile.oauth_token,
        request.user.profile.oauth_secret,
    )
    # token.set_verifier(request.GET['oauth_verifier'])
    client = oauth.Client(consumer, token)

    # GET lists/list
    lists = client_request(client, resource_urls['GET lists/list'], "GET",
                           './example_lists.json')
    lists = [lst for lst in lists
             if lst['user']['id_str'] == request.user.username]

    friends = client_request(client, resource_urls['GET friends/ids'], "GET",
                             './example_friends_ids.json')

    users_lookup_url = resource_urls['GET users/lookup'] + \
        '?user_id=' + ','.join(map(str, friends['ids'][:2]))
    rich_friends = client_request(client, users_lookup_url, "GET",
                                  './example_rich_friends.json')

    LIST_ID = lists[0]['id']
    lists_members_url = resource_urls['GET lists/members'] + \
        '?list_id=' + str(LIST_ID)
    lists_members = client_request(client, lists_members_url, "GET",
                                   './example_list_members.json')

    friends_ids = [fid for fid in friends['ids']]
    df = pd.DataFrame(index=friends_ids)
    lists_members_ids = [usr['id'] for usr in lists_members['users']]
    df[str(LIST_ID)] = df.index.map(lambda x: x in lists_members_ids)

    return render(request, 'listter/lists.html', {
        'lists': lists, 'friends': friends, 'rich_friends': rich_friends, 'lists_members': lists_members, 'df': df.to_json(orient='index'), })


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
    base_url = ('https://api.twitter.com/1.1/lists/members/create.json',
                'https://api.twitter.com/1.1/lists/members/destroy.json')[int(v)]

    lists_members_url = base_url + \
        f'?user_id={user_id}&list_id={list_id}'
    if settings.DEBUG:
        print(v, '->', lists_members_url)
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

    return render(request, 'listter/lists.html')
