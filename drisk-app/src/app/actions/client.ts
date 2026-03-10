"use server";

import { query } from "@/lib/db";
import { revalidatePath } from "next/cache";

export async function getClients(searchParams?: { search?: string; sector?: string }) {
  let sql = `
    SELECT 
      c.id, c.name, c.sector, c.contact_name, c.contact_email, c.contact_phone,
      c.created_at, c.updated_at,
      COUNT(DISTINCT s.id) as sites_count,
      COUNT(DISTINCT a.id) as open_actions_count,
      MAX(asm.completed_at) as latest_assessment_date
    FROM clients c
    LEFT JOIN estates e ON e.client_id = c.id
    LEFT JOIN sites s ON s.estate_id = e.id
    LEFT JOIN actions a ON a.site_id = s.id AND a.status = 'open'
    LEFT JOIN assessments asm ON asm.site_id = s.id AND asm.status = 'completed'
    WHERE 1=1
  `;
  const params: any[] = [];
  
  if (searchParams?.search) {
    params.push(\`%\${searchParams.search}%\`);
    sql += \` AND c.name ILIKE $\${params.length}\`;
  }
  
  if (searchParams?.sector) {
    params.push(searchParams.sector);
    sql += \` AND c.sector = $\${params.length}\`;
  }
  
  sql += \` GROUP BY c.id ORDER BY c.name ASC\`;

  const { rows } = await query(sql, params);
  return rows;
}

export async function getClientById(id: string) {
  const { rows } = await query(\`SELECT * FROM clients WHERE id = $1\`, [id]);
  return rows[0] || null;
}

export async function createClient(formData: FormData) {
  const name = formData.get("name") as string;
  const sector = formData.get("sector") as string;
  const contactName = formData.get("contactName") as string;
  const contactEmail = formData.get("contactEmail") as string;
  const contactPhone = formData.get("contactPhone") as string;
  const riskAppetite = formData.get("riskAppetite") as string;
  
  const { rows } = await query(
    \`INSERT INTO clients (name, sector, contact_name, contact_email, contact_phone, risk_appetite) 
     VALUES ($1, $2, $3, $4, $5, $6) RETURNING id\`,
    [name, sector, contactName, contactEmail, contactPhone, riskAppetite]
  );
  
  revalidatePath("/clients");
  return rows[0].id;
}

export async function updateClient(id: string, formData: FormData) {
  const name = formData.get("name") as string;
  const sector = formData.get("sector") as string;
  const contactName = formData.get("contactName") as string;
  const contactEmail = formData.get("contactEmail") as string;
  const contactPhone = formData.get("contactPhone") as string;
  const riskAppetite = formData.get("riskAppetite") as string;
  
  await query(
    \`UPDATE clients 
     SET name = $1, sector = $2, contact_name = $3, contact_email = $4, contact_phone = $5, risk_appetite = $6, updated_at = NOW()
     WHERE id = $7\`,
    [name, sector, contactName, contactEmail, contactPhone, riskAppetite, id]
  );
  
  revalidatePath("/clients");
  revalidatePath(\`/clients/\${id}/edit\`);
}

export async function deleteClient(id: string) {
  await query(\`DELETE FROM clients WHERE id = $1\`, [id]);
  revalidatePath("/clients");
}
