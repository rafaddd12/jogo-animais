let animalSelecionado = null;
let nomeAnimalSelecionado = null;
let valorAposta = 0;
let lucroTotal = 0;
let historicoResultados = [];
let chanceVitoria = 20; // %

// Mostrar telas
function mostrarTela(nomeTela) {
    const telas = ['apostar', 'banca', 'resultados', 'configuracoes'];
    telas.forEach(tela => {
        document.getElementById(`tela-${tela}`).style.display = (tela === nomeTela) ? 'block' : 'none';
    });
}

// Selecionar animal
function selecionarAnimal(numero, nome, elemento) {
    animalSelecionado = numero;
    nomeAnimalSelecionado = nome;
    document.getElementById('animal-selecionado').innerText = `Animal Selecionado: ${numero} - ${nome}`;

    document.querySelectorAll('.animal-btn').forEach(btn => btn.classList.remove('selecionado'));
    elemento.classList.add('selecionado');
}

// Confirmar aposta
function confirmarAposta() {
    valorAposta = parseFloat(document.getElementById('valor').value);

    if (!animalSelecionado) {
        alert('Escolha um animal para apostar!');
        return;
    }

    if (isNaN(valorAposta) || valorAposta < 5) {
        alert('O valor mínimo da aposta é R$ 5,00!');
        return;
    }

    // Realizar o sorteio
    realizarSorteio();
}

// Realizar sorteio
async function realizarSorteio() {
    // Animação de seleção
    await animarSelecao(animalSelecionado);

    // Fazer a aposta
    fetch('/apostar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `animal=${animalSelecionado}&valor=${valorAposta}`
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.erro || 'Erro ao realizar a aposta');
            });
        }
        return response.json();
    })
    .then(data => {
        // Mostrar resultado
        document.getElementById('mensagem-resultado').innerText = data.resultado;
        document.getElementById('imagem-resultado').src = `/static/icons/${data.numero}.jpg`;
        document.getElementById('nome-resultado').innerText = `${data.numero} - ${data.animal}`;
        document.getElementById('area-resultado').style.display = 'block';
    })
    .catch(error => {
        alert(error.message);
    });
}

// Animação de seleção
async function animarSelecao(numeroSorteado) {
    const botoes = document.querySelectorAll('.animal-btn');
    const totalBotoes = botoes.length;
    
    // Função para animar um botão
    const animarBotao = (botao) => {
        botao.classList.add('animacao');
        setTimeout(() => {
            botao.classList.remove('animacao');
        }, 100);
    };

    // Função para embaralhar array
    const embaralharArray = (array) => {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    };

    // Criar array com índices dos botões
    let indices = Array.from({length: totalBotoes}, (_, i) => i);
    
    // Animar todos os botões em sequência aleatória (2 voltas)
    for (let i = 0; i < 2; i++) {
        indices = embaralharArray([...indices]);
        for (let j = 0; j < totalBotoes; j++) {
            await new Promise(resolve => {
                setTimeout(() => {
                    animarBotao(botoes[indices[j]]);
                    resolve();
                }, 50);
            });
        }
    }

    // Animar até o número sorteado (5 animais)
    const indiceSorteado = numeroSorteado - 1;
    indices = embaralharArray([...indices]);
    let contador = 0;
    
    while (contador < 5) {
        const indiceAtual = indices[contador % indices.length];
        if (indiceAtual !== indiceSorteado) {
            await new Promise(resolve => {
                setTimeout(() => {
                    animarBotao(botoes[indiceAtual]);
                    resolve();
                }, 50);
            });
        }
        contador++;
    }

    // Destaque final no animal sorteado
    const botaoSorteado = botoes[indiceSorteado];
    botaoSorteado.classList.add('animacao');
    setTimeout(() => {
        botaoSorteado.classList.remove('animacao');
    }, 300);
}

// Limpar resultado
function limparResultado() {
    document.getElementById('area-resultado').style.display = 'none';
    document.getElementById('animal-selecionado').innerText = "Nenhum animal selecionado";
    document.getElementById('valor').value = "";
    document.querySelectorAll('.animal-btn').forEach(btn => btn.classList.remove('selecionado'));
    animalSelecionado = null;
    nomeAnimalSelecionado = null;
}

// Atualizar lucro da banca e visão de status
function atualizarBanca() {
    const lucroSpan = document.getElementById('lucro-total');
    lucroSpan.innerText = `R$ ${lucroTotal.toFixed(2)}`;
    let status = document.getElementById('status-banca');
    if (!status) {
        status = document.createElement('div');
        status.id = 'status-banca';
        lucroSpan.parentNode.appendChild(status);
    }
    if (lucroTotal < 0) {
        status.innerText = 'Situação: Perdendo';
        status.style.color = '#d32f2f';
    } else if (lucroTotal > 0) {
        status.innerText = 'Situação: Ganhando';
        status.style.color = '#388e3c';
    } else {
        status.innerText = 'Situação: Neutro';
        status.style.color = '#333';
    }
}

// Atualizar lista de últimos resultados
function atualizarListaResultados() {
    const lista = document.getElementById('lista-resultados');
    lista.innerHTML = '';
    
    historicoResultados.slice(0, 10).forEach(resultado => {
        const li = document.createElement('li');
        li.innerText = resultado;
        lista.appendChild(li);
    });
}

// Configurações
document.getElementById('chance-vitoria').addEventListener('input', function () {
    chanceVitoria = parseInt(this.value);
});

// Zerar banca
function zerarBanca() {
    lucroTotal = 0;
    atualizarBanca();
    alert('Banca Zerada!');
}
