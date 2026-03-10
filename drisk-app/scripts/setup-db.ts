// scripts/setup-db.ts
import { Pool } from 'pg';
import bcrypt from 'bcryptjs';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/drisk_dev',
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : undefined,
});

async function main() {
  const client = await pool.connect();
  try {
    console.log('Starting DRISK database setup...');
    
    // Enable UUID extension (useful if we want UUIDs instead of serials later, but standard pg serial is fine for MVP too as per spec unless specified) 
    // Spec usually uses uuids for security platforms, let's use standard setup
    await client.query(`CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`);

    // Create Enums
    await client.query(`
      DO $$ BEGIN
        CREATE TYPE user_role AS ENUM ('Administrator', 'Assessor', 'Contract Manager', 'Client Viewer');
      EXCEPTION
        WHEN duplicate_object THEN null;
      END $$;
    `);

    // Create Users Table
    await client.query(`
      CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        role user_role NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        last_login_at TIMESTAMP WITH TIME ZONE
      );
    `);
    
    console.log('Users table ready.');

    // Seed initial users for testing all 4 roles
    // Password for all is "password123"
    const passwordHash = await bcrypt.hash('password123', 10);
    
    // Check if empty
    const { rowCount } = await client.query('SELECT 1 FROM users LIMIT 1');
    if (rowCount === 0) {
      console.log('Seeding initial test users...');
      await client.query(`
        INSERT INTO users (email, password_hash, first_name, last_name, role)
        VALUES 
          ('admin@drisk.app', $1, 'System', 'Admin', 'Administrator'),
          ('assessor@drisk.app', $1, 'Field', 'Assessor', 'Assessor'),
          ('manager@drisk.app', $1, 'Contract', 'Manager', 'Contract Manager'),
          ('client@drisk.app', $1, 'Client', 'Viewer', 'Client Viewer');
      `, [passwordHash]);
      console.log('Seed data inserted.');
    } else {
      console.log('Users table already contains data, skipping seed.');
    }

    console.log('Setup complete!');
  } catch (error) {
    console.error('Error setting up DB:', error);
  } finally {
    client.release();
    pool.end();
  }
}

main();
