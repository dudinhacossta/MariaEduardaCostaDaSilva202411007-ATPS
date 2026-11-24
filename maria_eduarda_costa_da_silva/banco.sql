
CREATE DATABASE IF NOT EXISTS urna_eletronica
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE urna_eletronica;


CREATE TABLE IF NOT EXISTS candidatos (
    numero   INT          PRIMARY KEY,
    nome     VARCHAR(100) NOT NULL,
    partido  VARCHAR(20)  NOT NULL
) ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS eleitores (
    titulo    VARCHAR(20)  PRIMARY KEY,
    nome      VARCHAR(100) NOT NULL,
    ja_votou  TINYINT(1)   NOT NULL DEFAULT 0 CHECK (ja_votou IN (0, 1))
) ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS votos (
    id               INT          PRIMARY KEY AUTO_INCREMENT,
    numero_candidato INT          NULL,               -- NULL quando for branco ou nulo
    tipo             ENUM('VALIDO', 'BRANCO', 'NULO') NOT NULL,
    data_hora        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (numero_candidato) REFERENCES candidatos (numero)
) ENGINE = InnoDB;
