"""
Urna Eletronica - Interface grafica (Tkinter)
ATPS Topicos Avancados em ADS e SI

Usa o mesmo banco de dados (urna.db, criado a partir de banco.sql) e as mesmas
regras da versao em texto (urna.py).

Execute:  python urna_gui.py
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

from urna import conectar, calcular_resultado, MINIMO_VOTOS

# ---------------------------------------------------------------- cores e fontes
COR_FUNDO = "#eef1f5"
COR_TOPO = "#1f3b63"
COR_CORPO_URNA = "#d8d2c4"
COR_TELA = "#f7f7f2"
COR_TECLADO = "#2b2b2b"
COR_BRANCO = "#ffffff"
COR_CORRIGE = "#e8792b"
COR_CONFIRMA = "#2e9e48"
CORES_BARRAS = ["#2f6fd1", "#e0533d", "#2e9e48", "#9b59b6", "#f1a321", "#16a2b8"]

FONTE = "Segoe UI"


class UrnaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.conexao = conectar()

        self.title("Urna Eletronica - ATPS")
        self.geometry("980x640")
        self.minsize(900, 600)
        self.configure(bg=COR_FUNDO)

        self.configurar_estilo()
        self.criar_topo()

        self.abas = ttk.Notebook(self)
        self.abas.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.criar_aba_votacao()
        self.criar_aba_candidatos()
        self.criar_aba_eleitores()
        self.criar_aba_apuracao()
        self.abas.bind("<<NotebookTabChanged>>", lambda e: self.atualizar_tudo())

        self.bind_all("<Key>", self.tecla_fisica)
        self.protocol("WM_DELETE_WINDOW", self.sair)
        self.atualizar_tudo()

    # ------------------------------------------------------------ aparencia
    def configurar_estilo(self):
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure(".", font=(FONTE, 10), background=COR_FUNDO)
        estilo.configure("TNotebook", background=COR_FUNDO, borderwidth=0)
        estilo.configure("TNotebook.Tab", font=(FONTE, 11, "bold"), padding=(18, 8))
        estilo.map("TNotebook.Tab", background=[("selected", "#ffffff")])
        estilo.configure("TFrame", background=COR_FUNDO)
        estilo.configure("TLabelframe", background=COR_FUNDO)
        estilo.configure("TLabelframe.Label", font=(FONTE, 11, "bold"), background=COR_FUNDO)
        estilo.configure("TLabel", background=COR_FUNDO)
        estilo.configure("Treeview", rowheight=26, font=(FONTE, 10))
        estilo.configure("Treeview.Heading", font=(FONTE, 10, "bold"))
        estilo.configure("TButton", padding=(10, 6))
        estilo.configure("Perigo.TButton", foreground="#b3261e")
        estilo.configure("green.Horizontal.TProgressbar", background=COR_CONFIRMA)

    def criar_topo(self):
        topo = tk.Frame(self, bg=COR_TOPO)
        topo.pack(fill="x", pady=(0, 10))
        tk.Label(topo, text="URNA ELETRÔNICA", bg=COR_TOPO, fg="white",
                 font=(FONTE, 18, "bold")).pack(side="left", padx=16, pady=10)
        tk.Label(topo, text="Eleição para Prefeito  •  ATPS Tópicos Avançados em ADS e SI",
                 bg=COR_TOPO, fg="#c9d6ea", font=(FONTE, 10)).pack(side="left", pady=10)

    def atualizar_tudo(self):
        self.carregar_candidatos()
        self.carregar_eleitores()
        self.desenhar_apuracao()
        self.atualizar_contador()

    # ================================================================ VOTACAO
    def criar_aba_votacao(self):
        aba = ttk.Frame(self.abas, padding=12)
        self.abas.add(aba, text="  Votação  ")

        # Estado da urna
        self.eleitor_atual = None      # (titulo, nome) do eleitor liberado
        self.digitos = ""              # numero digitado
        self.voto_branco = False
        self.votos_sessao = 0

        # --- painel do mesario (esquerda)
        mesario = ttk.LabelFrame(aba, text="Mesário", padding=12)
        mesario.pack(side="left", fill="y", padx=(0, 12))

        ttk.Label(mesario, text="Título do eleitor:").pack(anchor="w")
        self.var_titulo_voto = tk.StringVar()
        self.ent_titulo_voto = ttk.Entry(mesario, textvariable=self.var_titulo_voto,
                                         font=(FONTE, 12), width=18)
        self.ent_titulo_voto.pack(fill="x", pady=(2, 8))
        self.ent_titulo_voto.bind("<Return>", lambda e: self.liberar_urna())

        self.btn_liberar = ttk.Button(mesario, text="Liberar urna", command=self.liberar_urna)
        self.btn_liberar.pack(fill="x")
        self.btn_cancelar = ttk.Button(mesario, text="Cancelar eleitor",
                                       command=self.cancelar_eleitor, state="disabled")
        self.btn_cancelar.pack(fill="x", pady=(6, 0))

        self.lbl_status = tk.Label(mesario, text="", bg=COR_FUNDO, fg="#444",
                                   font=(FONTE, 10), wraplength=200, justify="left")
        self.lbl_status.pack(anchor="w", pady=(14, 0))

        ttk.Separator(mesario).pack(fill="x", pady=14)
        self.lbl_contador = ttk.Label(mesario, text="", font=(FONTE, 10, "bold"))
        self.lbl_contador.pack(anchor="w")
        self.barra_progresso = ttk.Progressbar(mesario, maximum=MINIMO_VOTOS, length=200,
                                               style="green.Horizontal.TProgressbar")
        self.barra_progresso.pack(fill="x", pady=(4, 0))
        self.lbl_aptos = ttk.Label(mesario, text="")
        self.lbl_aptos.pack(anchor="w", pady=(8, 0))

        ttk.Label(mesario, text="Dica: depois de liberar, dá para votar\n"
                                "pelo teclado do computador:\n"
                                "números, B = branco,\n"
                                "Backspace = corrige, Enter = confirma",
                  foreground="#666").pack(side="bottom", anchor="w")

        # --- corpo da urna (direita)
        corpo = tk.Frame(aba, bg=COR_CORPO_URNA, bd=2, relief="ridge")
        corpo.pack(side="left", fill="both", expand=True)

        self.tela = tk.Frame(corpo, bg=COR_TELA, bd=3, relief="sunken")
        self.tela.pack(side="left", fill="both", expand=True, padx=18, pady=18)

        teclado = tk.Frame(corpo, bg=COR_TECLADO, padx=14, pady=14)
        teclado.pack(side="right", fill="y", padx=(0, 18), pady=18)
        tk.Label(teclado, text="JUSTIÇA ELEITORAL", bg=COR_TECLADO, fg="#bbbbbb",
                 font=(FONTE, 9, "bold")).grid(row=0, column=0, columnspan=3, pady=(0, 10))

        teclas = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
        for i, t in enumerate(teclas):
            self.botao_tecla(teclado, t).grid(row=1 + i // 3, column=i % 3, padx=4, pady=4)
        self.botao_tecla(teclado, "0").grid(row=4, column=1, padx=4, pady=4)

        acoes = tk.Frame(teclado, bg=COR_TECLADO)
        acoes.grid(row=5, column=0, columnspan=3, pady=(14, 0))
        for texto, cor, fg, cmd in (("BRANCO", COR_BRANCO, "black", self.votar_branco),
                                    ("CORRIGE", COR_CORRIGE, "black", self.corrigir),
                                    ("CONFIRMA", COR_CONFIRMA, "black", self.confirmar)):
            tk.Button(acoes, text=texto, bg=cor, fg=fg, activebackground=cor,
                      font=(FONTE, 9, "bold"), width=9, height=2 if texto != "CONFIRMA" else 3,
                      relief="raised", bd=2, cursor="hand2",
                      command=cmd).pack(side="left", padx=3, anchor="s")

        self.desenhar_tela()

    def botao_tecla(self, pai, texto):
        return tk.Button(pai, text=texto, width=4, height=2, bg="#111111", fg="white",
                         activebackground="#444444", activeforeground="white",
                         font=(FONTE, 14, "bold"), relief="raised", bd=2, cursor="hand2",
                         command=lambda: self.digitar(texto))

    def limpar_tela_urna(self):
        for widget in self.tela.winfo_children():
            widget.destroy()

    def rotulo_tela(self, texto, tamanho=12, negrito=False, **kw):
        fonte = (FONTE, tamanho, "bold") if negrito else (FONTE, tamanho)
        return tk.Label(self.tela, text=texto, bg=COR_TELA, font=fonte, **kw)

    def desenhar_tela(self, mensagem_final=None):
        """Redesenha o visor da urna de acordo com o estado atual."""
        self.limpar_tela_urna()

        if mensagem_final:
            self.rotulo_tela(mensagem_final, 64, True, fg="#333").pack(expand=True)
            return

        if self.eleitor_atual is None:
            self.rotulo_tela("URNA BLOQUEADA", 26, True, fg="#888").pack(expand=True, pady=(40, 0))
            self.rotulo_tela("Aguardando o mesário liberar o próximo eleitor",
                             12, fg="#888").pack(expand=True, pady=(0, 40))
            return

        self.rotulo_tela("SEU VOTO PARA", 11).pack(anchor="w", padx=16, pady=(14, 0))
        self.rotulo_tela("PREFEITO", 22, True).pack(pady=(4, 10))

        linha = tk.Frame(self.tela, bg=COR_TELA)
        linha.pack(anchor="w", padx=16)
        tk.Label(linha, text="Número:", bg=COR_TELA, font=(FONTE, 12)).pack(side="left")
        for i in range(2):
            digito = self.digitos[i] if i < len(self.digitos) else ""
            tk.Label(linha, text=digito, width=2, bg="white", font=(FONTE, 26, "bold"),
                     relief="solid", bd=1).pack(side="left", padx=4)

        info = tk.Frame(self.tela, bg=COR_TELA)
        info.pack(fill="x", padx=16, pady=14)

        if self.voto_branco:
            tk.Label(info, text="VOTO EM BRANCO", bg=COR_TELA, fg="#1f3b63",
                     font=(FONTE, 22, "bold")).pack(pady=10)
        elif len(self.digitos) == 2:
            candidato = self.conexao.execute(
                "SELECT nome, partido FROM candidatos WHERE numero = ?",
                (int(self.digitos),)).fetchone()
            if candidato:
                tk.Label(info, text=f"Nome:     {candidato[0]}", bg=COR_TELA,
                         font=(FONTE, 14)).pack(anchor="w")
                tk.Label(info, text=f"Partido:  {candidato[1]}", bg=COR_TELA,
                         font=(FONTE, 14)).pack(anchor="w")
            else:
                tk.Label(info, text="NÚMERO ERRADO", bg=COR_TELA, fg="#b3261e",
                         font=(FONTE, 16, "bold")).pack(anchor="w")
                tk.Label(info, text="VOTO NULO", bg=COR_TELA, fg="#b3261e",
                         font=(FONTE, 22, "bold")).pack(anchor="w")

        tk.Label(self.tela, text=f"Eleitor(a): {self.eleitor_atual[1]}", bg=COR_TELA,
                 fg="#555", font=(FONTE, 10)).pack(side="bottom", anchor="w", padx=16, pady=(0, 10))
        if self.voto_branco or len(self.digitos) == 2:
            rodape = tk.Frame(self.tela, bg=COR_TELA)
            rodape.pack(side="bottom", fill="x", padx=16, pady=6)
            tk.Frame(rodape, bg="#999", height=1).pack(fill="x", pady=(0, 6))
            tk.Label(rodape, text="Aperte a tecla:", bg=COR_TELA,
                     font=(FONTE, 10)).pack(anchor="w")
            tk.Label(rodape, text="   CONFIRMA para CONFIRMAR este voto", bg=COR_TELA,
                     fg=COR_CONFIRMA, font=(FONTE, 10, "bold")).pack(anchor="w")
            tk.Label(rodape, text="   CORRIGE para REINICIAR este voto", bg=COR_TELA,
                     fg=COR_CORRIGE, font=(FONTE, 10, "bold")).pack(anchor="w")

    # ------------------------------------------------------------ acoes da urna
    def liberar_urna(self):
        if self.eleitor_atual is not None:
            return
        titulo_eleitor = self.var_titulo_voto.get().strip()
        if not titulo_eleitor:
            self.status("Digite o título do eleitor.", erro=True)
            return
        eleitor = self.conexao.execute("SELECT nome, ja_votou FROM eleitores WHERE titulo = ?",
                                       (titulo_eleitor,)).fetchone()
        if eleitor is None:
            self.status("Eleitor não encontrado.", erro=True)
            return
        nome, ja_votou = eleitor
        if ja_votou:
            self.status(f"{nome} já votou! Cada eleitor só pode votar uma vez.", erro=True)
            self.bell()
            return
        if self.conexao.execute("SELECT COUNT(*) FROM candidatos").fetchone()[0] == 0:
            self.status("Cadastre ao menos um candidato antes de votar.", erro=True)
            return

        self.eleitor_atual = (titulo_eleitor, nome)
        self.digitos, self.voto_branco = "", False
        self.ent_titulo_voto.configure(state="disabled")
        self.btn_liberar.configure(state="disabled")
        self.btn_cancelar.configure(state="normal")
        self.status(f"Urna liberada para {nome}.")
        self.focus_set()
        self.desenhar_tela()

    def cancelar_eleitor(self):
        self.status("Votação do eleitor cancelada (nenhum voto registrado).")
        self.bloquear_urna()

    def bloquear_urna(self):
        self.eleitor_atual = None
        self.digitos, self.voto_branco = "", False
        self.ent_titulo_voto.configure(state="normal")
        self.btn_liberar.configure(state="normal")
        self.btn_cancelar.configure(state="disabled")
        self.var_titulo_voto.set("")
        self.ent_titulo_voto.focus_set()
        self.desenhar_tela()

    def digitar(self, digito):
        if self.eleitor_atual is None or self.voto_branco or len(self.digitos) >= 2:
            return
        self.digitos += digito
        self.desenhar_tela()

    def votar_branco(self):
        # Como na urna real: branco so pode ser escolhido antes de digitar numeros.
        if self.eleitor_atual is None:
            return
        if self.digitos:
            self.status("Para votar em branco, aperte CORRIGE antes.", erro=True)
            return
        self.voto_branco = True
        self.desenhar_tela()

    def corrigir(self):
        if self.eleitor_atual is None:
            return
        self.digitos, self.voto_branco = "", False
        self.desenhar_tela()

    def confirmar(self):
        if self.eleitor_atual is None:
            return
        if self.voto_branco:
            tipo, numero = "BRANCO", None
        elif len(self.digitos) == 2:
            existe = self.conexao.execute("SELECT 1 FROM candidatos WHERE numero = ?",
                                          (int(self.digitos),)).fetchone()
            tipo, numero = ("VALIDO", int(self.digitos)) if existe else ("NULO", None)
        else:
            self.bell()
            return

        titulo_eleitor, nome = self.eleitor_atual
        # Marca o eleitor e grava o voto na mesma transacao:
        # ou as duas coisas acontecem, ou nenhuma acontece.
        with self.conexao:
            self.conexao.execute("UPDATE eleitores SET ja_votou = 1 WHERE titulo = ?",
                                 (titulo_eleitor,))
            self.conexao.execute("INSERT INTO votos (numero_candidato, tipo) VALUES (?, ?)",
                                 (numero, tipo))

        self.votos_sessao += 1
        self.bell()
        self.eleitor_atual = ("", "")   # trava o teclado enquanto mostra o FIM
        self.desenhar_tela(mensagem_final="FIM")
        self.status(f"Voto de {nome} registrado com sucesso.")
        self.atualizar_contador()
        self.after(1500, self.bloquear_urna)

    def tecla_fisica(self, evento):
        """Permite votar pelo teclado do computador quando a urna esta liberada."""
        if self.abas.index("current") != 0 or not self.eleitor_atual or not self.eleitor_atual[0]:
            return
        if evento.char.isdigit():
            self.digitar(evento.char)
        elif evento.char.upper() == "B":
            self.votar_branco()
        elif evento.keysym == "BackSpace":
            self.corrigir()
        elif evento.keysym in ("Return", "KP_Enter"):
            self.confirmar()

    def status(self, texto, erro=False):
        self.lbl_status.configure(text=texto, fg="#b3261e" if erro else "#1f6f35")

    def atualizar_contador(self):
        total = self.conexao.execute("SELECT COUNT(*) FROM votos").fetchone()[0]
        aptos = self.conexao.execute(
            "SELECT COUNT(*) FROM eleitores WHERE ja_votou = 0").fetchone()[0]
        self.lbl_contador.configure(text=f"Votos na urna: {total}  (mínimo {MINIMO_VOTOS})")
        self.barra_progresso["value"] = min(total, MINIMO_VOTOS)
        self.lbl_aptos.configure(text=f"Eleitores que ainda não votaram: {aptos}")

    # ================================================================ CRUD (formularios)
    def criar_formulario(self, aba, titulo_quadro, campos, botoes):
        """Monta o formulario lateral. campos = [(rotulo, StringVar, largura)]."""
        quadro = ttk.LabelFrame(aba, text=titulo_quadro, padding=12)
        quadro.pack(side="left", fill="y", padx=(0, 12))
        entradas = []
        for rotulo, var, largura in campos:
            ttk.Label(quadro, text=rotulo).pack(anchor="w")
            entrada = ttk.Entry(quadro, textvariable=var, width=largura, font=(FONTE, 11))
            entrada.pack(fill="x", pady=(2, 10))
            entradas.append(entrada)
        for texto, comando, estilo in botoes:
            ttk.Button(quadro, text=texto, command=comando,
                       style=estilo).pack(fill="x", pady=3)
        return quadro, entradas

    def criar_tabela(self, aba, colunas):
        """colunas = [(id, titulo, largura)]"""
        quadro = ttk.Frame(aba)
        quadro.pack(side="left", fill="both", expand=True)
        tabela = ttk.Treeview(quadro, columns=[c[0] for c in colunas], show="headings",
                              selectmode="browse")
        for ident, titulo_col, largura in colunas:
            tabela.heading(ident, text=titulo_col)
            tabela.column(ident, width=largura, anchor="w")
        rolagem = ttk.Scrollbar(quadro, orient="vertical", command=tabela.yview)
        tabela.configure(yscrollcommand=rolagem.set)
        tabela.pack(side="left", fill="both", expand=True)
        rolagem.pack(side="right", fill="y")
        tabela.tag_configure("par", background="#f5f7fa")
        return tabela

    # ================================================================ CANDIDATOS
    def criar_aba_candidatos(self):
        aba = ttk.Frame(self.abas, padding=12)
        self.abas.add(aba, text="  Candidatos  ")
        self.var_cand_numero = tk.StringVar()
        self.var_cand_nome = tk.StringVar()
        self.var_cand_partido = tk.StringVar()

        quadro, entradas = self.criar_formulario(
            aba, "Dados do candidato",
            [("Número (2 dígitos):", self.var_cand_numero, 10),
             ("Nome:", self.var_cand_nome, 28),
             ("Partido:", self.var_cand_partido, 10)],
            [("Cadastrar", self.cadastrar_candidato, "TButton"),
             ("Alterar", self.alterar_candidato, "TButton"),
             ("Excluir", self.excluir_candidato, "Perigo.TButton"),
             ("Limpar campos", self.limpar_candidato, "TButton")])
        self.ent_cand_numero = entradas[0]
        ttk.Label(quadro, text="Clique em um candidato da lista\npara alterar ou excluir.",
                  foreground="#666").pack(anchor="w", pady=(12, 0))

        self.tab_candidatos = self.criar_tabela(
            aba, [("numero", "Número", 80), ("nome", "Nome", 260), ("partido", "Partido", 100)])
        self.tab_candidatos.bind("<<TreeviewSelect>>", self.selecionar_candidato)

    def carregar_candidatos(self):
        self.tab_candidatos.delete(*self.tab_candidatos.get_children())
        linhas = self.conexao.execute(
            "SELECT numero, nome, partido FROM candidatos ORDER BY numero").fetchall()
        for i, (numero, nome, partido) in enumerate(linhas):
            self.tab_candidatos.insert("", "end", iid=str(numero),
                                       values=(f"{numero:02d}", nome, partido),
                                       tags=("par",) if i % 2 else ())

    def selecionar_candidato(self, _evento=None):
        selecao = self.tab_candidatos.selection()
        if not selecao:
            return
        numero, nome, partido = self.tab_candidatos.item(selecao[0], "values")
        self.var_cand_numero.set(numero)
        self.var_cand_nome.set(nome)
        self.var_cand_partido.set(partido)

    def limpar_candidato(self):
        for var in (self.var_cand_numero, self.var_cand_nome, self.var_cand_partido):
            var.set("")
        self.tab_candidatos.selection_remove(self.tab_candidatos.selection())
        self.ent_cand_numero.focus_set()

    def ler_candidato(self, exigir_dados=True):
        numero = self.var_cand_numero.get().strip()
        nome = self.var_cand_nome.get().strip()
        partido = self.var_cand_partido.get().strip().upper()
        if not (numero.isdigit() and len(numero) == 2):
            messagebox.showwarning("Candidato", "O número deve ter exatamente 2 dígitos.")
            return None
        if exigir_dados and (not nome or not partido):
            messagebox.showwarning("Candidato", "Nome e partido são obrigatórios.")
            return None
        return int(numero), nome, partido

    def cadastrar_candidato(self):
        dados = self.ler_candidato()
        if dados is None:
            return
        try:
            with self.conexao:
                self.conexao.execute(
                    "INSERT INTO candidatos (numero, nome, partido) VALUES (?, ?, ?)", dados)
        except sqlite3.IntegrityError:
            messagebox.showerror("Candidato", "Já existe um candidato com esse número.")
            return
        messagebox.showinfo("Candidato", f"Candidato {dados[1]} cadastrado!")
        self.limpar_candidato()
        self.atualizar_tudo()

    def alterar_candidato(self):
        dados = self.ler_candidato()
        if dados is None:
            return
        numero, nome, partido = dados
        with self.conexao:
            cursor = self.conexao.execute(
                "UPDATE candidatos SET nome = ?, partido = ? WHERE numero = ?",
                (nome, partido, numero))
        if cursor.rowcount == 0:
            messagebox.showerror("Candidato", "Candidato não encontrado.\n"
                                 "(O número identifica o candidato e não pode ser alterado.)")
            return
        messagebox.showinfo("Candidato", f"Candidato {numero:02d} atualizado.")
        self.limpar_candidato()
        self.atualizar_tudo()

    def excluir_candidato(self):
        dados = self.ler_candidato(exigir_dados=False)
        if dados is None:
            return
        numero = dados[0]
        if not messagebox.askyesno("Excluir candidato",
                                   f"Tem certeza que deseja excluir o candidato {numero:02d}?"):
            return
        try:
            with self.conexao:
                cursor = self.conexao.execute("DELETE FROM candidatos WHERE numero = ?",
                                              (numero,))
        except sqlite3.IntegrityError:
            # A chave estrangeira em votos impede apagar quem ja recebeu votos.
            messagebox.showerror("Excluir candidato",
                                 "Esse candidato já recebeu votos e não pode ser excluído.\n"
                                 "Para excluí-lo, zere a urna primeiro (aba Apuração).")
            return
        if cursor.rowcount == 0:
            messagebox.showerror("Excluir candidato", "Candidato não encontrado.")
            return
        messagebox.showinfo("Excluir candidato", "Candidato excluído.")
        self.limpar_candidato()
        self.atualizar_tudo()

    # ================================================================ ELEITORES
    def criar_aba_eleitores(self):
        aba = ttk.Frame(self.abas, padding=12)
        self.abas.add(aba, text="  Eleitores  ")
        self.var_ele_titulo = tk.StringVar()
        self.var_ele_nome = tk.StringVar()

        quadro, entradas = self.criar_formulario(
            aba, "Dados do eleitor",
            [("Título de eleitor:", self.var_ele_titulo, 16),
             ("Nome:", self.var_ele_nome, 28)],
            [("Cadastrar", self.cadastrar_eleitor, "TButton"),
             ("Alterar", self.alterar_eleitor, "TButton"),
             ("Excluir", self.excluir_eleitor, "Perigo.TButton"),
             ("Limpar campos", self.limpar_eleitor, "TButton")])
        self.ent_ele_titulo = entradas[0]
        ttk.Label(quadro, text="Clique em um eleitor da lista\npara alterar ou excluir.",
                  foreground="#666").pack(anchor="w", pady=(12, 0))

        self.tab_eleitores = self.criar_tabela(
            aba, [("titulo", "Título", 110), ("nome", "Nome", 260), ("situacao", "Situação", 110)])
        self.tab_eleitores.tag_configure("votou", foreground="#1f6f35")
        self.tab_eleitores.bind("<<TreeviewSelect>>", self.selecionar_eleitor)

    def carregar_eleitores(self):
        self.tab_eleitores.delete(*self.tab_eleitores.get_children())
        linhas = self.conexao.execute(
            "SELECT titulo, nome, ja_votou FROM eleitores ORDER BY nome").fetchall()
        for i, (tit, nome, votou) in enumerate(linhas):
            tags = ["par"] if i % 2 else []
            if votou:
                tags.append("votou")
            self.tab_eleitores.insert("", "end", iid=tit,
                                      values=(tit, nome, "✔ Já votou" if votou else "Apto"),
                                      tags=tags)

    def selecionar_eleitor(self, _evento=None):
        selecao = self.tab_eleitores.selection()
        if not selecao:
            return
        tit, nome, _ = self.tab_eleitores.item(selecao[0], "values")
        self.var_ele_titulo.set(tit)
        self.var_ele_nome.set(nome)

    def limpar_eleitor(self):
        self.var_ele_titulo.set("")
        self.var_ele_nome.set("")
        self.tab_eleitores.selection_remove(self.tab_eleitores.selection())
        self.ent_ele_titulo.focus_set()

    def ler_eleitor(self, exigir_nome=True):
        tit = self.var_ele_titulo.get().strip()
        nome = self.var_ele_nome.get().strip()
        if not tit.isdigit():
            messagebox.showwarning("Eleitor", "O título deve conter apenas números.")
            return None
        if exigir_nome and not nome:
            messagebox.showwarning("Eleitor", "O nome é obrigatório.")
            return None
        return tit, nome

    def cadastrar_eleitor(self):
        dados = self.ler_eleitor()
        if dados is None:
            return
        try:
            with self.conexao:
                self.conexao.execute("INSERT INTO eleitores (titulo, nome) VALUES (?, ?)", dados)
        except sqlite3.IntegrityError:
            messagebox.showerror("Eleitor", "Esse título já está cadastrado.")
            return
        messagebox.showinfo("Eleitor", f"Eleitor(a) {dados[1]} cadastrado(a)!")
        self.limpar_eleitor()
        self.atualizar_tudo()

    def alterar_eleitor(self):
        dados = self.ler_eleitor()
        if dados is None:
            return
        tit, nome = dados
        with self.conexao:
            cursor = self.conexao.execute("UPDATE eleitores SET nome = ? WHERE titulo = ?",
                                          (nome, tit))
        if cursor.rowcount == 0:
            messagebox.showerror("Eleitor", "Eleitor não encontrado.\n"
                                 "(O título identifica o eleitor e não pode ser alterado.)")
            return
        messagebox.showinfo("Eleitor", f"Eleitor {tit} atualizado.")
        self.limpar_eleitor()
        self.atualizar_tudo()

    def excluir_eleitor(self):
        dados = self.ler_eleitor(exigir_nome=False)
        if dados is None:
            return
        tit = dados[0]
        eleitor = self.conexao.execute("SELECT nome, ja_votou FROM eleitores WHERE titulo = ?",
                                       (tit,)).fetchone()
        if eleitor is None:
            messagebox.showerror("Excluir eleitor", "Eleitor não encontrado.")
            return
        nome, ja_votou = eleitor
        if ja_votou:
            # Se apagasse, o mesmo titulo poderia ser cadastrado de novo e votar duas vezes.
            messagebox.showerror("Excluir eleitor",
                                 f"{nome} já votou e não pode ser excluído(a).\n"
                                 "Isso garante a integridade da eleição.")
            return
        if not messagebox.askyesno("Excluir eleitor", f"Tem certeza que deseja excluir {nome}?"):
            return
        with self.conexao:
            self.conexao.execute("DELETE FROM eleitores WHERE titulo = ?", (tit,))
        messagebox.showinfo("Excluir eleitor", f"{nome} excluído(a).")
        self.limpar_eleitor()
        self.atualizar_tudo()

    # ================================================================ APURACAO
    def criar_aba_apuracao(self):
        aba = ttk.Frame(self.abas, padding=12)
        self.abas.add(aba, text="  Apuração  ")

        barra = ttk.Frame(aba)
        barra.pack(fill="x")
        ttk.Button(barra, text="Atualizar", command=self.atualizar_tudo).pack(side="left")
        ttk.Button(barra, text="Carregar dados de exemplo",
                   command=self.carregar_exemplo).pack(side="left", padx=6)
        ttk.Button(barra, text="Zerar urna", style="Perigo.TButton",
                   command=self.zerar_urna).pack(side="right")

        self.lbl_resumo = ttk.Label(aba, text="", font=(FONTE, 11))
        self.lbl_resumo.pack(anchor="w", pady=(12, 6))

        self.grafico = tk.Canvas(aba, bg="white", highlightthickness=1,
                                 highlightbackground="#cfd6df")
        self.grafico.pack(fill="both", expand=True)
        self.grafico.bind("<Configure>", lambda e: self.desenhar_apuracao())

        self.lbl_situacao = tk.Label(aba, text="", bg=COR_FUNDO, font=(FONTE, 15, "bold"),
                                     fg=COR_TOPO, pady=10)
        self.lbl_situacao.pack(fill="x")

    def desenhar_apuracao(self):
        c = self.grafico
        c.delete("all")
        r = calcular_resultado(self.conexao)

        if r["total"] < MINIMO_VOTOS:
            self.lbl_resumo.configure(text=f"Votos registrados: {r['total']}")
            self.lbl_situacao.configure(
                text=f"A apuração é liberada depois de {MINIMO_VOTOS} votos "
                     f"(faltam {MINIMO_VOTOS - r['total']}).", fg="#888")
            c.create_text(c.winfo_width() / 2, c.winfo_height() / 2,
                          text="Aguardando o mínimo de votos...",
                          font=(FONTE, 16), fill="#aaaaaa")
            return

        self.lbl_resumo.configure(
            text=f"Total: {r['total']}   •   Válidos: {r['validos']}   •   "
                 f"Brancos: {r['brancos']}   •   Nulos: {r['nulos']}")
        eleito = r["situacao"].startswith("ELEITO")
        self.lbl_situacao.configure(text=r["situacao"], fg=COR_CONFIRMA if eleito else COR_TOPO)

        largura = max(c.winfo_width(), 400)
        x_barra, margem_dir = 230, 150
        espaco = largura - x_barra - margem_dir
        y = 30
        for i, (numero, nome, partido, qtd) in enumerate(r["candidatos"]):
            perc = qtd / r["validos"] * 100 if r["validos"] else 0
            cor = CORES_BARRAS[i % len(CORES_BARRAS)]
            c.create_text(20, y + 14, anchor="w", text=f"{numero:02d}  {nome}",
                          font=(FONTE, 11, "bold"))
            c.create_text(20, y + 32, anchor="w", text=partido, font=(FONTE, 9), fill="#666")
            c.create_rectangle(x_barra, y + 6, x_barra + espaco, y + 34,
                               fill="#eef1f5", outline="")
            c.create_rectangle(x_barra, y + 6, x_barra + espaco * perc / 100, y + 34,
                               fill=cor, outline="")
            c.create_text(x_barra + espaco + 12, y + 20, anchor="w",
                          text=f"{qtd} votos  ({perc:.1f}%)", font=(FONTE, 11))
            y += 56

        # linha dos 50% (maioria absoluta)
        x50 = x_barra + espaco / 2
        c.create_line(x50, 20, x50, y, dash=(4, 3), fill="#b3261e")
        c.create_text(x50, y + 10, text="50% dos válidos", fill="#b3261e", font=(FONTE, 9))

    def carregar_exemplo(self):
        candidatos = [(10, "Ana Souza", "PTA"), (25, "Bruno Lima", "PTB"),
                      (40, "Carla Mendes", "PTC")]
        eleitores = [(str(1000 + i), f"Eleitor {i}") for i in range(1, 13)]
        with self.conexao:
            self.conexao.executemany("INSERT OR IGNORE INTO candidatos VALUES (?, ?, ?)",
                                     candidatos)
            self.conexao.executemany("INSERT OR IGNORE INTO eleitores (titulo, nome) VALUES (?, ?)",
                                     eleitores)
        self.atualizar_tudo()
        messagebox.showinfo("Dados de exemplo",
                            "Carregados 3 candidatos (10, 25, 40)\n"
                            "e 12 eleitores (títulos 1001 a 1012).")

    def zerar_urna(self):
        if not messagebox.askyesno("Zerar urna",
                                   "Apagar todos os votos e liberar os eleitores para votar de novo?"):
            return
        with self.conexao:
            self.conexao.execute("DELETE FROM votos")
            self.conexao.execute("UPDATE eleitores SET ja_votou = 0")
        self.votos_sessao = 0
        self.atualizar_tudo()
        messagebox.showinfo("Zerar urna", "Urna zerada.")

    def sair(self):
        self.conexao.close()
        self.destroy()


if __name__ == "__main__":
    UrnaApp().mainloop()
