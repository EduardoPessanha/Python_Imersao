from django.db import models
from django.db.models.fields import CharField, FloatField, IntegerField

# Create your models here.
# Tudo que se referir a bancos de dados deverá ser construído dentro deste arquivo: models.py

# Criando as tabelas do banco de dados:

class Teste(models.Model):
    nome = models.CharField(max_length=50)
    idade = models.IntegerField()
    salario = models.FloatField()
