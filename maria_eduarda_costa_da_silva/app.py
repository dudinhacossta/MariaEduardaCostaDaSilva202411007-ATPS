"""
Urna Eletronica - versao web
ATPS Topicos Avancados em ADS e SI

O Python (Flask) cuida do banco de dados e de todas as regras da eleicao.
O navegador so mostra as telas e chama as rotas /api abaixo.

Execute:  python app.py     e abra http://127.0.0.1:5000
"""

import sqlite3
import threading
import webbrowser

from flask import Flask, g, jsonify, render_template, request

from urna import conectar, calcular_resultado, carregar_exemplo, MINIMO_VOTOS

app = Flask(__name__)
app.json.ensure_ascii = False


# ---------------------------------------------------------------- banco
def db():
    """Uma conexao por requisicao, fechada automaticamente no final."""
    if "conexao" not in g:
        g.conexao = conectar()
    return g.conexao


@app.teardown_appcontext
def fechar_conexao(_erro):
    conexao = g.pop("conexao", None)
    if conexao is not None:
        conexao.close()


def corpo():
    return request.get_json(silent=True) or {}


def campo(dados, nome):
    return str(dados.get(nome, "")).strip()


def erro(mensagem, status=400):
    return jsonify({"erro": mensagem}), status


def ok(mensagem, status=200, **extra):
    return jsonify({"mensagem": mensagem, **extra}), status


# ---------------------------------------------------------------- pagina
@app.get("/")
def index():
    return render_template("index.html", minimo=MINIMO_VOTOS)


# ---------------------------------------------------------------- candidatos
@app.get("/api/candidatos")
def listar_candidatos():
    linhas = db().execute("SELECT numero, nome, partido FROM candidatos ORDER BY numero")
    return jsonify([{"numero": n, "nome": nome, "partido": p} for n, nome, p in linhas])


@app.post("/api/candidatos")
def cadastrar_candidato():
    dados = corpo()
    numero = campo(dados, "numero")
    nome = campo(dados, "nome")
    partido = campo(dados, "partido").upper()
    if not (numero.isdigit() and len(numero) == 2):
        return erro("O número deve ter exatamente 2 dígitos.")
    if not nome or not partido:
        return erro("Nome e partido são obrigatórios.")
    conexao = db()
    try:
        with conexao:
            conexao.execute("INSERT INTO candidatos (numero, nome, partido) VALUES (?, ?, ?)",
                            (int(numero), nome, partido))
    except sqlite3.IntegrityError:
        return erro("Já existe um candidato com esse número.", 409)
    return ok(f"Candidato {nome} cadastrado!", 201)


@app.put("/api/candidatos/<int:numero>")
def alterar_candidato(numero):
    dados = corpo()
    nome = campo(dados, "nome")
    partido = campo(dados, "partido").upper()
    if not nome or not partido:
        return erro("Nome e partido são obrigatórios.")
    conexao = db()
    with conexao:
        cursor = conexao.execute("UPDATE candidatos SET nome = ?, partido = ? WHERE numero = ?",
                                 (nome, partido, numero))
    if cursor.rowcount == 0:
        return erro("Candidato não encontrado.", 404)
    return ok(f"Candidato {numero:02d} atualizado.")


@app.delete("/api/candidatos/<int:numero>")
def excluir_candidato(numero):
    conexao = db()
    try:
        with conexao:
            cursor = conexao.execute("DELETE FROM candidatos WHERE numero = ?", (numero,))
    except sqlite3.IntegrityError:
        # A chave estrangeira em votos impede apagar quem ja recebeu votos.
        return erro("Esse candidato já recebeu votos e não pode ser excluído. "
                    "Zere a urna primeiro (aba Apuração).", 409)
    if cursor.rowcount == 0:
        return erro("Candidato não encontrado.", 404)
    return ok("Candidato excluído.")


# ---------------------------------------------------------------- eleitores
@app.get("/api/eleitores")
def listar_eleitores():
    linhas = db().execute("SELECT titulo, nome, ja_votou FROM eleitores ORDER BY nome")
    return jsonify([{"titulo": t, "nome": n, "ja_votou": bool(v)} for t, n, v in linhas])


@app.post("/api/eleitores")
def cadastrar_eleitor():
    dados = corpo()
    titulo = campo(dados, "titulo")
    nome = campo(dados, "nome")
    if not titulo.isdigit():
        return erro("O título deve conter apenas números.")
    if not nome:
        return erro("O nome é obrigatório.")
    conexao = db()
    try:
        with conexao:
            conexao.execute("INSERT INTO eleitores (titulo, nome) VALUES (?, ?)", (titulo, nome))
    except sqlite3.IntegrityError:
        return erro("Esse título já está cadastrado.", 409)
    return ok(f"Eleitor(a) {nome} cadastrado(a)!", 201)


@app.put("/api/eleitores/<titulo>")
def alterar_eleitor(titulo):
    nome = campo(corpo(), "nome")
    if not nome:
        return erro("O nome é obrigatório.")
    conexao = db()
    with conexao:
        cursor = conexao.execute("UPDATE eleitores SET nome = ? WHERE titulo = ?", (nome, titulo))
    if cursor.rowcount == 0:
        return erro("Eleitor não encontrado.", 404)
    return ok(f"Eleitor {titulo} atualizado.")


@app.delete("/api/eleitores/<titulo>")
def excluir_eleitor(titulo):
    conexao = db()
    eleitor = conexao.execute("SELECT nome, ja_votou FROM eleitores WHERE titulo = ?",
                              (titulo,)).fetchone()
    if eleitor is None:
        return erro("Eleitor não encontrado.", 404)
    nome, ja_votou = eleitor
    if ja_votou:
        # Se apagasse, o mesmo titulo poderia ser cadastrado de novo e votar duas vezes.
        return erro(f"{nome} já votou e não pode ser excluído(a). "
                    "Isso garante a integridade da eleição.", 409)
    with conexao:
        conexao.execute("DELETE FROM eleitores WHERE titulo = ?", (titulo,))
    return ok(f"{nome} excluído(a).")


# ---------------------------------------------------------------- votacao
@app.post("/api/liberar")
def liberar_eleitor():
    """O mesario informa o titulo; a urna so libera quem existe e ainda nao votou."""
    titulo = campo(corpo(), "titulo")
    conexao = db()
    eleitor = conexao.execute("SELECT nome, ja_votou FROM eleitores WHERE titulo = ?",
                              (titulo,)).fetchone()
    if eleitor is None:
        return erro("Eleitor não encontrado.", 404)
    nome, ja_votou = eleitor
    if ja_votou:
        return erro(f"{nome} já votou! Cada eleitor só pode votar uma vez.", 409)
    if conexao.execute("SELECT COUNT(*) FROM candidatos").fetchone()[0] == 0:
        return erro("Cadastre ao menos um candidato antes de votar.")
    return jsonify({"titulo": titulo, "nome": nome})


@app.post("/api/votar")
def votar():
    dados = corpo()
    titulo = campo(dados, "titulo")
    voto = campo(dados, "voto").upper()
    conexao = db()

    if voto == "BRANCO":
        tipo, numero = "BRANCO", None
    elif voto.isdigit() and len(voto) == 2:
        existe = conexao.execute("SELECT 1 FROM candidatos WHERE numero = ?",
                                 (int(voto),)).fetchone()
        tipo, numero = ("VALIDO", int(voto)) if existe else ("NULO", None)
    else:
        return erro("Voto inválido.")

    # Marca o eleitor e grava o voto na mesma transacao.
    # O "AND ja_votou = 0" garante que o mesmo eleitor nunca vota duas vezes,
    # mesmo que a pagina envie o voto repetido.
    with conexao:
        cursor = conexao.execute(
            "UPDATE eleitores SET ja_votou = 1 WHERE titulo = ? AND ja_votou = 0", (titulo,))
        if cursor.rowcount == 0:
            return erro("Eleitor não encontrado ou já votou.", 409)
        conexao.execute("INSERT INTO votos (numero_candidato, tipo) VALUES (?, ?)",
                        (numero, tipo))
    return ok("Voto registrado.", tipo=tipo)


@app.get("/api/status")
def status():
    conexao = db()
    total = conexao.execute("SELECT COUNT(*) FROM votos").fetchone()[0]
    aptos = conexao.execute("SELECT COUNT(*) FROM eleitores WHERE ja_votou = 0").fetchone()[0]
    return jsonify({"total": total, "aptos": aptos, "minimo": MINIMO_VOTOS})


# ---------------------------------------------------------------- apuracao
@app.get("/api/apuracao")
def apuracao():
    r = calcular_resultado(db())
    r["candidatos"] = [{"numero": n, "nome": nome, "partido": p, "votos": qtd}
                       for n, nome, p, qtd in r["candidatos"]]
    r["minimo"] = MINIMO_VOTOS
    r["liberada"] = r["total"] >= MINIMO_VOTOS
    return jsonify(r)


@app.post("/api/exemplo")
def dados_exemplo():
    carregar_exemplo(db())
    return ok("Carregados 3 candidatos (10, 25, 40) e 12 eleitores (títulos 1001 a 1012).")


@app.post("/api/zerar")
def zerar_urna():
    conexao = db()
    with conexao:
        conexao.execute("DELETE FROM votos")
        conexao.execute("UPDATE eleitores SET ja_votou = 0")
    return ok("Urna zerada.")


if __name__ == "__main__":
    endereco = "http://127.0.0.1:5000"
    print(f"Urna Eletronica rodando em {endereco}  (CTRL+C para encerrar)")
    threading.Timer(1.0, lambda: webbrowser.open(endereco)).start()
    app.run(port=5000, debug=False)
