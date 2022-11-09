-- Running upgrade 0002 -> 0003

CREATE TABLE "user" (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    first_name VARCHAR(128) NOT NULL, 
    last_name VARCHAR(128) NOT NULL, 
    email VARCHAR(256) NOT NULL, 
    password_hash VARCHAR(1024) NOT NULL, 
    status VARCHAR(64) NOT NULL, 
    CONSTRAINT pk_user PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_user_email ON "user" (email);

UPDATE alembic_version SET version_num='0003' WHERE alembic_version.version_num = '0002';

