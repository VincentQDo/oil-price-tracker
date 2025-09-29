#!/usr/bin/env node

/**
 * Migration CLI tool
 * Usage:
 *   node scripts/migrate.js                    # Run all pending migrations
 *   node scripts/migrate.js create "add_email" # Create new migration file
 *   node scripts/migrate.js status             # Show migration status
 */

import fs from "fs";
import path from "path";
import sqlite from "sqlite3";
import { MigrationManager } from "../db/migration-manager.js";

const DATA_DIR = process.env.DB_DIR || path.resolve(process.cwd(), "data");
const DB_FILE = path.join(DATA_DIR, "data.db");

// Ensure data directory exists
fs.mkdirSync(DATA_DIR, { recursive: true });

const db = new sqlite.Database(DB_FILE, (err) => {
  if (err) {
    console.error("❌ DB connection error:", err.message);
    process.exit(1);
  }
});

const migrationManager = new MigrationManager(db);

async function showStatus() {
  try {
    await migrationManager.initialize();
    const applied = await migrationManager.getAppliedMigrations();
    const available = migrationManager.getAvailableMigrations();

    console.log('\n📊 Migration Status:\n');

    if (available.length === 0) {
      console.log('No migration files found');
      return;
    }

    available.forEach(migration => {
      const status = applied.includes(migration.version) ? '✅ Applied' : '⏳ Pending';
      console.log(`  ${status}  ${migration.version}`);
    });

    console.log(`\nTotal: ${available.length} migrations, ${applied.length} applied, ${available.length - applied.length} pending\n`);

  } catch (error) {
    console.error('❌ Failed to get migration status:', error);
    process.exit(1);
  }
}

async function runMigrations() {
  try {
    await migrationManager.runMigrations();
  } catch (error) {
    console.error('❌ Migration failed:', error);
    process.exit(1);
  } finally {
    db.close();
  }
}

function createMigration(name) {
  if (!name) {
    console.error('❌ Migration name is required');
    console.log('Usage: node scripts/migrate.js create "migration_name"');
    process.exit(1);
  }

  try {
    const filepath = migrationManager.createMigration(name);
    console.log(`✅ Migration created: ${filepath}`);
    console.log('📝 Edit the file to add your SQL commands');
  } catch (error) {
    console.error('❌ Failed to create migration:', error);
    process.exit(1);
  } finally {
    db.close();
  }
}

// Parse command line arguments
const command = process.argv[2];
const arg = process.argv[3];

switch (command) {
  case 'create':
    createMigration(arg);
    break;
  case 'status':
    showStatus().then(() => db.close());
    break;
  case undefined:
    // Default: run migrations
    runMigrations();
    break;
  default:
    console.log(`
🔧 Database Migration CLI

Usage:
  node scripts/migrate.js                    Run all pending migrations
  node scripts/migrate.js create "name"      Create new migration file
  node scripts/migrate.js status             Show migration status

Examples:
  node scripts/migrate.js
  node scripts/migrate.js create "add_user_email"
  node scripts/migrate.js status
`);
    process.exit(1);
}