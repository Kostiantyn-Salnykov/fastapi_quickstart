CREATE TABLE migrations (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT migrations_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE "user" (
    first_name VARCHAR(128) NOT NULL,
    last_name VARCHAR(128) NOT NULL,
    email VARCHAR(320) NOT NULL,
    password_hash VARCHAR(1024) NOT NULL,
    status VARCHAR(64) NOT NULL,
    settings JSONB NOT NULL,
    id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT pk_user PRIMARY KEY (id)
);

COMMENT ON COLUMN "user".settings IS 'TEST COMMENT.';

CREATE UNIQUE INDEX ix_user_email ON "user" (email);

INSERT INTO migrations (version_num) VALUES ('0001') RETURNING migrations.version_num;
