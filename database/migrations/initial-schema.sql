CREATE TABLE IF NOT EXISTS fuel_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    supplier_name TEXT NOT NULL,
    supplier_url TEXT,
    price REAL NOT NULL,
    UNIQUE(date, supplier_name)
);
