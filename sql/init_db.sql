DROP TABLE IF EXISTS chefs;
CREATE TABLE chefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    specialty TEXT NOT NULL,
    years_experience INTEGER NOT NULL CHECK(year >= 1900),
    signature_dishes TEXT NOT NULL,
    age INTEGER NOT NULL CHECK(duration > 0),
    wins INTEGER DEFAULT 0 CHECK (wins >= 0 AND wins <= cookoffs),
    cookoffs INTEGER DEFAULT 0
);

CREATE UNIQUE INDEX idx_chefs_name ON chefs(name);