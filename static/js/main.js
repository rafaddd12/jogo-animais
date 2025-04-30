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
    // Remove seleção anterior
    document.querySelectorAll('.animal-btn').forEach(btn => btn.classList.remove('selecionado'));
    
    // Adiciona seleção atual
    elemento.classList.add('selecionado');
    
    // Atualiza o texto do animal selecionado
    document.getElementById('animal-selecionado').textContent = `Animal Selecionado: ${numero} - ${nome}`;
    
    // Armazena o número e nome do animal selecionado no botão
    elemento.setAttribute('data-numero', numero);
    elemento.setAttribute('data-nome', nome);
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

// Confirmar aposta
function confirmarAposta() {
    const valor = parseFloat(document.getElementById('valor').value);
    const animalSelecionado = document.querySelector('.animal-btn.selecionado');

    if (!animalSelecionado) {
        alert('Por favor, selecione um animal');
        return;
    }

    if (isNaN(valor) || valor < 5) {
        alert('O valor mínimo da aposta é R$ 5,00');
        return;
    }

    const numero = animalSelecionado.getAttribute('data-numero');

    // Desabilita o botão de apostar durante o processo
    const botaoApostar = document.querySelector('.botao-apostar');
    botaoApostar.disabled = true;

    // Realiza a animação do sorteio
    animarSelecao(numero)
        .then(() => {
            // Após a animação, faz a aposta
            return fetch('/apostar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `animal=${numero}&valor=${valor}`
            });
        })
        .then(response => response.json())
        .then(data => {
            if (data.erro) {
                throw new Error(data.erro);
            }

            // Atualiza o ranking
            if (data.ranking) {
                atualizarRanking(data.ranking);
            }

            // Mostra o resultado
            const areaResultado = document.getElementById('area-resultado');
            const mensagemResultado = document.getElementById('mensagem-resultado');
            const imagemResultado = document.getElementById('imagem-resultado');
            const nomeResultado = document.getElementById('nome-resultado');
            const overlay = document.getElementById('overlay');

            if (!areaResultado || !mensagemResultado || !imagemResultado || !nomeResultado || !overlay) {
                throw new Error('Elementos do resultado não encontrados');
            }

            mensagemResultado.textContent = data.resultado;
            mensagemResultado.className = data.resultado.includes('ganhou') ? 'mensagem-ganhou' : 'mensagem-perdeu';
            imagemResultado.src = `/static/icons/${data.numero}.jpg`;
            nomeResultado.textContent = `${data.numero} - ${data.animal}`;

            // Esconde a área de aposta e mostra o resultado
            document.getElementById('area-aposta').style.display = 'none';
            overlay.style.display = 'block';
            areaResultado.style.display = 'flex';

            // Se ganhou, dispara os confetes
            if (data.resultado.includes('ganhou')) {
                createConfetti();
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert(error.message || 'Ocorreu um erro ao processar sua aposta');
        })
        .finally(() => {
            // Reabilita o botão de apostar
            botaoApostar.disabled = false;
        });
}

// Limpar resultado e voltar para aposta
function limparResultado() {
    const areaResultado = document.getElementById('area-resultado');
    const overlay = document.getElementById('overlay');
    const areaAposta = document.getElementById('area-aposta');
    const animalSelecionado = document.getElementById('animal-selecionado');
    const valorInput = document.getElementById('valor');

    // Limpa a seleção do animal
    document.querySelectorAll('.animal-btn').forEach(btn => btn.classList.remove('selecionado'));
    animalSelecionado.textContent = 'Nenhum animal selecionado';
    valorInput.value = '';

    // Esconde o resultado e mostra a área de aposta
    overlay.style.display = 'none';
    areaResultado.style.display = 'none';
    areaAposta.style.display = 'block';
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

// Atualizar ranking
function atualizarRanking(ranking) {
    const rankingList = document.getElementById('ranking-list');
    if (!rankingList) return;

    rankingList.innerHTML = '';
    ranking.forEach(item => {
        const div = document.createElement('div');
        div.className = 'ranking-item';
        div.textContent = item;
        rankingList.appendChild(div);
    });
}
