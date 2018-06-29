from django.shortcuts import render


def topView(request):
    return render(request, 'listter/top.html')
