from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import random
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Chave para sessão

# Configurações do admin
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # Mude para uma senha mais segura!
VALOR_MINIMO_APOSTA = 5.0  # Valor mínimo da aposta
REDUCAO_CHANCE_POR_5_REAIS = 1  # Redução de chance a cada R$ 5,00 acima do mínimo

# Lista dos animais
animais = {
    1: 'Avestruz', 2: 'Águia', 3: 'Burro', 4: 'Borboleta', 5: 'Cachorro',
    6: 'Cabra', 7: 'Carneiro', 8: 'Camelo', 9: 'Cobra', 10: 'Coelho',
    11: 'Cavalo', 12: 'Elefante', 13: 'Galo', 14: 'Gato', 15: 'Jacaré',
    16: 'Leão', 17: 'Macaco', 18: 'Porco', 19: 'Pavão', 20: 'Peru',
    21: 'Touro', 22: 'Tigre', 23: 'Urso', 24: 'Veado', 25: 'Vaca'
}

# Banco de dados em memória
dados_banca = {
    'apostado': 0,
    'pago': 0,
    'lucro': 0,
    'chance_vitoria': 10,
    'ranking': []
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html', animais=animais)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return 'Login inválido'
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html', dados_banca=dados_banca)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/apostar', methods=['POST'])
def apostar():
    numero = int(request.form['animal'])
    valor = float(request.form['valor'])

    # Verifica se o valor da aposta é válido
    if valor < VALOR_MINIMO_APOSTA:
        return jsonify({
            'erro': f'O valor mínimo da aposta é R$ {VALOR_MINIMO_APOSTA:.2f}'
        }), 400

    dados_banca['apostado'] += valor

    # Calcula a chance de vitória baseada no valor da aposta
    valor_acima_minimo = valor - VALOR_MINIMO_APOSTA
    reducao_chance = int(valor_acima_minimo / 5) * REDUCAO_CHANCE_POR_5_REAIS
    chance_atual = max(1, dados_banca['chance_vitoria'] - reducao_chance)

    if random.randint(1, 100) <= chance_atual:
        sorteado = numero
    else:
        opcoes = [n for n in animais.keys() if n != numero]
        sorteado = random.choice(opcoes)

    nome_sorteado = animais[sorteado]

    if sorteado == numero:
        ganho = valor * 20
        dados_banca['pago'] += ganho
        resultado = f"🎉 Você ganhou R${ganho:.2f}! (Chance: {chance_atual}%)"
    else:
        resultado = f"😞 Você perdeu. (Chance: {chance_atual}%)"

    dados_banca['lucro'] = dados_banca['apostado'] - dados_banca['pago']

    dados_banca['ranking'].insert(0, f"{sorteado:02d} - {nome_sorteado}")
    if len(dados_banca['ranking']) > 10:
        dados_banca['ranking'].pop()

    return jsonify({
        'resultado': resultado,
        'animal': nome_sorteado,
        'numero': sorteado,
        'apostado': dados_banca['apostado'],
        'pago': dados_banca['pago'],
        'lucro': dados_banca['lucro'],
        'ranking': dados_banca['ranking'],
        'chance_atual': chance_atual
    })

@app.route('/configurar', methods=['POST'])
@login_required
def configurar():
    nova_chance = int(request.form['chance'])
    dados_banca['chance_vitoria'] = nova_chance
    return jsonify({'status': 'Chance atualizada'})

@app.route('/zerar', methods=['POST'])
@login_required
def zerar():
    dados_banca['apostado'] = 0
    dados_banca['pago'] = 0
    dados_banca['lucro'] = 0
    dados_banca['ranking'] = []
    return jsonify({'status': 'Banca zerada'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

