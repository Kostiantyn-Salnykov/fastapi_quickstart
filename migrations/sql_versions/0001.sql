CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE EXTENSION IF NOT EXISTS pgcrypto;

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

