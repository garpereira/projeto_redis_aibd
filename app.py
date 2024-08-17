from flask import Flask, render_template, request, redirect, url_for
import redis

# Iniciando a aplicação Flask
app = Flask(__name__)

# Iniciando a conexão com o Redis
redis_cnn = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

@app.route('/')
def index():

    # Recuperar todos os produtos
    products = get_all_products()

    if not products:
        products = {'Nenhum produto cadastrado':''}
    
    message = request.args.get('message')
    message_promo = request.args.get('message_promo')

    return render_template('index.html', product_list=products, message=message, message_promo=message_promo)

@app.route('/account')
def account():
    return render_template('account.html')

def create_product(nome, valor, quantidade, imagem):
    if request.method == 'POST':
        produto = {
            'nome': nome,
            'valor': valor,
            'quantidade': quantidade,
            'imagem': imagem
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
    imagem = request.form['imagem']
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

@app.route('/create_discount', methods=['POST'])
def handle_create_discount():
    tempo_expiracao = request.form['tempo_expiracao']
    desconto = request.form['desconto']
    nome = request.form['produto']
    create_discount(tempo_expiracao, desconto, nome)
    message = "Promoção cadastrada com sucesso!"
    return redirect(url_for('index', message_promo=message))

def create_discount(tempo_expiracao, desconto, nome):
    promocao = {
        'tempo_expiracao': tempo_expiracao,
        'desconto': desconto,
        'nome': nome
    }
    redis_cnn.hset(f'promocao:{nome}', mapping=promocao)  # O nome será a chave do hash da promoção
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

if __name__ == '__main__':
    app.run(debug=True)