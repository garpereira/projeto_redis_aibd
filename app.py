from flask import Flask, render_template, request, redirect, url_for
import redis
import base64
from datetime import datetime

# Iniciando a aplicação Flask
app = Flask(__name__)

# Iniciando a conexão com o Redis
redis_cnn = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

@app.route('/')
def index():

    # Recuperar todos os produtos
    products = get_all_products()
    discounts = get_all_discounts()

    for product in products:
        for discount in discounts:
            if product['nome'] == discount['nome']:
                product['desconto'] = discount['desconto']
                product['valor_desconto'] = round(float(product['valor']) * (1 - float(discount['desconto']) / 100), 2)
                product['tempo_expiracao'] = discount['tempo_expiracao']
    
    message = request.args.get('message')
    message_promo = request.args.get('message_promo')
    message_delete = request.args.get('message_delete')

    return render_template('index.html', product_list=products, message=message, message_promo=message_promo, message_delete=message_delete)

@app.route('/account')
def account():
    return render_template('account.html')

def create_product(nome, valor, quantidade, imagem):
    if request.method == 'POST':
        if imagem:
            imagem_data = imagem.read()
            imagem_base64 = base64.b64encode(imagem_data).decode('utf-8')

        else:
            imagem_base64 = ""

        produto = {
            'nome': nome,
            'valor': valor,
            'quantidade': quantidade,
            'imagem': imagem_base64
        }
        redis_cnn.hset(f'produto:{nome}', mapping=produto)  # O nome do produto será a chave do hash
# Exemplo de uso:
#create_product('Camiseta', 29.99, 100, 'camiseta.jpg')
#f'produto:{nome}': A chave do hash será formada pela palavra "produto:"

@app.route('/create_product', methods=['POST'])
def handle_create_product():
    nome = request.form['nome']
    valor = request.form['valor']
    quantidade = request.form['quantidade']
    imagem = request.files['imagem']
    create_product(nome, valor, quantidade, imagem)
    message = "Produto cadastrado com sucesso!"
    return redirect(url_for('index', message=message))

def get_product_names():
    # Usa SCAN para iterar sobre todas as chaves
    product_names = []
    cursor = '0'
    while cursor != 0:
        cursor, keys = redis_cnn.scan(cursor=cursor, match='produto:*')
        for key in keys:
            product_name = key.split(':', 1)[1]
            product_names.append(product_name)
    return product_names

def get_all_products():
    products = []
    cursor = '0'
    while cursor != 0:
        cursor, keys = redis_cnn.scan(cursor=cursor, match='produto:*')
        for key in keys:
            product_data = redis_cnn.hgetall(key)
            products.append(product_data)
    return products

def get_all_discounts():
    discounts = []
    cursor = '0'
    while cursor != 0:
        cursor, keys = redis_cnn.scan(cursor=cursor, match='promocao:*')
        for key in keys:
            discount_data = redis_cnn.hgetall(key)
            discount_data['tempo_expiracao'] = redis_cnn.ttl(key)
            discounts.append(discount_data)
    return discounts

@app.route('/create_discount', methods=['POST'])
def handle_create_discount():
    data_expiracao = request.form['data_expiracao']
    desconto = request.form['desconto']
    nome = request.form['produto']
    message = create_discount(data_expiracao, desconto, nome)
    return redirect(url_for('index', message_promo=message))

def create_discount(data_expiracao, desconto, nome):
    # Compara com a data atual para pegar o tempo de expiração em segundos:
    data_atual = datetime.now()
    data_expiracao = datetime.strptime(data_expiracao, '%Y-%m-%dT%H:%M')
    tempo_expiracao = int((data_expiracao - data_atual).total_seconds())

    if tempo_expiracao > 0:
        promocao = {
            'desconto': desconto,
            'nome': nome
        }
        redis_cnn.hset(f'promocao:{nome}', mapping=promocao)  # O nome será a chave do hash da promoção
        redis_cnn.expire(f'promocao:{nome}', tempo_expiracao)  # Define o tempo de expiração da promoção
        return "valido"
    else:
        return "invalido" # Se a data de expiração for menor que a data atual, a promoção não será criada

# Exemplo de uso:
#create_discount(1643673600, 10, 'Camiseta')  # Promoção expira em 01/02/2022 com 10% de desconto na camiseta

@app.route('/create_user', methods=['POST'])
def create_user(nome, sobrenome, senha):
    cliente = {
        'nome': nome,
        'sobrenome': sobrenome,
        'senha': senha
    }
    redis_cnn.hset(f'usuario:{nome}_{sobrenome}', mapping=cliente) # A chave será composta por nome e sobrenome para maior distinção
# Exemplo de uso:
#create_user('James', 'SaladadeFruta', '123123Salada')


def update_product(nome, nova_quantidade):
    redis_cnn.hincrby(f'produto:{nome}', 'quantidade', nova_quantidade) # Função incrementa ou decrementa valores

@app.route('/delete_product/<product_name>', methods=['POST'])
def delete_product(product_name):
    redis_cnn.delete(f'produto:{product_name}')
    message = f'Produto {product_name} excluído com sucesso!'
    return redirect(url_for('index', message_delete=message))

if __name__ == '__main__':
    app.run(debug=True)