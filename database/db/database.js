/** @typedef (import('../types/message.d.js').Message) Message*/

import fs from "fs";
import sqlite from "sqlite3";
import path from "path";
import { MigrationManager } from "./migration-manager.js";

const DATA_DIR = process.env.DB_DIR || path.resolve(process.cwd(), "data");
const DB_FILE = path.join(DATA_DIR, "data.db");
export const MESSAGE_STATUS = Object.freeze({
  SENT: "sent",
  DELIVERED: "delivered",
  READ: "read",
});

// Ensure data directory exists
fs.mkdirSync(DATA_DIR, { recursive: true });

// Create database connection
const db = new sqlite.Database(DB_FILE, (err) => {
  console.log("Trying to access the database at", DB_FILE);
  if (err) {
    console.error("❌ DB connection error:", err.message);
    process.exit(1);
  } else {
    console.log("✅ DB connection established");
  }
});

// Initialize database with migrations
async function initializeDatabase() {
  const migrationManager = new MigrationManager(db);

  try {
    await migrationManager.runMigrations();
  } catch (error) {
    console.error("❌ Database initialization failed:", error);
    process.exit(1);
  }
}

// Run initialization
initializeDatabase();

/**
 * @param {number} [limit] Default to 100 if not provided
 * @param {number} [offset] Default to 0 if not provided
 * @param {string} [supplier] Optional supplier filter
 * @returns {Promise<OilPrice[]>} Promise of oil prices object array
 * */
export function getPrices(limit = 0, offset = 0, supplier) {
  let lim = Number.isSafeInteger(limit) ? Number(limit) : 100;
  lim = Math.min(lim, 200);
  const off = Number.isSafeInteger(offset) ? offset : 0;

  console.log(
    "Fetching oil prices with the following limit and offset:",
    lim,
    off,
  );

  return new Promise((resolve, reject) => {
    const params = [];
    let sql = "SELECT * FROM fuel_prices";
    
    if (supplier) {
      sql += " WHERE supplier_name = ?";
      params.push(supplier);
    }

    sql += " ORDER BY date DESC";

    if (lim > 0) {
      sql += " LIMIT ? OFFSET ?";
      params.push(lim, off);
    }


    db.all(sql, params, (err, rows) => {
      if (err) {
        console.error(err);
        reject(err);
        return;
      }

      const prices = rows || [];
      if (prices.length === 0) {
        resolve([]);
        return;
      }
      resolve(prices);      
    });
  });
}

/**
 * 
 * @param {OilPrice[]} prices 
 * @returns 
 */
export function addPrices(prices) {
  return new Promise((resolve, reject) => {
    const sql =
      "INSERT INTO fuel_prices (date, supplier_name, supplier_url, price) VALUES (?, ?, ?, ?)";

    // Start a transaction for better performance + atomicity
    db.serialize(() => {
      db.run("BEGIN TRANSACTION");

      const stmt = db.prepare(sql);
      for (const { date, supplier_name, supplier_url, price } of prices) {
        stmt.run([date, supplier_name, supplier_url, price]);
      }
      stmt.finalize(err => {
        if (err) {
          db.run("ROLLBACK");
          console.error("Error finalizing statement:", err);
          reject(err);
          return;
        }
        db.run("COMMIT", commitErr => {
          if (commitErr) {
            console.error("Error committing transaction:", commitErr);
            reject(commitErr);
            return;
          }
          resolve(1);
        });
      });
    });
  });
}


// Export the MigrationManager for CLI usage
export { MigrationManager };
export default db;