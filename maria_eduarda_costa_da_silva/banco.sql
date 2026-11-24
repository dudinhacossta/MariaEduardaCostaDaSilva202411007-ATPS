
CREATE TABLE IF NOT EXISTS candidatos (
    numero   INTEGER PRIMARY KEY,        
    nome     TEXT    NOT NULL,
    partido  TEXT    NOT NULL
);


CREATE TABLE IF NOT EXISTS eleitores (
    titulo    TEXT    PRIMARY KEY,      
    nome      TEXT    NOT NULL,
    ja_votou  INTEGER NOT NULL DEFAULT 0 CHECK (ja_votou IN (0, 1))
);


CREATE TABLE IF NOT EXISTS votos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_candidato INTEGER,               -- NULL quando for branco ou nulo
    tipo             TEXT    NOT NULL CHECK (tipo IN ('VALIDO', 'BRANCO', 'NULO')),
    data_hora        TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (numero_candidato) REFERENCES candidatos (numero)
);

