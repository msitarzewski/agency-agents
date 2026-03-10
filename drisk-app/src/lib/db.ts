import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/drisk_dev',
  ssl: (process.env.DATABASE_URL || 'localhost').includes('localhost') ? false : (process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : undefined),
});

export const query = async (text: string, params?: any[]) => {
  const start = Date.now();
  const res = await pool.query(text, params);
  const duration = Date.now() - start;
  if (process.env.NODE_ENV === 'development') {
    console.log('Executed query', { text, duration, rows: res.rowCount });
  }
  return res;
};

export const getClient = () => {
  return pool.connect();
};
