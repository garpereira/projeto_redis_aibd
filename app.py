from flask import Flask, render_template
import redis

# Iniciando a aplicação Flask
app = Flask(__name__)

# Iniciando a conexão com o Redis
redis_cnn = redis.Redis(host="localhost", port=6379, db=0)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/account')
def account():
    return render_template('account.html')

if __name__ == '__main__':
    app.run(debug=True)