from flask import Flask, render_template, request, jsonify
import random
import os

app = Flask(__name__)

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

@app.route('/')
def home():
    return render_template('index.html', animais=animais)

@app.route('/apostar', methods=['POST'])
def apostar():
    numero = int(request.form['animal'])
    valor = float(request.form['valor'])

    dados_banca['apostado'] += valor

    if random.randint(1, 100) <= dados_banca['chance_vitoria']:
        sorteado = numero
    else:
        opcoes = [n for n in animais.keys() if n != numero]
        sorteado = random.choice(opcoes)

    nome_sorteado = animais[sorteado]

    if sorteado == numero:
        ganho = valor * 20
        dados_banca['pago'] += ganho
        resultado = f"🎉 Você ganhou R${ganho:.2f}!"
    else:
        resultado = "😞 Você perdeu."

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
        'ranking': dados_banca['ranking']
    })

@app.route('/configurar', methods=['POST'])
def configurar():
    nova_chance = int(request.form['chance'])
    dados_banca['chance_vitoria'] = nova_chance
    return jsonify({'status': 'Chance atualizada'})

@app.route('/zerar', methods=['POST'])
def zerar():
    dados_banca['apostado'] = 0
    dados_banca['pago'] = 0
    dados_banca['lucro'] = 0
    dados_banca['ranking'] = []
    return jsonify({'status': 'Banca zerada'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

