from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import redis
import base64
import json
from datetime import datetime, timedelta
from os.path import join

# Iniciando a aplicação Flask
app = Flask(__name__)
app.secret_key = 'Sua Senha Aqui'

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
    message_login = request.args.get('message_login')

    return render_template('index.html', product_list=products, message=message, message_promo=message_promo, message_delete=message_delete, message_login=message_login)

@app.route('/static/<path:filename>')
def static_files(filename):
    response = send_from_directory('static', filename)
    response.cache_control.max_age = timedelta(days=1)
    return response

@app.route('/account')
def account():
    message_user_register = request.args.get('message_user_register')
    message_user_login = request.args.get('message_user_login')
    

    if 'username' in session.keys():
        user_logged_in = update_user_session()
        if not user_logged_in:
            logout_user()
            user_logged_in = False
        else:
            discounts = get_all_discounts()
            products_ = []
            for product_name in user_logged_in['carrinho_compra']:
                products_.append(get_single_product(product_name))
                for discount in discounts:
                    if discount['nome'] == products_[-1]['nome']:
                        products_[-1]['desconto'] = discount['desconto']
                        products_[-1]['valor_desconto'] = round(float(products_[-1]['valor']) * (1 - float(discount['desconto']) / 100), 2)
                        products_[-1]['tempo_expiracao'] = discount['tempo_expiracao']
            user_logged_in['carrinho_compra'] = products_
    else:
        user_logged_in = False
    
    return render_template('account.html', message_user_register=message_user_register, message_user_login=message_user_login, user_logged_in=user_logged_in)

def create_product(nome, valor, quantidade, imagem):
    if request.method == 'POST':
        if imagem:
            imagem_data = imagem.read()
            imagem_base64 = base64.b64encode(imagem_data).decode('utf-8')

        else:
            pattern_path = join(app.static_folder, 'images/logo_.png')
            with open(pattern_path, 'rb') as img_file:
                imagem_data = img_file.read()
                imagem_base64 = base64.b64encode(imagem_data).decode('utf-8')

        produto = {
            'nome': nome,
            'valor': valor,
            'quantidade': quantidade,
            'imagem': imagem_base64,
            'desconto': 0.0,
            'valor_desconto': 0.0
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

def get_single_product(product_name):
    return redis_cnn.hgetall(f'produto:{product_name}')

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

def get_single_discount(product_name):
    return redis_cnn.hget(f'promocao:{product_name}', 'desconto')

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

    valor_produto = redis_cnn.hget(f'produto:{nome}', 'valor')

    if tempo_expiracao > 0:
        promocao = {
            'desconto': desconto,
            'valor_desconto':  round(float(valor_produto) * (1 - float(desconto) / 100), 2),
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
def handle_create_user():
    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']
    message = create_user(nome, email, senha)
    return redirect(url_for('account', message_user_register=message))

def create_user(nome, email, senha):
    if request.method == 'POST':
        # Verifica se o usuário já existe
        if redis_cnn.exists(f'usuario:{email}'):
            return 'failure'
        else:
            cliente = {
                'nome': nome,
                'email': email,
                'senha': senha,
                'carrinho_compra': json.dumps([]),
                'historico_pedidos': json.dumps({})
            }
            redis_cnn.hset(f'usuario:{email}', mapping=cliente) # A chave será composta por email
            return 'success'
# Exemplo de uso:
#create_user('James', 'email@email.com', '123123Salada')

@app.route('/login', methods=['POST'])
def handle_login_user():
    email = request.form['email']
    senha = request.form['senha']
    message = login_user(email, senha)
    return redirect(url_for('account', message_user_login=message))

def login_user(email, senha):
    if request.method == 'POST':
        # Verifica a existencia do email
        if redis_cnn.exists(f'usuario:{email}'):
            usuario = redis_cnn.hgetall(f'usuario:{email}')
            if senha == usuario['senha']:
                # Inicia a sessão do usuario
                session['username'] = {'email':usuario['email']}
                return 'success'
            else:
                return 'failure'
        else:
            return 'failure'

def update_user_session():
    if 'username' in session.keys():
        usuario = redis_cnn.hgetall(f'usuario:{session["username"]["email"]}')
        if usuario:
            carrinho_ = json.loads(redis_cnn.hget(f'usuario:{session["username"]["email"]}', 'carrinho_compra'))
            historico_ = json.loads(redis_cnn.hget(f'usuario:{session["username"]["email"]}', 'historico_pedidos'))
            usuario['carrinho_compra'] = carrinho_
            usuario['historico_pedidos'] = historico_
        return usuario

@app.route('/logout', methods=['POST'])
def logout_user():
    session.pop('username', None)
    return redirect(url_for('account'))

def update_product(nome, valor_incr_decr):
    redis_cnn.hincrby(f'produto:{nome}', 'quantidade', valor_incr_decr) # Função incrementa ou decrementa valores

@app.route('/delete_product/<product_name>', methods=['POST'])
def delete_product(product_name):
    redis_cnn.delete(f'produto:{product_name}')
    message = f'Produto {product_name} excluído com sucesso!'
    return redirect(url_for('index', message_delete=message))

@app.route('/remove_cart/<product_name>', methods=['POST'])
def remove_product_cart(product_name):
    user_id = session['username']
    carrinho_ = json.loads(redis_cnn.hget(f'usuario:{user_id["email"]}', 'carrinho_compra'))
    carrinho_.remove(product_name)
    redis_cnn.hset(f'usuario:{user_id["email"]}', 'carrinho_compra', json.dumps(carrinho_))
    return redirect(url_for('account'))

@app.route('/add_to_cart/?<product_name>', methods=['POST'])
def add_to_cart(product_name):
    # Verifica se há usuário logado, então atualiza o carrinho
    if 'username' in session.keys():
        user = session['username']
        cart_shop = json.loads(redis_cnn.hget(f'usuario:{user["email"]}', 'carrinho_compra'))
        cart_shop.append(product_name)
        redis_cnn.hset(f'usuario:{user["email"]}', 'carrinho_compra', json.dumps(cart_shop))
        return redirect(url_for('index', message_login='success'))
    else:
        return redirect(url_for('index', message_login='failure'))

@app.route('/checkout', methods=['POST'])
def purchase_complete():
    user_id = session['username']
    # Precisamos passar os items que estão no carrinho de compra para o histórico de pedidos
    data_compra = datetime.today().strftime("%d/%m/%Y")
    carrinho_compra = json.loads(redis_cnn.hget(f'usuario:{user_id["email"]}', 'carrinho_compra'))
    historico_pedidos = json.loads(redis_cnn.hget(f'usuario:{user_id["email"]}', 'historico_pedidos'))
    
    if not historico_pedidos:
        historico_pedidos = {}

    if data_compra not in historico_pedidos.keys():
        historico_pedidos[data_compra] = []
    
    # Agora iremos adicionar os produtos que estão no carrinho, nesta chave criada no historico
    for product_name in carrinho_compra:
        product = get_single_product(product_name)
        product['desconto'] = get_single_discount(product_name)
        if product['desconto']:
            product['valor_desconto'] = round(float(product['valor']) * (1 - float(product['desconto']) / 100), 2)
        historico_pedidos[data_compra].append(product)

    carrinho_compra = []
    
    # atualiza as informacoes do usuario
    redis_cnn.hset(f'usuario:{user_id["email"]}', 'carrinho_compra', json.dumps(carrinho_compra))
    redis_cnn.hset(f'usuario:{user_id["email"]}', 'historico_pedidos', json.dumps(historico_pedidos))
    return redirect(url_for('account'))

@app.route('/queries', methods=['POST', 'GET'])
def queries():
    resultado = None

    if request.method == 'POST':
        consulta = request.form.get('consulta')

        if consulta == '1':
            resultado = redis_cnn.keys('usuario:*')

        elif consulta == '2':
            email = request.form.get('email')
            resultado = redis_cnn.hmget(f'usuario:{email}', 'nome', 'email')

        elif consulta == '3':
            email = request.form.get('email')
            carrinho = json.loads(redis_cnn.hget(f'usuario:{email}', 'carrinho_compra'))
            produtos_carrinho = [get_single_product(produto) for produto in carrinho]
            resultado = produtos_carrinho if carrinho else 'Carrinho vazio'

        elif consulta == '4':
            email = request.form.get('email')
            carrinho = json.loads(redis_cnn.hget(f'usuario:{email}', 'carrinho_compra'))
            produtos_carrinho = [get_single_product(produto) for produto in carrinho]
            print(produtos_carrinho)
            resultado = sum(float(produto['valor']) if not (float(produto['desconto']) > 0) else float(produto['valor_desconto']) for produto in produtos_carrinho)

        elif consulta == '5':
            produto_nome = request.form.get('produto_nome')
            quantidade = request.form.get('quantidade')
            redis_cnn.hset(f'produto:{produto_nome}', 'quantidade', quantidade)
            resultado = f'Quantidade do produto {produto_nome} atualizada para {quantidade}.'

        elif consulta == '6':
            resultado = [key for key in redis_cnn.keys('promocao:*') if redis_cnn.ttl(key) > 0]

        elif consulta == '7':
            email = request.form.get('email')
            data = request.form.get('data')
            historico = json.loads(redis_cnn.hget(f'usuario:{email}', 'historico_pedidos'))
            resultado = historico.get(data, [])
            
        elif consulta == '8':
            produto_nome = request.form.get('produto_nome')
            desconto = request.form.get('desconto')
            expiracao = request.form.get('expiracao')
            create_discount(expiracao, desconto, produto_nome)
            valor_com_desconto = redis_cnn.hget(f'promocao:{produto_nome}', 'valor_desconto')
            resultado = f'Desconto aplicado. Novo valor do produto {produto_nome}: {valor_com_desconto}'

        elif consulta == '9':
            email = request.form.get('email')
            produto_nome = request.form.get('produto_nome')
            carrinho = json.loads(redis_cnn.hget(f'usuario:{email}', 'carrinho_compra'))
            carrinho = [produto for produto in carrinho if produto['nome'] != produto_nome]
            redis_cnn.hset(f'usuario:{email}', 'carrinho_compra', json.dumps(carrinho))
            resultado = f'Produto {produto_nome} removido do carrinho de {email}.'

        elif consulta == '10':
            produto_nome = request.form.get('produto_nome')
            usuarios = redis_cnn.keys('usuario:*')
            usuarios_com_produto = []
            for usuario in usuarios:
                carrinho = json.loads(redis_cnn.hget(usuario, 'carrinho_compra'))
                if any(produto == produto_nome for produto in carrinho):
                    usuarios_com_produto.append(usuario)
            print("ate aqui foi")
            resultado = usuarios_com_produto if usuarios_com_produto else f"Não há usuários com o produto {produto_nome} no carrinho."

        # Converta o resultado para string se necessário
        resultado = str(resultado)
    products = get_all_products()

    return render_template('queries.html', resultado=resultado, product_list=products)

    None
if __name__ == '__main__':
    app.run(debug=True)