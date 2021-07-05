E aqui estamos nós para segunda aula, e hoje vamos trabalhar com o carrinho do cliente.

e o primeiro passo para isso é criar uma URL especifica para isso:

```python
path("add_carrinho", views.add_carrinho, name='add_carrinho'),
```

Com a URL pronto vamos redirecionar o form em produto.html para essa URL específica

```python
<form method="POST" action="{% url 'add_carrinho' %}">
```

feito isso precisamos criar a view add_carrinho chamada pela URL:

```python
def add_carrinho(request):
    if not request.session.get('carrinho'):
        request.session['carrinho'] = []
        request.session.save()

    x = dict(request.POST)

    def removeLixo(adicional):
        adicionais = x.copy()
        adicionais.pop('id')
        adicionais.pop('csrfmiddlewaretoken')
        adicionais.pop('observacoes')
        adicionais.pop('quantidade')
        adicionais = list(adicionais.items())

        return adicionais
        
    adicionais = removeLixo(x)    

    id = int(x['id'][0])
    preco_total = Produto.objects.filter(id=id)[0].preco
    adicionais_verifica =  Adicional.objects.filter(produto = id)
    aprovado = True

    for i in adicionais_verifica:
        encontrou = False
        minimo = i.minimo
        maximo = i.maximo
        for j in adicionais:
            if i.nome == j[0]:
                encontrou = True
                if len(j[1]) < minimo or len(j[1]) > maximo:
                    aprovado = False
        if minimo > 0 and encontrou == False:
            aprovado = False
    
    if not aprovado:
        return redirect(f'/produto/{id}?erro=1')

    for i, j in adicionais:
        for k in j:
            preco_total += Opcoes.objects.filter(id=int(k))[0].acrecimo
    
    def troca_id_por_nome_adicional(adicional):
        adicionais_com_nome = []
        for i in adicionais:
            opcoes = []
            for j in i[1]:
                op = Opcoes.objects.filter(id = int(j))[0].nome
                opcoes.append(op) 
            adicionais_com_nome.append((i[0], opcoes))
        return adicionais_com_nome
    
    adicionais = troca_id_por_nome_adicional(adicionais)
    
    preco_total *= int(x['quantidade'][0])
    data = {'id_produto': int(x['id'][0]),
            'observacoes': x['observacoes'][0],
            'preco': preco_total,
            'adicionais': adicionais,
            'quantidade': x['quantidade'][0]}

    request.session['carrinho'].append(data)
    request.session.save()
    #return HttpResponse(request.session['carrinho'])
    return redirect(f'/ver_carrinho')
```

Como podemos perceber o código acima redireciona para a URL ver_carrinho, por isso vamos cria-la.

```python
path("ver_carrinho", views.ver_carrinho, name='ver_carrinho'),
```

Criaremos agora a view ver_carrinho:

```python
def ver_carrinho(request):
    categorias = Categoria.objects.all()
    dados_motrar = []
    for i in request.session['carrinho']:
        prod = Produto.objects.filter(id=i['id_produto'])
        dados_motrar.append(
            {'imagem': prod[0].img.url,
             'nome': prod[0].nome_produto,
             'quantidade': i['quantidade'],
             'preco': i['preco'],
             'id': i['id_produto']
             }
        )
    total = sum([float(i['preco']) for i in request.session['carrinho']])

    return render(request, 'carrinho.html', {'dados': dados_motrar,
                                             'total': total,
                                             'carrinho': len(request.session['carrinho']),
                                             'categorias': categorias,
                                             })
```

Podemos observar que essa view renderiza um arquivo html chamado carrinho.html, vamos cria-lo:

```python
{%extends 'base.html'%}

{% block 'conteudo'%}
<br>
<br>
<div class="container">
<table class="table table-striped">
    <thead>
      <tr>
        <th>Imagem</th>
        <th>Produto</th>
        <th>QTD.</th>
        <th>Sub total</th>
        <th>Remover</th>
      </tr>
    </thead>
    <tbody>
    {% for i in dados%}
      <tr>
        <th><img src="{{i.imagem}}" width="50px"></th>
        <td>{{i.nome}}</td>
        <td>{{i.quantidade}}</td>
        <td>{{i.preco}}0</td>
        <td><a href="" class="btn btn-danger">Remover</a></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  <h3>Frete: R${{frete}}0</h3>
  <h1 class="titulo">Total: </h1>
  <h2 style="color: gray;">&nbsp R${{total}}0</h2>
  <a href="" class="btn btn-success">Finalizar compra</a>
  <a href="{% url 'home'%}" class="btn btn-primary">Continuar comprando</a>
</div>
{%endblock%}
```

Agora precisamos adicionar a funcionalidade de remover do carrinho e para isso vamos efetuar alguma alteraçoẽs no carrinho.html

```python
{% load filtros %}

{% for j, i in dados|enumerate%}

<a href="{% url 'remover_carrinho' j%}" class="btn btn-danger">Remover</a>
```

vamos criar a pasta templatestags e dentro dela o arquivo filtros.py:

```python
from django import template

register = template.Library()

@register.filter(name='enumerate')
def enumerat(valor):
    return enumerate(valor)
```

precisamos informar o django que criamos um novo filtro para isso vamos em setting.py:

```python
'libraries':{
            'filtros': 'produto.templatestags.filtros',

            }
```

Agora precisamos criar a URL remover_carrinho:

```python
path("remover_carrinho/<int:id>", views.remover_carrinho, name='remover_carrinho'),
```

E também a view remover_carrinho:

```python
def remover_carrinho(request, id):
    request.session['carrinho'].pop(id)
    request.session.save()
    return redirect('/ver_carrinho')
```

Agora estamos com o carrinho pronto, podemos partir então para finalização do pedido e para isso iremos criar um novo APP chamado pedido:

```python
python3 manage.py startapp pedido
```

(Lembre-se) de cadastrar o novo APP em settings.py

Agora vamos criar a tabela no banco de dados para armazenar os pedidos.

```python
from django.db import models
from datetime import datetime
from produto.models import Produto

class Pedido(models.Model):
    usuario = models.CharField(max_length=200)
    total = models.FloatField()
    troco = models.CharField(blank=True, max_length=20)
    pagamento = models.CharField(max_length=20)
    ponto_referencia = models.CharField(max_length=2000, blank=True)
    data = models.DateTimeField(default=datetime.now())
    cep = models.CharField(max_length=50, blank=True)
    rua = models.CharField(max_length=200)
    numero = models.CharField(max_length=10)
    bairro = models.CharField(max_length=200, blank=True)
    telefone = models.CharField(max_length=30)
    entregue = models.BooleanField(default=False)

    def __str__(self):
        return self.usuario

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    preco = models.FloatField()
    descricao = models.TextField()
    adicionais = models.TextField()
```

Vamos rodar os comandos para efetuar as alterações no banco de dados:

```python
python3 manage.py makemigrations

python3 manage.py migrate
```

Pronto, agora vamos registrar essas tabelas na área administrativa:

```python
from django.contrib import admin
from .models import ItemPedido, Pedido
from django.http import HttpResponse
# Register your models here.

class itemPedidoInline(admin.TabularInline):
    readonly_fields = ('produto', 'quantidade', 'preco', 'descricao', 'adicionais',)
    model = ItemPedido
    extra = 1

class PedidoAdmin(admin.ModelAdmin):
    inlines = [
        itemPedidoInline
    ]
    list_display = ('usuario', 'total', 'data', 'entregue')
    search_fields = ('entregue',)
    readonly_fields = ('usuario', 'total', 'troco', 'cupom', 'pagamento', 'ponto_referencia', 'data', 'cep', 'rua', 'numero', 'bairro', 'telefone')
    list_filter = ('entregue',)
admin.site.register(Pedido, PedidoAdmin)
```

E por aqui terminamos a segunda aula da Imersão Python, até a próxima.