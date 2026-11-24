

import os

import pymysql
from pymysql.err import IntegrityError

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_SCRIPT = "banco.sql"
MINIMO_VOTOS = 10

MYSQL = {
    "host": os.environ.get("URNA_DB_HOST", "localhost"),
    "port": int(os.environ.get("URNA_DB_PORTA", "3306")),
    "user": os.environ.get("URNA_DB_USUARIO", "root"),
    "password": os.environ.get("URNA_DB_SENHA", ""),
}
NOME_BANCO = "urna_eletronica"


# ---------------------------------------------------------------- banco
class Banco:
    """Conexao com o MySQL.
    execute() devolve o cursor e 'with banco:' abre uma transacao
    (commit se der certo, rollback se der erro)."""

    def __init__(self, conexao):
        self.conexao = conexao

    def execute(self, sql, parametros=()):
        cursor = self.conexao.cursor()
        cursor.execute(sql, parametros)
        return cursor

    def executemany(self, sql, lista):
        cursor = self.conexao.cursor()
        cursor.executemany(sql, lista)
        return cursor

    def commit(self):
        self.conexao.commit()

    def close(self):
        self.conexao.close()

    def __enter__(self):
        self.conexao.begin()
        return self

    def __exit__(self, tipo_erro, erro, rastro):
        if tipo_erro is None:
            self.conexao.commit()
        else:
            self.conexao.rollback()
        return False


_tabelas_criadas = False


def criar_banco(banco):
    """Executa o banco.sql: cria o banco urna_eletronica e as tabelas, se nao existirem."""
    with open(os.path.join(PASTA, ARQUIVO_SCRIPT), encoding="utf-8") as f:
        linhas = [linha for linha in f if not linha.strip().startswith("--")]
    for comando in "".join(linhas).split(";"):
        if comando.strip():
            banco.execute(comando)


def conectar():
    global _tabelas_criadas
    conexao = pymysql.connect(**MYSQL, charset="utf8mb4", autocommit=True)
    banco = Banco(conexao)
    if not _tabelas_criadas:
        criar_banco(banco)
        _tabelas_criadas = True
    conexao.select_db(NOME_BANCO)
    return banco


# ---------------------------------------------------------------- tela
def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")


def titulo(texto):
    print("\n" + "=" * 50)
    print(texto.center(50))
    print("=" * 50)


def pausar():
    input("\nPressione ENTER para continuar...")


# ---------------------------------------------------------------- cadastros
def cadastrar_candidato(conexao):
    titulo("CADASTRO DE CANDIDATO")
    numero = input("Numero do candidato (2 digitos): ").strip()
    if not (numero.isdigit() and len(numero) == 2):
        print("Numero invalido. Use exatamente 2 digitos.")
        return
    nome = input("Nome: ").strip()
    partido = input("Partido: ").strip().upper()
    if not nome or not partido:
        print("Nome e partido sao obrigatorios.")
        return
    try:
        conexao.execute("INSERT INTO candidatos (numero, nome, partido) VALUES (%s, %s, %s)",
                        (int(numero), nome, partido))
        conexao.commit()
        print(f"Candidato {nome} ({numero}) cadastrado!")
    except IntegrityError:
        print("Ja existe um candidato com esse numero.")


def cadastrar_eleitor(conexao):
    titulo("CADASTRO DE ELEITOR")
    titulo_eleitor = input("Numero do titulo de eleitor: ").strip()
    if not titulo_eleitor.isdigit():
        print("O titulo deve conter apenas numeros.")
        return
    nome = input("Nome: ").strip()
    if not nome:
        print("Nome obrigatorio.")
        return
    try:
        conexao.execute("INSERT INTO eleitores (titulo, nome) VALUES (%s, %s)",
                        (titulo_eleitor, nome))
        conexao.commit()
        print(f"Eleitor {nome} cadastrado!")
    except IntegrityError:
        print("Esse titulo ja esta cadastrado.")


# ---------------------------------------------------------------- alterar / excluir
def buscar_candidato(conexao):
    """Pede o numero e devolve (numero, nome, partido) ou None."""
    numero = input("Numero do candidato: ").strip()
    if not numero.isdigit():
        print("Numero invalido.")
        return None
    candidato = conexao.execute("SELECT numero, nome, partido FROM candidatos WHERE numero = %s",
                                (int(numero),)).fetchone()
    if candidato is None:
        print("Candidato nao encontrado.")
    return candidato


def alterar_candidato(conexao):
    titulo("ALTERAR CANDIDATO")
    candidato = buscar_candidato(conexao)
    if candidato is None:
        return
    numero, nome_atual, partido_atual = candidato
    print("(deixe em branco e tecle ENTER para manter o valor atual)")
    nome = input(f"Nome [{nome_atual}]: ").strip() or nome_atual
    partido = input(f"Partido [{partido_atual}]: ").strip().upper() or partido_atual
    with conexao:
        conexao.execute("UPDATE candidatos SET nome = %s, partido = %s WHERE numero = %s",
                        (nome, partido, numero))
    print(f"Candidato {numero:02d} atualizado: {nome} ({partido}).")


def excluir_candidato(conexao):
    titulo("EXCLUIR CANDIDATO")
    candidato = buscar_candidato(conexao)
    if candidato is None:
        return
    numero, nome, partido = candidato
    if input(f"Excluir {nome} ({partido})? (S/N): ").strip().upper() != "S":
        print("Exclusao cancelada.")
        return
    try:
        with conexao:
            conexao.execute("DELETE FROM candidatos WHERE numero = %s", (numero,))
        print(f"Candidato {nome} excluido.")
    except IntegrityError:
        # A chave estrangeira em votos impede apagar quem ja recebeu votos.
        print("Esse candidato ja recebeu votos e nao pode ser excluido.")
        print("Para exclui-lo, zere a urna primeiro (opcao 7 do menu principal).")


def buscar_eleitor(conexao):
    """Pede o titulo e devolve (titulo, nome, ja_votou) ou None."""
    titulo_eleitor = input("Numero do titulo de eleitor: ").strip()
    eleitor = conexao.execute("SELECT titulo, nome, ja_votou FROM eleitores WHERE titulo = %s",
                              (titulo_eleitor,)).fetchone()
    if eleitor is None:
        print("Eleitor nao encontrado.")
    return eleitor


def alterar_eleitor(conexao):
    titulo("ALTERAR ELEITOR")
    eleitor = buscar_eleitor(conexao)
    if eleitor is None:
        return
    titulo_eleitor, nome_atual, _ = eleitor
    print("(deixe em branco e tecle ENTER para manter o valor atual)")
    nome = input(f"Nome [{nome_atual}]: ").strip() or nome_atual
    with conexao:
        conexao.execute("UPDATE eleitores SET nome = %s WHERE titulo = %s", (nome, titulo_eleitor))
    print(f"Eleitor {titulo_eleitor} atualizado: {nome}.")


def excluir_eleitor(conexao):
    titulo("EXCLUIR ELEITOR")
    eleitor = buscar_eleitor(conexao)
    if eleitor is None:
        return
    titulo_eleitor, nome, ja_votou = eleitor
    if ja_votou:
        # Se apagasse, o mesmo titulo poderia ser cadastrado de novo e votar duas vezes.
        print(f"{nome} ja votou e nao pode ser excluido (garante a integridade da eleicao).")
        return
    if input(f"Excluir o eleitor {nome}? (S/N): ").strip().upper() != "S":
        print("Exclusao cancelada.")
        return
    with conexao:
        conexao.execute("DELETE FROM eleitores WHERE titulo = %s", (titulo_eleitor,))
    print(f"Eleitor {nome} excluido.")


# ---------------------------------------------------------------- listagens
def listar_candidatos(conexao):
    titulo("CANDIDATOS")
    for numero, nome, partido in conexao.execute(
            "SELECT numero, nome, partido FROM candidatos ORDER BY numero"):
        print(f"  {numero:02d} - {nome} ({partido})")


def listar_eleitores(conexao):
    titulo("ELEITORES")
    for tit, nome, votou in conexao.execute(
            "SELECT titulo, nome, ja_votou FROM eleitores ORDER BY nome"):
        situacao = "JA VOTOU" if votou else "apto"
        print(f"  {tit:<8} {nome:<25} {situacao}")


def listar(conexao):
    listar_candidatos(conexao)
    listar_eleitores(conexao)


def carregar_exemplo(conexao):
    """Dados de teste: 3 candidatos e 12 eleitores."""
    candidatos = [(10, "Ana Souza", "PTA"), (25, "Bruno Lima", "PTB"),
                  (40, "Carla Mendes", "PTC")]
    eleitores = [(str(1000 + i), f"Eleitor {i}") for i in range(1, 13)]
    conexao.executemany("INSERT IGNORE INTO candidatos VALUES (%s, %s, %s)", candidatos)
    conexao.executemany("INSERT IGNORE INTO eleitores (titulo, nome) VALUES (%s, %s)", eleitores)
    conexao.commit()
    print("Dados de exemplo carregados (titulos 1001 a 1012).")


# ---------------------------------------------------------------- votacao
def registrar_voto(conexao):
    """Faz um voto completo. Retorna True se o voto foi registrado."""
    titulo_eleitor = input("\nTitulo do eleitor: ").strip()
    eleitor = conexao.execute("SELECT nome, ja_votou FROM eleitores WHERE titulo = %s",
                              (titulo_eleitor,)).fetchone()
    if eleitor is None:
        print("Eleitor nao encontrado.")
        return False
    nome, ja_votou = eleitor
    if ja_votou:
        print(f"{nome} ja votou! Cada eleitor so pode votar uma vez.")
        return False

    print(f"\nEleitor: {nome}")
    while True:
        digitado = input("Digite o numero do candidato (B = branco): ").strip().upper()
        if digitado == "B":
            tipo, numero = "BRANCO", None
            print(">> VOTO EM BRANCO")
        else:
            candidato = None
            if digitado.isdigit():
                candidato = conexao.execute(
                    "SELECT numero, nome, partido FROM candidatos WHERE numero = %s",
                    (int(digitado),)).fetchone()
            if candidato:
                tipo, numero = "VALIDO", candidato[0]
                print(f">> {candidato[1]} - {candidato[2]}")
            else:
                tipo, numero = "NULO", None
                print(">> NUMERO ERRADO - VOTO NULO")

        opcao = input("[C] CONFIRMA  [R] CORRIGE: ").strip().upper()
        if opcao == "C":
            break

    # Marca o eleitor e grava o voto na mesma transacao:
    # ou as duas coisas acontecem, ou nenhuma acontece.
    with conexao:
        conexao.execute("UPDATE eleitores SET ja_votou = 1 WHERE titulo = %s", (titulo_eleitor,))
        conexao.execute("INSERT INTO votos (numero_candidato, tipo) VALUES (%s, %s)", (numero, tipo))
    print("\a*** FIM ***")
    return True


def votacao(conexao):
    titulo("VOTACAO")
    if conexao.execute("SELECT COUNT(*) FROM candidatos").fetchone()[0] == 0:
        print("Cadastre ao menos um candidato antes de votar.")
        return

    votos = 0
    while True:
        aptos = conexao.execute("SELECT COUNT(*) FROM eleitores WHERE ja_votou = 0").fetchone()[0]
        if aptos == 0:
            print("\nTodos os eleitores ja votaram.")
            break
        if votos >= MINIMO_VOTOS:
            if input(f"\n{votos} votos nesta sessao. Encerrar? (S/N): ").strip().upper() == "S":
                break
        else:
            print(f"\n--- Voto {votos + 1} de no minimo {MINIMO_VOTOS} ---")
        if registrar_voto(conexao):
            votos += 1

    print(f"\nVotacao encerrada. Votos nesta sessao: {votos}")


# ---------------------------------------------------------------- apuracao
def calcular_resultado(conexao):
    """Conta os votos e aplica a regra da maioria absoluta.
    Usada tanto pela versao em texto quanto pela interface grafica (urna_gui.py)."""
    total = conexao.execute("SELECT COUNT(*) FROM votos").fetchone()[0]
    brancos = conexao.execute("SELECT COUNT(*) FROM votos WHERE tipo = 'BRANCO'").fetchone()[0]
    nulos = conexao.execute("SELECT COUNT(*) FROM votos WHERE tipo = 'NULO'").fetchone()[0]
    validos = total - brancos - nulos

    candidatos = conexao.execute("""
        SELECT c.numero, c.nome, c.partido, COUNT(v.id) AS qtd
          FROM candidatos c
          LEFT JOIN votos v ON v.numero_candidato = c.numero
         GROUP BY c.numero, c.nome, c.partido
         ORDER BY qtd DESC, c.nome
    """).fetchall()

    # Regra da maioria absoluta (mais da metade dos votos validos)
    if total == 0:
        situacao = "Nenhum voto registrado."
    elif validos == 0:
        situacao = "Nao houve votos validos."
    else:
        primeiro = candidatos[0]
        empate = len(candidatos) > 1 and candidatos[1][3] == primeiro[3]
        if primeiro[3] > validos / 2:
            situacao = f"ELEITO(A) EM 1o TURNO: {primeiro[1]} ({primeiro[2]})"
        elif len(candidatos) > 1 and not empate:
            situacao = (f"Ninguem passou de 50% dos validos -> 2o TURNO: "
                        f"{primeiro[1]} x {candidatos[1][1]}")
        else:
            situacao = "Empate na primeira colocacao -> 2o TURNO necessario."

    return {"total": total, "brancos": brancos, "nulos": nulos, "validos": validos,
            "candidatos": candidatos, "situacao": situacao}


def apuracao(conexao):
    titulo("RESULTADO DA APURACAO")
    r = calcular_resultado(conexao)
    if r["total"] == 0:
        print(r["situacao"])
        return

    for numero, nome, partido, qtd in r["candidatos"]:
        perc = qtd / r["validos"] * 100 if r["validos"] else 0
        barra = "#" * int(perc / 4)
        print(f"{numero:02d} {nome:<15} {partido:<5} {qtd:>3} votos {perc:5.1f}% {barra}")

    print("-" * 50)
    print(f"Votos validos: {r['validos']} | Brancos: {r['brancos']} | "
          f"Nulos: {r['nulos']} | Total: {r['total']}")
    print("\n" + r["situacao"])


def zerar(conexao):
    if input("Apagar todos os votos e liberar os eleitores? (S/N): ").strip().upper() == "S":
        with conexao:
            conexao.execute("DELETE FROM votos")
            conexao.execute("UPDATE eleitores SET ja_votou = 0")
        print("Urna zerada.")


# ---------------------------------------------------------------- menu
def submenu(conexao, nome, opcoes):
    """Menu de CRUD (cadastrar, alterar, excluir, listar) de candidatos ou eleitores."""
    while True:
        limpar_tela()
        titulo(nome)
        for chave, (texto, _) in opcoes.items():
            print(f"  [{chave}] {texto}")
        print("  [0] Voltar ao menu principal")
        escolha = input("\nOpcao: ").strip()
        if escolha == "0":
            return
        if escolha in opcoes:
            opcoes[escolha][1](conexao)
        else:
            print("Opcao invalida.")
        pausar()


def menu_candidatos(conexao):
    submenu(conexao, "CANDIDATOS", {
        "1": ("Cadastrar candidato", cadastrar_candidato),
        "2": ("Alterar candidato", alterar_candidato),
        "3": ("Excluir candidato", excluir_candidato),
        "4": ("Listar candidatos", listar_candidatos),
    })


def menu_eleitores(conexao):
    submenu(conexao, "ELEITORES", {
        "1": ("Cadastrar eleitor", cadastrar_eleitor),
        "2": ("Alterar eleitor", alterar_eleitor),
        "3": ("Excluir eleitor", excluir_eleitor),
        "4": ("Listar eleitores", listar_eleitores),
    })


def main():
    conexao = conectar()
    opcoes = {
        "1": ("Candidatos (cadastrar, alterar, excluir)", menu_candidatos),
        "2": ("Eleitores (cadastrar, alterar, excluir)", menu_eleitores),
        "3": ("Listar candidatos e eleitores", listar),
        "4": ("Iniciar votacao", votacao),
        "5": ("Apuracao dos votos", apuracao),
        "6": ("Carregar dados de exemplo", carregar_exemplo),
        "7": ("Zerar urna", zerar),
    }
    while True:
        limpar_tela()
        titulo("URNA ELETRONICA")
        for chave, (texto, _) in opcoes.items():
            print(f"  [{chave}] {texto}")
        print("  [0] Sair")
        escolha = input("\nOpcao: ").strip()
        if escolha == "0":
            break
        if escolha in opcoes:
            funcao = opcoes[escolha][1]
            funcao(conexao)
            if funcao in (menu_candidatos, menu_eleitores):
                continue  # o submenu ja fez as pausas dele
        else:
            print("Opcao invalida.")
        pausar()
    conexao.close()
    print("Ate logo!")


if __name__ == "__main__":
    main()
