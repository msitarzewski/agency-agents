"use server";

import { query } from "@/lib/db";
import { revalidatePath } from "next/cache";

export async function getEstates(searchParams?: { search?: string }) {
  let sql = `
    SELECT 
      e.id, e.name, e.region, e.description,
      e.created_at, e.updated_at,
      c.name as client_name, c.id as client_id,
      COUNT(DISTINCT s.id) as sites_count
    FROM estates e
    JOIN clients c ON c.id = e.client_id
    LEFT JOIN sites s ON s.estate_id = e.id
    WHERE 1=1
  `;
  const params: any[] = [];
  
  if (searchParams?.search) {
    params.push(`%${searchParams.search}%`);
    sql += ` AND (e.name ILIKE $${params.length} OR c.name ILIKE $${params.length})`;
  }
  
  sql += ` GROUP BY e.id, c.name, c.id ORDER BY e.name ASC`;

  const { rows } = await query(sql, params);
  return rows;
}

export async function getEstateById(id: string) {
  const { rows } = await query(`SELECT * FROM estates WHERE id = $1`, [id]);
  return rows[0] || null;
}

export async function getClientsForSelect() {
  const { rows } = await query(`SELECT id, name FROM clients ORDER BY name ASC`);
  return rows;
}

export async function createEstate(formData: FormData) {
  const name = formData.get("name") as string;
  const clientId = formData.get("clientId") as string;
  const region = formData.get("region") as string;
  const description = formData.get("description") as string;
  
  const { rows } = await query(
    `INSERT INTO estates (name, client_id, region, description) 
     VALUES ($1, $2, $3, $4) RETURNING id`,
    [name, clientId, region, description]
  );
  
  revalidatePath("/estates");
  return rows[0].id;
}

export async function updateEstate(id: string, formData: FormData) {
  const name = formData.get("name") as string;
  const clientId = formData.get("clientId") as string;
  const region = formData.get("region") as string;
  const description = formData.get("description") as string;
  
  await query(
    `UPDATE estates 
     SET name = $1, client_id = $2, region = $3, description = $4, updated_at = NOW()
     WHERE id = $5`,
    [name, clientId, region, description, id]
  );
  
  revalidatePath("/estates");
  revalidatePath(`/estates/${id}/edit`);
}

export async function deleteEstate(id: string) {
  await query(`DELETE FROM estates WHERE id = $1`, [id]);
  revalidatePath("/estates");
}
