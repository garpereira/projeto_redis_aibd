# Projeto Banco Redis
- 
## Shopipipipi

Shopipipipi é uma aplicação web simples desenvolvida com Flask e Redis. O objetivo é permitir o cadastro de produtos e promoções em uma loja fictícia. A aplicação inclui funcionalidades para criar produtos e promoções, bem como visualizar uma lista de produtos e promoções existentes.

### Tecnologias Utilizadas
- Flask: Um microframework para Python que facilita a criação de aplicações web.
- Redis: Um banco de dados em memória utilizado para armazenamento rápido de dados.
- Bootstrap: Framework CSS para estilização e design responsivo da interface.

### Estrutura do Projeto
#### app.py
Este é o arquivo principal da aplicação Flask. Ele contém todas as rotas e a lógica de backend necessária para a operação do site.

- Rota /: Página inicial que lista todos os produtos e permite o cadastro de novos produtos e promoções.
- Rota /account: Página "Minha Conta" (atualmente em branco).
Funções auxiliares:
- create_product: Cria um novo produto no banco de dados Redis.
- get_product_names: Retorna a lista de nomes de produtos cadastrados.
- create_discount: Cria uma nova promoção no banco de dados Redis.
- update_product: Atualiza a quantidade de um produto existente.
- create_user: Cria um novo usuário no banco de dados Redis.

#### Templates HTML
- base.html: Template base que define o layout padrão do site, incluindo cabeçalho, navegação e rodapé.
- index.html: Página inicial que estende o template base e inclui formulários para cadastro de produtos e promoções, além de mensagens de feedback ao usuário.

### Funcionalidades
- Cadastro de Produtos: Permite que o usuário cadastre novos produtos informando nome, valor, quantidade e imagem do produto.
- Cadastro de Promoções: Permite que o usuário cadastre novas promoções vinculadas a produtos existentes, definindo o tempo de expiração e o desconto.
- Exibição de Produtos e Promoções: Exibe os produtos e promoções cadastrados (área de visualização em desenvolvimento).

### Requisitos
- Python 3.x
- Flask
- Redis Server

### Instalação e Execução
1. Clone o repositório:

``` bash
    git clone https://github.com/seu-usuario/shopipipipi.git
    cd shopipipipi
```
2. Crie um ambiente virtual e ative-o:

```bash
    python -m venv venv
    source venv/bin/activate  # No Windows, use `venv\Scripts\activate`
```

3. Instale as dependências:

```bash
    pip install flask redis
```

4. Inicie o servidor Redis:

```bash
redis-server
```

5. Execute a aplicação:

```bash
python app.py
```

6. Acesse a aplicação no navegador:

Abra http://localhost:5000 em seu navegador para acessar a aplicação.

### Observações
- Certifique-se de que o servidor Redis está em execução na máquina local na porta 6379.
- Você pode ajustar a configuração do Redis conforme necessário no arquivo app.py.

### Licença
Este projeto está licenciado sob a licença MIT.