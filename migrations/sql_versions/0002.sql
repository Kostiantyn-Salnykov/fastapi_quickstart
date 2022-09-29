-- Running upgrade 0001 -> 0002

CREATE TABLE to_do (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    title VARCHAR(128) NOT NULL, 
    description VARCHAR(256), 
    status VARCHAR(32) NOT NULL, 
    CONSTRAINT pk_to_do PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_to_do_title ON to_do (title);

UPDATE alembic_version SET version_num='0002' WHERE alembic_version.version_num = '0001';

