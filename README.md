# Urna Eletrônica — ATPS Tópicos Avançados em ADS e SI

**Aluna:** Maria Eduarda Costa da Silva — **Matrícula:** 202411007

Simulação de urna eletrônica em Python com banco SQLite: cadastro de candidatos e eleitores,
votação (com branco, nulo, CONFIRMA/CORRIGE e bloqueio de voto duplo) e apuração com a regra
da maioria absoluta.

## Requisitos

- Python 3.8+ (só usa a biblioteca padrão — não precisa instalar nada com pip)

## Como executar

```bash
cd maria_eduarda_costa_da_silva
python urna.py
```

O arquivo `urna.db` é criado automaticamente ao lado do `urna.py` a partir do `banco.sql`.

## Roteiro rápido de teste

1. Opção **6** — carrega 3 candidatos (10, 25, 40) e 12 eleitores (títulos 1001 a 1012)
2. Opção **3** — lista candidatos e eleitores
3. Opção **4** — votação (mínimo de 10 votos; `B` = branco, número inexistente = nulo)
4. Opção **5** — apuração
5. Opção **7** — zera a urna para testar de novo

## Estrutura

```
maria_eduarda_costa_da_silva/
  urna.py        # programa principal
  banco.sql      # script de criação das tabelas
  LINK_DO_VIDEO_MARIA_EDUARDA_COSTA_DA_SILVA.txt
roteiro_video.md # roteiro do vídeo de apresentação
```
