from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def home(request):
    # return HttpResponse('Olá')
    return render(request, 'home.html', {'nome': 'Eduardo'})    #estamos renderizando uma página HTML
