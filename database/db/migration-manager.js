import fs from "fs";
import path from "path";
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const MIGRATION_TRACKER_SQL_FILE_NAME = 'migration-tracker.sql';

/**
 * Migration manager to handle database schema changes
 */
export class MigrationManager {
  constructor(/** @type {import('sqlite3').Database} */ db) {
    this.db = db;
    this.migrationsDir = path.join(__dirname, '../migrations');
  }

  /**
   * Initialize the migration system by creating the tracker table
   */
  async initialize() {
    return new Promise((resolve, reject) => {
      const trackerSql = fs.readFileSync(
        path.join(this.migrationsDir, MIGRATION_TRACKER_SQL_FILE_NAME),
        'utf8'
      );

      this.db.exec(trackerSql, (err) => {
        if (err) {
          console.error('Failed to initialize migration tracker:', err);
          reject(err);
        } else {
          console.log('Migration tracker initialized');
          resolve();
        }
      });
    });
  }

  /**
   * Get list of applied migrations
   */
  async getAppliedMigrations() {
    return new Promise((resolve, reject) => {
      this.db.all(
        'SELECT version FROM schema_migrations ORDER BY version',
        [],
        (err, rows) => {
          if (err) {
            reject(err);
          } else {
            resolve(rows.map(row => row.version));
          }
        }
      );
    });
  }

  /**
   * Get list of available migration files
   */
  getAvailableMigrations() {
    const files = fs.readdirSync(this.migrationsDir)
      .filter(file => file.endsWith('.sql') && file !== 'migration-tracker.sql')
      .sort();

    return files.map(file => {
      const version = file.replace('.sql', '');
      return {
        version,
        filename: file,
        path: path.join(this.migrationsDir, file)
      };
    });
  }

  /**
   * Apply a single migration
   */
  async applyMigration(migration) {
    return new Promise((resolve, reject) => {
      const sql = fs.readFileSync(migration.path, 'utf8');

      this.db.serialize(() => {
        this.db.exec('BEGIN TRANSACTION');

        this.db.exec(sql, (err) => {
          if (err) {
            console.error(`Failed to apply migration ${migration.version}:`, err);
            this.db.exec('ROLLBACK');
            reject(err);
            return;
          }

          // Record the migration as applied
          this.db.run(
            'INSERT INTO schema_migrations (version, description) VALUES (?, ?)',
            [migration.version, `Migration: ${migration.version}`],
            (err) => {
              if (err) {
                console.error(`Failed to record migration ${migration.version}:`, err);
                this.db.exec('ROLLBACK');
                reject(err);
                return;
              }

              this.db.exec('COMMIT');
              console.log(`✓ Applied migration: ${migration.version}`);
              resolve();
            }
          );
        });
      });
    });
  }

  /**
   * Run all pending migrations
   */
  async runMigrations() {
    try {
      console.log('🚀 Starting database migrations...');

      await this.initialize();
      const appliedMigrations = await this.getAppliedMigrations();
      const availableMigrations = this.getAvailableMigrations();

      const pendingMigrations = availableMigrations.filter(
        migration => !appliedMigrations.includes(migration.version)
      );

      if (pendingMigrations.length === 0) {
        console.log('✓ No pending migrations');
        return;
      }

      console.log(`📋 Found ${pendingMigrations.length} pending migration(s)`);

      for (const migration of pendingMigrations) {
        await this.applyMigration(migration);
      }

      console.log('✅ All migrations completed successfully');

    } catch (error) {
      console.error('❌ Migration failed:', error);
      throw error;
    }
  }

  /**
   * Create a new migration file
   */
  createMigration(name) {
    const timestamp = new Date().toISOString()
      .replace(/[-:]/g, '')
      .replace(/\..+/, '')
      .replace('T', '_');

    const filename = `${timestamp}_${name.replace(/[^a-zA-Z0-9]/g, '_')}.sql`;
    const filepath = path.join(this.migrationsDir, filename);

    const template = `-- Migration: ${filename}
-- Description: ${name}

-- Add your SQL commands here
-- Example:
-- ALTER TABLE users ADD COLUMN email TEXT;

-- Don't forget to add indexes if needed
-- CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
`;

    fs.writeFileSync(filepath, template);
    console.log(`📝 Created migration file: ${filename}`);
    return filepath;
  }
}