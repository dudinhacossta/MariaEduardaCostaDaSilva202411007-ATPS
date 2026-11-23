# Urna Eletrônica — ATPS Tópicos Avançados em ADS e SI

**Aluna:** Maria Eduarda Costa da Silva — **Matrícula:** 202411007

Simulação de urna eletrônica em Python com banco SQLite: CRUD de candidatos e eleitores
(cadastrar, alterar, excluir e listar), votação (com branco, nulo, CONFIRMA/CORRIGE e bloqueio
de voto duplo) e apuração com a regra da maioria absoluta.

Tem duas formas de usar, as duas com o mesmo banco de dados:

- **Versão web** (`app.py`): o Python (Flask) cuida do banco e das regras, e a tela abre no navegador.
- **Versão em modo texto** (`urna.py`): roda direto no terminal, sem instalar nada.

## Requisitos

- Python 3.8+
- Flask (só para a versão web): `pip install -r requirements.txt`

## Como executar

```bash
cd maria_eduarda_costa_da_silva

# versão web — abre sozinha no navegador em http://127.0.0.1:5000
pip install -r requirements.txt
python app.py

# versão em modo texto
python urna.py
```

O arquivo `urna.db` é criado automaticamente ao lado do `urna.py` a partir do `banco.sql`.

## Roteiro rápido de teste (versão web)

1. Aba **Apuração** → *Carregar dados de exemplo*: 3 candidatos (10, 25, 40) e 12 eleitores (títulos 1001 a 1012)
2. Abas **Candidatos** e **Eleitores**: cadastrar, clicar numa linha para alterar ou excluir
3. Aba **Votação**: digitar o título, *Liberar urna*, votar no teclado da urna (mínimo de 10 votos)
4. Aba **Apuração**: gráfico e resultado; *Zerar urna* para testar de novo

## Estrutura

```
maria_eduarda_costa_da_silva/
  app.py             # servidor web (Flask) com as rotas da API
  urna.py            # versão em modo texto + funções de banco usadas pelas duas versões
  banco.sql          # script de criação das tabelas
  templates/
    index.html       # página da urna
  static/
    style.css        # aparência
    app.js           # comportamento das telas
  requirements.txt
  LINK_DO_VIDEO_MARIA_EDUARDA_COSTA_DA_SILVA.txt
```
