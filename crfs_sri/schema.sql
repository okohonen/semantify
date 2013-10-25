CREATE TABLE schemas
(id INTEGER PRIMARY KEY AUTOINCREMENT,
 name VARCHAR(100));

CREATE TABLE pages
(id INTEGER PRIMARY KEY AUTOINCREMENT,
url TEXT,
body TEXT,
timestamp DATETIME,
version INT,
schema_id INT
);

CREATE UNIQUE INDEX pages_uvs ON pages (url, version, schema_id);

CREATE TABLE tokens
(id INTEGER PRIMARY KEY AUTOINCREMENT,
 page_id INT,
 val VARCHAR(50),
 FOREIGN KEY(page_id) REFERENCES pages(id) ON DELETE CASCADE);

 CREATE TABLE feature_sets
 (id INTEGER PRIMARY KEY AUTOINCREMENT,
 name VARCHAR(100));
 
CREATE TABLE features
(token_id INT,
 line TEXT,
 feature_set_id INT,
 FOREIGN KEY(token_id) REFERENCES tokens(id) ON DELETE CASCADE,
 FOREIGN KEY(feature_set_id) REFERENCES feature_sets(id));
 
 CREATE TABLE tags 
 (schema_id INT,
   token_id INT, 
   val VARCHAR(100),
 FOREIGN KEY(token_id) REFERENCES tokens(id) ON DELETE CASCADE,
 FOREIGN KEY(schema_id) REFERENCES schemas(id));

CREATE TABLE IF NOT EXISTS ortho1html(id INTEGER PRIMARY KEY AUTOINCREMENT, entity, long, brief, iscapital, isnumber, hasnumber, hassplchars,classname, classlong, classbrief, parentname, grandparentname, greatgrandparentname, ancestors, tagsetname, added);

CREATE TABLE IF NOT EXISTS ortho3 (id INTEGER PRIMARY KEY AUTOINCREMENT, entity, longcurrent, briefcurrent, previousterm, longprevious, briefprevious, nextterm, longnext, briefnext,iscapital, isnumber, hasnumber, hassplchars, tagsetname, added);

CREATE TABLE IF NOT EXISTS ortho3html (id INTEGER PRIMARY KEY AUTOINCREMENT, entity, longcurrent, briefcurrent, previousterm, lonprevious, briefprevious, nextterm, longnext, briefnext,iscapital, isnumber, hasnumber, hassplchars, classname, classlong, classbrief, parentname, grandparentname, greatgrandparentname, ancestors,tagsetname, added);

INSERT INTO schemas (id, name) VALUES (1, 'default');
INSERT INTO feature_sets (name) VALUES ('ortho1');
INSERT INTO feature_sets (name) VALUES ('ortho3');
INSERT INTO feature_sets (name) VALUES ('html');


--drop table ortho1html;
--drop table ortho3;
--drop table ortho3html;
--drop table features;
--drop table feature_sets;
--drop table tokens;
--drop table pages;
--drop table tags;

SELECT tt.*, tags.val FROM (SELECT tokens.id AS token_id, GROUP_CONCAT(features.line, '\t') AS f FROM tokens JOIN features ON tokens.id=features.token_id WHERE page_id=1 AND feature_set_id IN (SELECT id FROM feature_sets WHERE name IN('ortho1', 'html')) GROUP BY tokens.id) AS tt JOIN tags ON tags.token_id=tt.token_id WHERE tags.schema_id=1;
