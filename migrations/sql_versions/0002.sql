-- Running upgrade 0001 -> 0002

CREATE TABLE "group" (
    id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    name VARCHAR(256) NOT NULL,
    CONSTRAINT pk_group PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_group_name ON "group" (name);

CREATE TABLE permission (
    id UUID  NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    object_name VARCHAR(128) NOT NULL, 
    action VARCHAR(32) NOT NULL, 
    CONSTRAINT pk_permission PRIMARY KEY (id), 
    CONSTRAINT uq_permission_object_name UNIQUE (object_name, action)
);

CREATE TABLE role (
    id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    name VARCHAR(128) NOT NULL, 
    CONSTRAINT pk_role PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_role_name ON role (name);

CREATE TABLE "user" (
    id UUID NOT NULL,
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

CREATE TABLE group_role (
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    group_id UUID NOT NULL, 
    role_id UUID NOT NULL, 
    CONSTRAINT pk_group_role PRIMARY KEY (group_id, role_id), 
    CONSTRAINT fk_group_role_group_id_group FOREIGN KEY(group_id) REFERENCES "group" (id) ON DELETE CASCADE ON UPDATE CASCADE, 
    CONSTRAINT fk_group_role_role_id_role FOREIGN KEY(role_id) REFERENCES role (id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE group_user (
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    group_id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    CONSTRAINT pk_group_user PRIMARY KEY (group_id, user_id), 
    CONSTRAINT fk_group_user_group_id_group FOREIGN KEY(group_id) REFERENCES "group" (id) ON DELETE CASCADE ON UPDATE CASCADE, 
    CONSTRAINT fk_group_user_user_id_user FOREIGN KEY(user_id) REFERENCES "user" (id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE permission_user (
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    permission_id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    CONSTRAINT pk_permission_user PRIMARY KEY (permission_id, user_id), 
    CONSTRAINT fk_permission_user_permission_id_permission FOREIGN KEY(permission_id) REFERENCES permission (id) ON DELETE CASCADE ON UPDATE CASCADE, 
    CONSTRAINT fk_permission_user_user_id_user FOREIGN KEY(user_id) REFERENCES "user" (id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE role_permission (
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    role_id UUID NOT NULL, 
    permission_id UUID NOT NULL, 
    CONSTRAINT pk_role_permission PRIMARY KEY (role_id, permission_id), 
    CONSTRAINT fk_role_permission_permission_id_permission FOREIGN KEY(permission_id) REFERENCES permission (id) ON DELETE CASCADE ON UPDATE CASCADE, 
    CONSTRAINT fk_role_permission_role_id_role FOREIGN KEY(role_id) REFERENCES role (id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE role_user (
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    role_id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    CONSTRAINT pk_role_user PRIMARY KEY (role_id, user_id), 
    CONSTRAINT fk_role_user_role_id_role FOREIGN KEY(role_id) REFERENCES role (id) ON DELETE CASCADE ON UPDATE CASCADE, 
    CONSTRAINT fk_role_user_user_id_user FOREIGN KEY(user_id) REFERENCES "user" (id) ON DELETE CASCADE ON UPDATE CASCADE
);

UPDATE alembic_version SET version_num='0002' WHERE alembic_version.version_num = '0001';

