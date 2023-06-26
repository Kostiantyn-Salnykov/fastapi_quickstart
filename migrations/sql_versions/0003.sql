-- Running upgrade 0002 -> 0003

CREATE TABLE tag (
    id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    title VARCHAR(64) NOT NULL, 
    CONSTRAINT pk_tag PRIMARY KEY (id)
);

CREATE INDEX ix_tag_title ON tag (title);

CREATE TABLE category (
    id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    title VARCHAR(128) NOT NULL, 
    owner_id UUID NOT NULL, 
    CONSTRAINT pk_category PRIMARY KEY (id), 
    CONSTRAINT fk_category_owner_id_user FOREIGN KEY(owner_id) REFERENCES "user" (id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX ix_category_title ON category (title);

CREATE TABLE wish_list (
    id UUID  NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    title VARCHAR(128) NOT NULL, 
    owner_id UUID NOT NULL, 
    CONSTRAINT pk_wish_list PRIMARY KEY (id), 
    CONSTRAINT fk_wish_list_owner_id_user FOREIGN KEY(owner_id) REFERENCES "user" (id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX ix_wish_list_title ON wish_list (title);

CREATE TABLE wish (
    id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    wishlist_id UUID NOT NULL, 
    category_id UUID, 
    title VARCHAR(128) NOT NULL, 
    description VARCHAR(256), 
    status VARCHAR(32) NOT NULL, 
    complexity VARCHAR(32) NOT NULL, 
    priority SMALLINT NOT NULL, 
    CONSTRAINT pk_wish PRIMARY KEY (id), 
    CONSTRAINT fk_wish_category_id_category FOREIGN KEY(category_id) REFERENCES category (id) ON DELETE CASCADE ON UPDATE CASCADE, 
    CONSTRAINT fk_wish_wishlist_id_wish_list FOREIGN KEY(wishlist_id) REFERENCES wish_list (id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX ix_wish_title ON wish (title);

CREATE TABLE wish_tag (
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    wish_id UUID NOT NULL, 
    tag_id UUID NOT NULL, 
    CONSTRAINT pk_wish_tag PRIMARY KEY (wish_id, tag_id), 
    CONSTRAINT fk_wish_tag_tag_id_tag FOREIGN KEY(tag_id) REFERENCES tag (id) ON DELETE CASCADE ON UPDATE CASCADE, 
    CONSTRAINT fk_wish_tag_wish_id_wish FOREIGN KEY(wish_id) REFERENCES wish (id) ON DELETE CASCADE ON UPDATE CASCADE
);

UPDATE alembic_version SET version_num='0003' WHERE alembic_version.version_num = '0002';

