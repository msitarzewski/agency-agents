"use server";

import { query } from "@/lib/db";
import { revalidatePath } from "next/cache";

export async function getAssetsBySiteId(siteId: string) {
  const { rows } = await query(`
    SELECT id, name, asset_type, description, criticality_level, created_at
    FROM assets
    WHERE site_id = $1
    ORDER BY criticality_level DESC, name ASC
  `, [siteId]);
  return rows;
}

export async function createAsset(formData: FormData) {
  const siteId = formData.get("siteId") as string;
  const name = formData.get("name") as string;
  const assetType = formData.get("assetType") as string;
  const description = formData.get("description") as string;
  const criticalityLevel = parseInt(formData.get("criticalityLevel") as string, 10);
  
  await query(
    `INSERT INTO assets (site_id, name, asset_type, description, criticality_level) 
     VALUES ($1, $2, $3, $4, $5)`,
    [siteId, name, assetType, description, criticalityLevel]
  );
  
  revalidatePath(`/sites/${siteId}`);
}

export async function deleteAsset(id: string, siteId: string) {
  await query(`DELETE FROM assets WHERE id = $1`, [id]);
  revalidatePath(`/sites/${siteId}`);
}
