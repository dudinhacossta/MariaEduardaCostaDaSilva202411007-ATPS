# Urna Eletrônica — ATPS Tópicos Avançados em ADS e SI

**Aluna:** Maria Eduarda Costa da Silva — **Matrícula:** 202411007

Simulação de urna eletrônica em Python com banco **MySQL**: CRUD de candidatos e eleitores
(cadastrar, alterar, excluir e listar), votação (com branco, nulo, CONFIRMA/CORRIGE e bloqueio
de voto duplo) e apuração com a regra da maioria absoluta.

Tem duas formas de usar, as duas com o mesmo banco de dados:

- **Versão web** (`app.py`): o Python (Flask) cuida do banco e das regras, e a tela abre no navegador.
- **Versão em modo texto** (`urna.py`): roda direto no terminal.

## Requisitos

- Python 3.8+
- MySQL 8 ou MariaDB (o do XAMPP serve) rodando na porta 3306
- Bibliotecas: `pip install -r requirements.txt` (Flask e PyMySQL)

## Banco de dados

O `banco.sql` cria o banco `urna_eletronica` e as tabelas. Ele roda sozinho quando o programa
abre, mas também pode ser importado no phpMyAdmin ou no MySQL Workbench.

A conexão usa o usuário `root` sem senha (padrão do XAMPP). Se o seu MySQL tiver senha,
defina antes de rodar:

```bash
# Windows (PowerShell)
$env:URNA_DB_SENHA = "sua_senha"
```

Também dá para trocar `URNA_DB_HOST`, `URNA_DB_PORTA` e `URNA_DB_USUARIO` do mesmo jeito.

## Como executar

```bash
cd maria_eduarda_costa_da_silva
pip install -r requirements.txt

# versão web — abre sozinha no navegador em http://127.0.0.1:5000
python app.py

# versão em modo texto
python urna.py
```

## Roteiro rápido de teste (versão web)

1. Aba **Apuração** → *Carregar dados de exemplo*: 3 candidatos (10, 25, 40) e 12 eleitores (títulos 1001 a 1012)
2. Abas **Candidatos** e **Eleitores**: cadastrar, clicar numa linha para alterar ou excluir
3. Aba **Votação**: digitar o título, *Liberar urna*, votar no teclado da urna (mínimo de 10 votos)
4. Aba **Apuração**: gráfico e resultado; *Zerar urna* para testar de novo

## Estrutura

```
maria_eduarda_costa_da_silva/
  app.py             # servidor web (Flask) com as rotas da API
  urna.py            # conexão com o MySQL, versão em modo texto e funções usadas pelas duas versões
  banco.sql          # script MySQL de criação do banco e das tabelas
  templates/
    index.html       # página da urna
  static/
    style.css        # aparência
    app.js           # comportamento das telas
  requirements.txt
  LINK_DO_VIDEO_MARIA_EDUARDA_COSTA_DA_SILVA.txt
```
