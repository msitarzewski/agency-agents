"use server";

import { query } from "@/lib/db";
import { revalidatePath } from "next/cache";

export async function getSites(searchParams?: { search?: string; estateId?: string; type?: string }) {
  let sql = `
    SELECT 
      s.id, s.name, s.site_type, s.city, s.country,
      s.created_at, s.updated_at,
      e.name as estate_name, e.id as estate_id,
      c.name as client_name, c.id as client_id
    FROM sites s
    JOIN estates e ON e.id = s.estate_id
    JOIN clients c ON c.id = e.client_id
    WHERE 1=1
  `;
  const params: any[] = [];
  
  if (searchParams?.search) {
    params.push(`%${searchParams.search}%`);
    sql += ` AND (s.name ILIKE $${params.length}`;
    
    params.push(`%${searchParams.search}%`);
    sql += ` OR e.name ILIKE $${params.length}`;
    
    params.push(`%${searchParams.search}%`);
    sql += ` OR c.name ILIKE $${params.length})`;
  }
  
  if (searchParams?.estateId) {
    params.push(searchParams.estateId);
    sql += ` AND s.estate_id = $${params.length}`;
  }

  if (searchParams?.type) {
    params.push(searchParams.type);
    sql += ` AND s.site_type = $${params.length}`;
  }
  
  sql += ` ORDER BY s.name ASC`;

  const { rows } = await query(sql, params);
  return rows;
}

export async function getSiteById(id: string) {
  const { rows } = await query(`
    SELECT s.*, e.client_id, e.name as estate_name, c.name as client_name
    FROM sites s
    JOIN estates e ON e.id = s.estate_id
    JOIN clients c ON c.id = e.client_id
    WHERE s.id = $1
  `, [id]);
  return rows[0] || null;
}

export async function getEstatesForSelect() {
  const { rows } = await query(`
    SELECT e.id, e.name, c.name as client_name 
    FROM estates e
    JOIN clients c ON c.id = e.client_id
    ORDER BY c.name ASC, e.name ASC
  `);
  return rows;
}

export async function createSite(formData: FormData) {
  const name = formData.get("name") as string;
  const estateId = formData.get("estateId") as string;
  const siteType = formData.get("siteType") as string;
  const addressLine1 = formData.get("addressLine1") as string;
  const addressLine2 = formData.get("addressLine2") as string;
  const city = formData.get("city") as string;
  const postcode = formData.get("postcode") as string;
  const country = formData.get("country") as string;
  const latitude = formData.get("latitude") ? parseFloat(formData.get("latitude") as string) : null;
  const longitude = formData.get("longitude") ? parseFloat(formData.get("longitude") as string) : null;
  const operatingHours = formData.get("operatingHours") as string;
  const occupancyProfile = formData.get("occupancyProfile") as string;
  const publicAccessLevel = formData.get("publicAccessLevel") as string;
  const vulnerableOccupants = formData.get("vulnerableOccupants") as string;
  const criticalServices = formData.get("criticalServices") as string;
  
  const { rows } = await query(
    `INSERT INTO sites (
      name, estate_id, site_type, address_line1, address_line2, city, postcode, country, latitude, longitude,
      operating_hours, occupancy_profile, public_access_level, vulnerable_occupants, critical_services
     ) 
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15) RETURNING id`,
    [
      name, estateId, siteType, addressLine1, addressLine2, city, postcode, country, latitude, longitude,
      operatingHours, occupancyProfile, publicAccessLevel, vulnerableOccupants, criticalServices
    ]
  );
  
  revalidatePath("/sites");
  return rows[0].id;
}

export async function updateSite(id: string, formData: FormData) {
  const name = formData.get("name") as string;
  const estateId = formData.get("estateId") as string;
  const siteType = formData.get("siteType") as string;
  const addressLine1 = formData.get("addressLine1") as string;
  const addressLine2 = formData.get("addressLine2") as string;
  const city = formData.get("city") as string;
  const postcode = formData.get("postcode") as string;
  const country = formData.get("country") as string;
  const latitude = formData.get("latitude") ? parseFloat(formData.get("latitude") as string) : null;
  const longitude = formData.get("longitude") ? parseFloat(formData.get("longitude") as string) : null;
  const operatingHours = formData.get("operatingHours") as string;
  const occupancyProfile = formData.get("occupancyProfile") as string;
  const publicAccessLevel = formData.get("publicAccessLevel") as string;
  const vulnerableOccupants = formData.get("vulnerableOccupants") as string;
  const criticalServices = formData.get("criticalServices") as string;
  
  await query(
    `UPDATE sites 
     SET name = $1, estate_id = $2, site_type = $3, address_line1 = $4, address_line2 = $5, city = $6, 
         postcode = $7, country = $8, latitude = $9, longitude = $10,
         operating_hours = $11, occupancy_profile = $12, public_access_level = $13,
         vulnerable_occupants = $14, critical_services = $15, updated_at = NOW()
     WHERE id = $16`,
    [
      name, estateId, siteType, addressLine1, addressLine2, city, postcode, country, latitude, longitude,
      operatingHours, occupancyProfile, publicAccessLevel, vulnerableOccupants, criticalServices, id
    ]
  );
  
  revalidatePath("/sites");
  revalidatePath(`/sites/${id}/edit`);
  revalidatePath(`/sites/${id}`);
}

export async function deleteSite(id: string) {
  await query(`DELETE FROM sites WHERE id = $1`, [id]);
  revalidatePath("/sites");
}

export async function getAssessmentsBySiteId(siteId: string) {
  const { rows } = await query(`
    SELECT a.id, a.assessment_type, a.status, a.assessed_at, a.completed_at, a.created_at,
           t.name as template_name,
           rs.band as risk_band, rs.score_value as risk_score,
           rs.metadata as risk_metadata
    FROM assessments a
    JOIN assessment_templates t ON a.template_id = t.id
    LEFT JOIN risk_scores rs ON rs.assessment_id = a.id AND rs.layer = 'residual'
    WHERE a.site_id = $1
    ORDER BY a.created_at DESC
  `, [siteId]);
  return rows;
}

export async function getLatestRiskScores(siteId: string) {
  const { rows } = await query(`
    SELECT rs.*
    FROM risk_scores rs
    JOIN assessments a ON a.id = rs.assessment_id
    WHERE a.site_id = $1 AND a.status = 'completed'
    ORDER BY a.completed_at DESC, rs.layer ASC
    LIMIT 20
  `, [siteId]);

  return rows;
}
