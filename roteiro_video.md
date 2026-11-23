# Roteiro do vídeo (máx. 3 min)

**0:00–0:15 — Apresentação**
"Olá, meu nome é Maria Eduarda Costa da Silva, matrícula 202411007, curso de Análise e Desenvolvimento de Sistemas."

**0:15–2:00 — Código (mostrar no PyCharm)**
1. `banco.sql`: 3 tabelas — candidatos, eleitores (com o campo `ja_votou`) e votos. O voto não guarda o título do eleitor, para manter o voto secreto.
2. `conectar()`: abre o SQLite e executa o banco.sql criando as tabelas.
3. CRUD completo (menus 1 Candidatos e 2 Eleitores):
   - Criação: `cadastrar_candidato` / `cadastrar_eleitor` usam INSERT com parâmetros `?`; número repetido cai no `IntegrityError`.
   - Alteração: `alterar_candidato` / `alterar_eleitor` fazem UPDATE (ENTER mantém o valor atual).
   - Exclusão: `excluir_candidato` / `excluir_eleitor` fazem DELETE com confirmação. Candidato que já recebeu voto não pode ser apagado (a chave estrangeira bloqueia) e eleitor que já votou também não (senão poderia ser recadastrado e votar de novo).
4. `registrar_voto()`: confere se o eleitor existe e se já votou; mostra o candidato, aceita branco (B) e nulo (número inexistente), tem CONFIRMA/CORRIGE.
5. Integridade: o `with conexao:` faz o UPDATE do eleitor e o INSERT do voto na mesma transação.
6. `votacao()`: só deixa encerrar depois de 10 votos (`MINIMO_VOTOS`).
7. `apuracao()`: conta os votos com SQL, mostra porcentagem e barra, e aplica a regra da maioria absoluta (eleito no 1º turno ou 2º turno), como no texto do TSE.

**2:00–3:00 — Execução**
- Opção 6 (dados de exemplo) → opção 3 (listar).
- Opção 1 (Candidatos): cadastrar um candidato novo, alterar o nome dele e excluir.
- Opção 2 (Eleitores): alterar o nome de um eleitor.
- Opção 4: fazer 10 votos, incluindo 1 branco, 1 nulo, 1 correção e 1 tentativa de votar duas vezes com o mesmo título (mostrar o bloqueio).
- Opção 5: mostrar o resultado.
- (se der tempo) Opção 1 → Excluir o candidato 10: mostrar que é bloqueado porque já tem votos.
