# Roteiro do vídeo (máx. 3 min)

**0:00–0:15 — Apresentação**
"Olá, meu nome é Maria Eduarda Costa da Silva, matrícula 202411007, curso de Análise e Desenvolvimento de Sistemas."

**0:15–2:00 — Código (mostrar no PyCharm)**
1. `banco.sql`: 3 tabelas — candidatos, eleitores (com o campo `ja_votou`) e votos. O voto não guarda o título do eleitor, para manter o voto secreto.
2. `urna.py` → `conectar()`: abre o SQLite e executa o banco.sql criando as tabelas. `calcular_resultado()`: conta os votos com SQL e aplica a regra da maioria absoluta (eleito no 1º turno ou 2º turno), como no texto do TSE.
3. `app.py` (Flask): cada operação do sistema é uma rota.
   - Criação: `POST /api/candidatos` e `/api/eleitores` fazem INSERT com parâmetros `?`; número repetido cai no `IntegrityError`.
   - Alteração: `PUT` faz UPDATE.
   - Exclusão: `DELETE` faz DELETE. Candidato que já recebeu voto não pode ser apagado (a chave estrangeira bloqueia) e eleitor que já votou também não (senão poderia ser recadastrado e votar de novo).
4. `votar()`: o `UPDATE ... WHERE ja_votou = 0` e o INSERT do voto ficam na mesma transação (`with conexao:`), então cada eleitor só vota uma vez.
5. `MINIMO_VOTOS = 10`: a apuração só é liberada depois de 10 votos.
6. `templates/index.html` + `static/app.js`: as telas, que só chamam as rotas do Python.

**2:00–3:00 — Execução (`python app.py`)**
- Apuração → Carregar dados de exemplo.
- Candidatos: cadastrar um candidato novo, clicar nele, alterar o nome e excluir.
- Eleitores: alterar o nome de um eleitor.
- Votação: fazer 10 votos, incluindo 1 branco, 1 nulo, 1 correção e 1 tentativa de votar duas vezes com o mesmo título (mostrar o bloqueio).
- Apuração: mostrar o gráfico e o resultado.
- (se der tempo) Candidatos → excluir o 10: mostrar que é bloqueado porque já tem votos.
