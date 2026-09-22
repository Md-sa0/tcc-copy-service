BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE products (
    id UUID NOT NULL, 
    sku VARCHAR(64) NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    category VARCHAR(100) NOT NULL, 
    target_audience VARCHAR(500) NOT NULL, 
    technical_attributes JSONB NOT NULL, 
    key_benefits JSONB NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_products_sku ON products (sku);

CREATE TABLE generated_copies (
    id UUID NOT NULL, 
    product_id UUID NOT NULL, 
    input_hash VARCHAR(64) NOT NULL, 
    tone_of_voice VARCHAR(30) NOT NULL, 
    input_snapshot JSONB NOT NULL, 
    instagram_copy JSONB NOT NULL, 
    whatsapp_copy JSONB NOT NULL, 
    seo_copy JSONB NOT NULL, 
    model_name VARCHAR(100) NOT NULL, 
    inference_time_ms FLOAT NOT NULL, 
    tokens_used INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE
);

CREATE INDEX ix_generated_copies_product_id ON generated_copies (product_id);

CREATE INDEX ix_generated_copies_input_hash ON generated_copies (input_hash);

CREATE INDEX ix_copies_product_created ON generated_copies (product_id, created_at);

CREATE TABLE api_metrics (
    id UUID NOT NULL, 
    request_id VARCHAR(36) NOT NULL, 
    path VARCHAR(300) NOT NULL, 
    method VARCHAR(10) NOT NULL, 
    kind VARCHAR(20) NOT NULL, 
    latency_ms FLOAT NOT NULL, 
    cache_status VARCHAR(10) NOT NULL, 
    status_code INTEGER NOT NULL, 
    input_hash VARCHAR(64), 
    model_name VARCHAR(100), 
    tokens_used INTEGER NOT NULL, 
    tokens_saved INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_api_metrics_request_id ON api_metrics (request_id);

CREATE INDEX ix_metrics_created_kind ON api_metrics (created_at, kind);

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

COMMIT;

