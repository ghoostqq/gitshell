import os

import oauth2 as oauth
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response

from listter.models import Profile


@login_required
def listsView(request):
    return render(request, 'listter/lists.html')
