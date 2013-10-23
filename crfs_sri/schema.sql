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

CREATE TABLE features
(page_id INT,
 line TEXT,
 tag VARCHAR(100),
 feature_set INT,
 schema_id INT,
 FOREIGN KEY(page_id) REFERENCES pages(id),
 FOREIGN KEY(schema_id) REFERENCES schemas(id));

CREATE TABLE IF NOT EXISTS ortho1html(id INTEGER PRIMARY KEY AUTOINCREMENT, entity, long, brief, iscapital, isnumber, hasnumber, hassplchars,classname, classlong, classbrief, parentname, grandparentname, greatgrandparentname, ancestors, tagsetname, added);

CREATE TABLE IF NOT EXISTS ortho3 (id INTEGER PRIMARY KEY AUTOINCREMENT, entity, longcurrent, briefcurrent, previousterm, longprevious, briefprevious, nextterm, longnext, briefnext,iscapital, isnumber, hasnumber, hassplchars, tagsetname, added);

CREATE TABLE IF NOT EXISTS ortho3html (id INTEGER PRIMARY KEY AUTOINCREMENT, entity, longcurrent, briefcurrent, previousterm, lonprevious, briefprevious, nextterm, longnext, briefnext,iscapital, isnumber, hasnumber, hassplchars, classname, classlong, classbrief, parentname, grandparentname, greatgrandparentname, ancestors,tagsetname, added);


