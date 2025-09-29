-- Migration tracker table to keep track of applied migrations
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at INTEGER DEFAULT (strftime('%s', 'now') * 1000),
    description TEXT
);