Vamos começar a aula 3 criando a tabela de cupons de desconto

```python
class CupomDesconto(models.Model):
    codigo = models.CharField(max_length=8, unique=True)
    desconto = models.FloatField()
    usos = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.codigo
```

E não se esqueçam de incluir o cupom em pedido

```python
cupom  = models.ForeignKey(CupomDesconto, null=True, blank=True, on_delete=models.CASCADE)
```

E agora vamos cadastrar essa tabela na área administrativa:

```python
@admin.register(CupomDesconto)
class CupomDescontoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'desconto', 'ativo')
    readonly_fields=('usos',)
```

Feito isso, quando o usuário clicar em finalizar compra em carrinho.html vamos redirecionar ele:

```python
<a href="{% url 'finalizar_pedido' %}" class="btn btn-success">Finalizar compra</a>
```

Precisamos então criar a respectiva URL

```python
from django.urls import path
from . import views

urlpatterns = [
    path("finalizar_pedido/", views.finalizar_pedido, name='finalizar_pedido'),
    path("validaCupom/", views.validaCupom, name='validaCupom'),

]
```

Criaremos então e view:

```python
from django.db.models.fields import CommaSeparatedIntegerField
from django.shortcuts import redirect, render
from django.http import HttpResponse
from .models import Pedido, ItemPedido, CupomDesconto
from produto.models import Produto, Categoria

def finalizar_pedido(request, room_name='pedir'):
    if request.method == "GET":
        categorias = Categoria.objects.all()
        erro = request.GET.get('erro')
        total = sum([float(i['preco']) for i in request.session['carrinho']])
        return render(request, 'finalizar_pedido.html', {'carrinho': len(request.session['carrinho']),
                                                        'categorias': categorias,
                                                        'total': total,
                                                        'erro': erro})
    else:
        if len(request.session['carrinho']) > 0:
            x = request.POST
            total = sum([float(i['preco']) for i in request.session['carrinho']])
            cupom = CupomDesconto.objects.filter(codigo=x['cupom'])
            cupom_salvar = None
            if len(cupom) > 0 and cupom[0].ativo:
                total = total - ((total*cupom[0].desconto)/100)
                cupom[0].usos += 1
                cupom[0].save()
                cupom_salvar = cupom[0]

            carrinho = request.session.get('carrinho')
            listaCarrinho = []
            for i in carrinho:
                listaCarrinho.append({
                    'produto': Produto.objects.filter(id = i['id_produto'])[0],
                    'observacoes': i['observacoes'],
                    'preco': i['preco'],
                    'adicionais': i['adicionais'],
                    'quantidade': i['quantidade'],
                })
            

            lambda_func_troco = lambda x: int(x['troco_para'])-total if not x['troco_para'] == '' else ""
            lambda_func_pagamento = lambda x: 'Cartão' if x['meio_pagamento'] == '2' else 'Dinheiro'
            pedido = Pedido(usuario=x['nome'],
                            total = total,
                            troco = lambda_func_troco(x),
                            cupom = cupom_salvar,
                            pagamento = lambda_func_pagamento(x),
                            ponto_referencia = x['pt_referencia'],
                            cep = x['cep'],
                            rua = x['rua'],
                            numero = x['numero'],
                            bairro = x['bairro'],
                            telefone = x['telefone'],
                            )
            pedido.save()
            
            ItemPedido.objects.bulk_create(
                ItemPedido(
                    pedido = pedido,
                    produto = v['produto'],
                    quantidade = v['quantidade'],
                    preco = v['preco'],
                    adicionais = str(v['adicionais'])
                ) for v in listaCarrinho

            )
        
            request.session['carrinho'].clear()
            request.session.save()
            return render(request, 'pedido_realizado.html')
        else:
            return redirect('/pedidos/finalizar_pedido?erro=1')
```

Agora vamos criar o finalizar_pedido.html:

```python
{% extends 'base.html'%}

{% block 'head' %}
<script src="https://code.jquery.com/jquery-3.4.1.js"></script>

<script>$(document).ready(function() {

    function limpa_formulário_cep() {
        // Limpa valores do formulário de cep.
        $("#rua").val("");
        $("#bairro").val("");
    }
    
    //Quando o campo cep perde o foco.
    $("#cep").blur(function() {
        //Nova variável "cep" somente com dígitos.
        var cep = $(this).val().replace(/\D/g, '');

        //Verifica se campo cep possui valor informado.
        if (cep != "") {

            //Expressão regular para validar o CEP.
            var validacep = /^[0-9]{8}$/;

            //Valida o formato do CEP.
            if(validacep.test(cep)) {

                //Preenche os campos com "..." enquanto consulta webservice.
                $("#rua").val("...");
                $("#bairro").val("...");
                

                //Consulta o webservice viacep.com.br/
                $.getJSON("https://viacep.com.br/ws/"+ cep +"/json/?callback=?", function(dados) {
                
                    if (!("erro" in dados)) {
                        //Atualiza os campos com os valores da consulta.
                        $("#rua").val(dados.logradouro);
                        $("#bairro").val(dados.bairro);
                   
                    } //end if.
                    else {
                        //CEP pesquisado não foi encontrado.
                        limpa_formulário_cep();
                        alert("CEP não encontrado.");
                    }
                });
            } //end if.
            else {
                //cep é inválido.
                limpa_formulário_cep();
                alert("Formato de CEP inválido.");
            }
        } //end if.
        else {
            //cep sem valor, limpa formulário.
            limpa_formulário_cep();
        }
    });
});

</script>

{%endblock%}

{%block 'conteudo'%}
<div class="container">

  <br>
  <h1 class="rosa">Ao clicar em "Efetuar pedido" será confirmado sua compra</h1>
  <hr>
  {%if erro == '1'%}
    <div class="alert alert-danger" role="alert">
        Escolha ao menos um produto antes de efetuar a compra!
    </div>
  
  {%endif%}

    <div class="row">

        <div class="col-sm fundo">

        <form method="post" action="{% url 'finalizar_pedido' %}">{% csrf_token %}

          <br>
          <h3 class="rosa">Nome*:</h3>
          <input type="text" required="required" class="form-control" placeholder="Nome" name="nome">

          <br>
          <h3 class="rosa">Cep:</h3>
          <input type="text" class="form-control" id="cep" placeholder="CEP" name="cep">

          <br>
          <h3 class="rosa">Cidade*:</h3>
          <select class="form-control">
            <option selected>Santa rita do passa quatro</option>
          </select>

          <br>
          <h3 class="rosa">Rua*:</h3>
          <input type="text" required="required" class="form-control" placeholder="Rua" id="rua" name="rua">

          <br>
          <h3 class="rosa">Número*:</h3>
          <input type="text" required="required" class="form-control" placeholder="Número" name="numero">

          <br>
          <h3 class="rosa">Bairro*:</h3>
          <input type="text" required="required" class="form-control" placeholder="Bairro" id="bairro" name="bairro">

          <br>
          <h3 class="rosa">Ponto de referência:</h3>
          <input type="text" class="form-control" placeholder="Ponto de referência" name="pt_referencia">

          <br>
          <h3 class="rosa">Telefone*:</h3>
          <input type="text" required="required" class="form-control" placeholder="Telefone" name="telefone">
          <br>

     
          
    </div>

  </div>
  <div class="row">
    <div class="col-sm fundo">

    </div>

    <div class="col-sm fundo">
        <div class="btn btn-info btn-lg" onclick="pagar_entrega()">Pagar na entrega</div>
    </div>

</div>
<hr>
<br>

<div class="row">
    <div class="col-sm fundo">
        <h1 id="total">Total: R${{total}}0</h1>
    </div>

    <div class="col-sm fundo">
        <input id="inputCupom" class="form-control" type="text" name="cupom" placeholder="Cupom de desconto">
        <p id="msg"></p>
        <br>
        <div id="btnCupom" class="btn btn-secondary" onclick="validaCupom()">Validar cupom</div>
    </div>

</div>
<br>
<br>

<div id="pagamento">
    
    <h3 class="rosa">Meio de pagamento*:</h3>
    <select name="meio_pagamento" class="form-control" onchange="javascript:dinheiro(this);">
      <option value="1">Dinheiro</option>
      <option value="2">Cartão</option>
    </select>

    <div id="troco">
        <h3 class="rosa">troco para*:</h3>
        <input type="text" class="form-control" placeholder="Número" name="troco_para">
    </div>
    <br>
    <button onclick="envia()" class="btn btn-success btn-lg">Efetuar pedido!</button>

</div>

<div style="display: none;" id="pagamaneto_online">
teste

</div>
</form>

</div>

<script>
function validaCupom(){
   cupom = document.getElementById('inputCupom').value
   $.ajax({
            url: "{% url 'validaCupom'%}",
            method: 'post',
            data: {
                'csrfmiddlewaretoken': '{{ csrf_token }}',
                'cupom': cupom
            },
            success: function(resposta){
              resposta = JSON.parse(resposta)
              div_total = document.getElementById('total')
              msg = document.getElementById('msg')
              if(resposta['status'] == 1){
                div_total.innerHTML = 'Total: R${{total}}0'
                msg.innerHTML = "Cupom inválido"
                msg.style.color = 'red'
              }else{
                div_total.innerHTML = 'De: <s>R${{total}}0</s> Por R$' + resposta['total_com_desconto'] + '0'
                msg.innerHTML = resposta['desconto'] + "% aplicado com sucesso"
                msg.style.color = 'green'
              }
                

            }

        })
}
</script>

{%endblock%}
```

Ainda precisamos criar a view para validar o cupom:

```python
def validaCupom(request):
    cupom = request.POST.get('cupom')
    cupom = CupomDesconto.objects.filter(codigo = cupom)
    if len(cupom) > 0 and cupom[0].ativo:
        desconto = cupom[0].desconto
        total = sum([float(i['preco']) for i in request.session['carrinho']])
        total_com_desconto = total - ((total*desconto)/100)
        data_json = json.dumps({'status': 0,
                                'desconto': desconto,
                                'total_com_desconto': str(total_com_desconto).replace('.', ',')

                                })
        return HttpResponse(data_json)
    else:
        return HttpResponse(json.dumps({'status': 1}))
```

E agora precisamos criar a página de pedido realizado:

```python
{% extends 'base.html'%}

{% block 'conteudo' %}
<div class="alert alert-success" role="alert">
    Seu pedido foi realizado com sucesso
  </div>
{%endblock%}
```