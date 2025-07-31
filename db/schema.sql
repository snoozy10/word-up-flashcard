CREATE TABLE IF NOT EXISTS contents (
    id INTEGER PRIMARY KEY,
    de TEXT NOT NULL,
    en TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS decks (
    id INTEGER PRIMARY KEY,
    name TEXT,
    parent_id INTEGER, -- NULL for root
    FOREIGN KEY (parent_id) REFERENCES decks(id)
);

CREATE TABLE IF NOT EXISTS cards (
    id              INTEGER PRIMARY KEY,
    deck_id         INTEGER NOT NULL,
    content_id      INTEGER NOT NULL,
    state           INTEGER NOT NULL,
    step            INTEGER,
    stability       REAL,
    difficulty      REAL,
    due             INTEGER NOT NULL,
    last_review     INTEGER,
    FOREIGN KEY (deck_id) REFERENCES decks (id),
    FOREIGN KEY (content_id) REFERENCES contents (id)
);

CREATE TABLE IF NOT EXISTS revlogs (
    card_id         INTEGER NOT NULL,         -- Foreign key to the 'cards' table (cards.id)
    rating          INTEGER NOT NULL,         -- [og name ease]The recall score (1 = wrong, 2 = hard, 3 = okay, 4 = easy)
    review_datetime INTEGER,      -- Review datetime in epoch milliseconds
    review_duration INTEGER,                  -- Time taken for the review in milliseconds (up to 60000 i.e. 1 minute)
    FOREIGN KEY (card_id) REFERENCES cards (id)
);

CREATE TABLE IF NOT EXISTS metadata (
    id INTEGER PRIMARY KEY,
    last_session_cutoff INTEGER NOT NULL,
    new_cards_reviewed INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_contents_id ON contents (id);
CREATE INDEX IF NOT EXISTS idx_cards_sched ON cards (deck_id, state, due);
CREATE INDEX IF NOT EXISTS idx_revlog_cid on revlogs (card_id);
