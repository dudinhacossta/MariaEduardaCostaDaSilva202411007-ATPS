-- Script do banco de dados - Urna Eletronica (SQLite)
-- Pode ser executado no DB Browser for SQLite ou pelo proprio programa (urna.py).

-- Candidatos que concorrem na eleicao
CREATE TABLE IF NOT EXISTS candidatos (
    numero   INTEGER PRIMARY KEY,          -- numero digitado na urna (ex.: 10, 25)
    nome     TEXT    NOT NULL,
    partido  TEXT    NOT NULL
);

-- Eleitores aptos a votar
CREATE TABLE IF NOT EXISTS eleitores (
    titulo    TEXT    PRIMARY KEY,         -- numero do titulo de eleitor
    nome      TEXT    NOT NULL,
    ja_votou  INTEGER NOT NULL DEFAULT 0 CHECK (ja_votou IN (0, 1))
);

-- Votos registrados.
-- O voto NAO guarda o titulo do eleitor: assim o voto continua secreto.
CREATE TABLE IF NOT EXISTS votos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_candidato INTEGER,               -- NULL quando for branco ou nulo
    tipo             TEXT    NOT NULL CHECK (tipo IN ('VALIDO', 'BRANCO', 'NULO')),
    data_hora        TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (numero_candidato) REFERENCES candidatos (numero)
);

-- Consulta de apuracao (exemplo)
-- SELECT c.numero, c.nome, c.partido, COUNT(v.id) AS votos
--   FROM candidatos c
--   LEFT JOIN votos v ON v.numero_candidato = c.numero
--  GROUP BY c.numero
--  ORDER BY votos DESC;
