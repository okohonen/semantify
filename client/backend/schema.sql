CREATE TABLE pages_annotated
(id INTEGER PRIMARY KEY AUTOINCREMENT,
url TEXT,
timestamp DATETIME,
version INT,
is_body BOOLEAN,
model_id INT REFERENCES models(id) ON DELETE CASCADE
-- Same page may be annotated for different model, then different page_id
);

CREATE UNIQUE INDEX pages_annotated_uvm ON pages_annotated (url, version, model_id);

CREATE TABLE pages_unannotated
(id INTEGER PRIMARY KEY AUTOINCREMENT,
url TEXT,
timestamp DATETIME,
version INT,
is_body BOOLEAN);

CREATE UNIQUE INDEX pages_unannotated_uv ON pages_unannotated (url, version);


CREATE TABLE models (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       name VARCHAR(50),
       dtdfile VARCHAR(100));

CREATE UNIQUE INDEX models_n ON models (name);

-- SELECT tt.*, tags.val FROM (SELECT tokens.id AS token_id, GROUP_CONCAT(features.line, '\t') AS f FROM tokens JOIN features ON tokens.id=features.token_id WHERE page_id=1 AND feature_set_id IN (SELECT id FROM feature_sets WHERE name IN('ortho1', 'html')) GROUP BY tokens.id) AS tt JOIN tags ON tags.token_id=tt.token_id WHERE tags.schema_id=1;
