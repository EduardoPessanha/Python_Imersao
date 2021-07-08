from django.urls import path
from . import views         # o ponto sempre referencia para a própia pasta

urlpatterns = [
    path("", views.home, name='home'),
]