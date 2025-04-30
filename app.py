from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import random
import os
from functools import wraps
import hashlib
import time
from datetime import datetime, timedelta
from printer import ThermalPrinter

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Chave para sessão

# Configurações do admin
ADMIN_USERNAME = "admin"
# Senha: brasil2018 (hash SHA-256)
ADMIN_PASSWORD_HASH = "25a5aa52395e86d9645397dead15dec4a3c577a98d51f9f87323875506d14835"
VALOR_MINIMO_APOSTA = 5.0
REDUCAO_CHANCE_POR_5_REAIS = 5  # Redução por cada R$ 5,00 acima do mínimo
REDUCAO_ADICIONAL_ACIMA_MINIMO = 3  # Redução adicional progressiva
REDUCAO_MINIMA = 8  # Nova constante para garantir que R$ 5,00 tenha 2% de chance

# Configurações de segurança
MAX_LOGIN_ATTEMPTS = 3
LOGIN_TIMEOUT_MINUTES = 30
CSRF_TOKEN_TIMEOUT_MINUTES = 60

# Adicionar novas configurações
LIMITE_APOSTA_MAXIMO = 1000.0  # Limite máximo de aposta
MAX_APOSTAS_POR_MINUTO = 10    # Limite de apostas por minuto
TEMPO_SESSAO_ADMIN = 7200      # Tempo de sessão do admin em segundos (2 horas)

# Configuração da impressora
PRINTER_ADDRESS = "00:11:22:33:44:55"  # Substitua pelo endereço Bluetooth da sua impressora
printer = ThermalPrinter()

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

# Controle de segurança
login_attempts = {}
admin_logs = []

# Controle de apostas
controle_apostas = {}

# Inicializa a impressora
printer.connect(PRINTER_ADDRESS)

def generate_csrf_token():
    """Gera um token CSRF único"""
    token = hashlib.sha256(os.urandom(64)).hexdigest()
    session['csrf_token'] = token
    session['csrf_token_time'] = datetime.now().timestamp()
    return token

def validate_csrf_token(token):
    """Valida o token CSRF"""
    stored_token = session.get('csrf_token')
    token_time = session.get('csrf_token_time')
    
    if not stored_token or not token_time:
        return False
    
    # Verifica se o token expirou
    if datetime.now().timestamp() - token_time > CSRF_TOKEN_TIMEOUT_MINUTES * 60:
        return False
    
    return stored_token == token

def hash_password(password):
    """Cria hash da senha usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_login_attempts(ip):
    """Verifica tentativas de login"""
    now = datetime.now()
    
    # Limpa tentativas antigas
    for stored_ip in list(login_attempts.keys()):
        if now - login_attempts[stored_ip]['last_attempt'] > timedelta(minutes=LOGIN_TIMEOUT_MINUTES):
            del login_attempts[stored_ip]
    
    # Verifica tentativas do IP atual
    if ip in login_attempts:
        attempts = login_attempts[ip]
        if attempts['count'] >= MAX_LOGIN_ATTEMPTS:
            time_diff = now - attempts['last_attempt']
            if time_diff < timedelta(minutes=LOGIN_TIMEOUT_MINUTES):
                return False
            else:
                del login_attempts[ip]
    
    return True

def log_admin_action(action, ip, valor=None, chance_real=None):
    """Registra ações do admin com mais detalhes"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = {
        'timestamp': timestamp,
        'action': action,
        'ip': ip,
        'valor': valor,
        'chance_real': chance_real
    }
    
    admin_logs.append(log_entry)
    if len(admin_logs) > 1000:  # Aumentar limite de logs
        admin_logs.pop(0)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        
        # Verifica se a sessão expirou (2 horas)
        if 'login_time' in session:
            if time.time() - session['login_time'] > 7200:  # 2 horas
                session.clear()
                return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def limitar_apostas(ip):
    """Limita o número de apostas por IP"""
    agora = datetime.now()
    if ip not in controle_apostas:
        controle_apostas[ip] = []
    
    # Remove apostas antigas (mais de 1 minuto)
    controle_apostas[ip] = [
        tempo for tempo in controle_apostas[ip]
        if (agora - tempo).total_seconds() < 60
    ]
    
    # Verifica se excedeu o limite
    if len(controle_apostas[ip]) >= MAX_APOSTAS_POR_MINUTO:
        return False
    
    # Adiciona nova aposta
    controle_apostas[ip].append(agora)
    return True

@app.route('/')
def home():
    return render_template('index.html', animais=animais)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ip = request.remote_addr
        
        if not check_login_attempts(ip):
            return render_template('login.html', error=f'Muitas tentativas. Tente novamente em {LOGIN_TIMEOUT_MINUTES} minutos.')
        
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Registra tentativa
        if ip not in login_attempts:
            login_attempts[ip] = {'count': 0, 'last_attempt': datetime.now()}
        login_attempts[ip]['count'] += 1
        login_attempts[ip]['last_attempt'] = datetime.now()
        
        if username == ADMIN_USERNAME and hash_password(password) == ADMIN_PASSWORD_HASH:
            session['logged_in'] = True
            session['login_time'] = time.time()
            session['csrf_token'] = generate_csrf_token()
            log_admin_action('Login bem-sucedido', ip)
            return redirect(url_for('admin'))
        
        log_admin_action(f'Tentativa de login falha - usuário: {username}', ip)
        if username != ADMIN_USERNAME:
            return render_template('login.html', error='Usuário incorreto')
        else:
            return render_template('login.html', error='Senha incorreta')
    
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin():
    csrf_token = generate_csrf_token()
    
    # Verifica se é uma requisição AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'dados_banca': {
                'apostado': dados_banca['apostado'],
                'pago': dados_banca['pago'],
                'lucro': dados_banca['lucro'],
                'chance_vitoria': dados_banca['chance_vitoria']
            },
            'admin_logs': admin_logs[-10:],
            'csrf_token': csrf_token  # Incluindo o token CSRF na resposta
        })
    
    return render_template('admin.html', 
                         dados_banca=dados_banca,
                         csrf_token=csrf_token,
                         admin_logs=admin_logs[-10:])

@app.route('/logout')
def logout():
    if 'logged_in' in session:
        log_admin_action('Logout', request.remote_addr)
    session.clear()
    return redirect(url_for('home'))

@app.route('/apostar', methods=['POST'])
def apostar():
    try:
        print("Iniciando processamento da aposta...")
        
        ip = request.remote_addr
        
        # Verifica limite de apostas
        if not limitar_apostas(ip):
            return jsonify({
                'erro': f'Limite de {MAX_APOSTAS_POR_MINUTO} apostas por minuto excedido. Aguarde um pouco.'
            }), 429

        # Verifica se os campos necessários existem
        if 'animal' not in request.form or 'valor' not in request.form:
            return jsonify({'erro': 'Campos obrigatórios faltando'}), 400
        
        try:
            numero = int(request.form['animal'])
            valor = float(request.form['valor'])
            
            # Validação adicional dos valores
            if numero not in animais:
                return jsonify({'erro': 'Animal inválido'}), 400
            if valor <= 0:
                return jsonify({'erro': 'Valor deve ser positivo'}), 400
            
        except ValueError:
            return jsonify({'erro': 'Valores inválidos'}), 400

        # Verifica se o valor da aposta é válido
        if valor < VALOR_MINIMO_APOSTA:
            return jsonify({
                'erro': f'O valor mínimo da aposta é R$ {VALOR_MINIMO_APOSTA:.2f}'
            }), 400

        # Verifica limite máximo de aposta
        if valor > LIMITE_APOSTA_MAXIMO:
            return jsonify({
                'erro': f'O valor máximo permitido por aposta é R$ {LIMITE_APOSTA_MAXIMO:.2f}'
            }), 400

        dados_banca['apostado'] += valor

        # Se a chance base for 0, a chance final também será 0
        if dados_banca['chance_vitoria'] == 0:
            chance_atual = 0
            print("Chance base é 0%, chance final também será 0%")
        # Se o valor for maior que R$ 10,00, a chance será 0
        elif valor > 10.0:
            chance_atual = 0
            print("Valor acima de R$ 10,00, chance final será 0%")
        else:
            # Calcula a chance de vitória baseada no valor da aposta
            chance_atual = float(dados_banca['chance_vitoria'])  # Começa com a chance base
            print(f"Chance base definida no admin: {chance_atual}%")
            
            # Calcula a chance proporcional à chance base do admin
            chance_proporcional = (chance_atual / 100) * 20  # 20% é o máximo para aposta mínima
            
            # Aplica redução base para valor mínimo (R$ 5,00)
            if valor == VALOR_MINIMO_APOSTA:
                chance_atual = chance_proporcional
                print(f"Chance proporcional para aposta mínima (R$ 5,00): {chance_atual}%")
            
            # Redução para valores acima do mínimo
            elif valor > VALOR_MINIMO_APOSTA:
                valor_acima_minimo = valor - VALOR_MINIMO_APOSTA
                
                # Começa com a chance proporcional
                chance_atual = chance_proporcional
                
                # Redução progressiva (quanto mais alto o valor, maior a redução)
                reducao_progressiva = (valor_acima_minimo / VALOR_MINIMO_APOSTA) * (chance_atual * 0.5)
                
                # Aplica a redução progressiva
                chance_atual = max(1, chance_atual - reducao_progressiva)
                print(f"Chance após redução progressiva: {chance_atual}%")

            # Garante que a chance está entre 1% e o máximo definido no admin
            chance_atual = max(1, min(chance_atual, dados_banca['chance_vitoria']))
            print(f"Chance final após ajustes: {chance_atual}%")

        # Sorteia o resultado baseado na chance calculada
        if random.uniform(0, 100) <= chance_atual:
            sorteado = numero
        else:
            opcoes = [n for n in animais.keys() if n != numero]
            sorteado = random.choice(opcoes)

        nome_sorteado = animais[sorteado]

        if sorteado == numero:
            ganho = valor * 20
            dados_banca['pago'] += ganho
            resultado = f"🎉 Você ganhou R${ganho:.2f}!"
            log_admin_action(f'Aposta de R${valor:.2f} - Ganhou R${ganho:.2f}', ip, valor, chance_atual)
            # Tenta imprimir o resultado
            printer.print_result(valor, f"Ganhou R${ganho:.2f}", chance_atual)
        else:
            resultado = "😞 Você perdeu."
            log_admin_action(f'Aposta de R${valor:.2f} - Perdeu', ip, valor, chance_atual)
            # Tenta imprimir o resultado
            printer.print_result(valor, "Perdeu", chance_atual)

        dados_banca['lucro'] = dados_banca['apostado'] - dados_banca['pago']

        dados_banca['ranking'].insert(0, f"{sorteado:02d} - {nome_sorteado}")
        if len(dados_banca['ranking']) > 10:
            dados_banca['ranking'].pop()

        resposta = {
            'resultado': resultado,
            'animal': nome_sorteado,
            'numero': sorteado,
            'apostado': dados_banca['apostado'],
            'pago': dados_banca['pago'],
            'lucro': dados_banca['lucro'],
            'ranking': dados_banca['ranking']
        }
        return jsonify(resposta)

    except Exception as e:
        print(f"ERRO CRÍTICO: {str(e)}")
        import traceback
        print(f"Traceback completo:\n{traceback.format_exc()}")
        return jsonify({'erro': 'Erro interno do servidor'}), 500

@app.route('/configurar', methods=['POST'])
@login_required
def configurar():
    # Validação do token CSRF
    if not validate_csrf_token(request.form.get('csrf_token')):
        log_admin_action('Tentativa de configuração com token CSRF inválido', request.remote_addr)
        return jsonify({'erro': 'Token de segurança inválido'}), 403
    
    try:
        nova_chance = int(float(request.form['chance']))  # Converte para float primeiro e depois para int
        if not (0 <= nova_chance <= 100):
            return jsonify({'erro': 'Chance deve estar entre 0 e 100'}), 400
            
        dados_banca['chance_vitoria'] = nova_chance
        print(f"Nova chance de vitória configurada: {nova_chance}%")
        log_admin_action(f'Chance atualizada para {nova_chance}%', request.remote_addr)
        return jsonify({'status': 'Chance atualizada'})
    except ValueError:
        return jsonify({'erro': 'Valor inválido'}), 400

@app.route('/zerar', methods=['POST'])
@login_required
def zerar():
    # Validação do token CSRF
    if not validate_csrf_token(request.form.get('csrf_token')):
        log_admin_action('Tentativa de zerar banca com token CSRF inválido', request.remote_addr)
        return jsonify({'erro': 'Token de segurança inválido'}), 403
    
    dados_banca['apostado'] = 0
    dados_banca['pago'] = 0
    dados_banca['lucro'] = 0
    dados_banca['ranking'] = []
    
    log_admin_action('Banca zerada', request.remote_addr)
    return jsonify({'status': 'Banca zerada'})

# Adicionar rota para estatísticas
@app.route('/estatisticas')
@login_required
def estatisticas():
    total_apostas = len([log for log in admin_logs if 'apostou' in log['action'].lower()])
    total_ganhos = sum(1 for log in admin_logs if 'ganhou' in log['action'].lower())
    
    stats = {
        'total_apostas': total_apostas,
        'total_ganhos': total_ganhos,
        'taxa_vitoria': (total_ganhos / total_apostas * 100) if total_apostas > 0 else 0,
        'maior_aposta': max([log['valor'] for log in admin_logs if 'apostou' in log['action'].lower()], default=0),
        'maior_premio': max([log['valor'] for log in admin_logs if 'ganhou' in log['action'].lower()], default=0)
    }
    
    return jsonify(stats)

@app.route('/imprimir', methods=['POST'])
def imprimir():
    try:
        resultado = request.form.get('resultado')
        animal = request.form.get('animal')
        valor = float(request.form.get('valor'))
        
        # Extrai a chance real do resultado (se ganhou)
        chance_real = dados_banca['chance_vitoria']
        
        # Tenta imprimir
        if printer.print_result(valor, resultado, chance_real):
            return jsonify({'status': 'Imprimindo resultado...'})
        else:
            return jsonify({'erro': 'Não foi possível imprimir. Verifique a impressora.'})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

