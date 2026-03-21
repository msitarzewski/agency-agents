import { Hono } from "hono";
import { z } from "zod";
import { db } from "../db/index.js";
import { causes, conversions, users } from "../db/schema.js";
import { eq, sql } from "drizzle-orm";
import { adminAuth } from "../middleware/auth.js";

const app = new Hono();

// All admin routes require API key authentication
app.use("*", adminAuth);

// Validation schemas
const createCauseSchema = z.object({
  causeId: z.string().min(1, "causeId is required"),
  tokenAddress: z.string().min(1, "tokenAddress is required"),
  name: z.string().min(1, "name is required"),
  symbol: z.string().min(1, "symbol is required"),
  description: z.string().optional().default(""),
  charityWallet: z.string().min(1, "charityWallet is required"),
});

const updateCauseSchema = z.object({
  name: z.string().min(1).optional(),
  description: z.string().optional(),
  isActive: z.boolean().optional(),
});

/**
 * POST /causes - Add new cause.
 */
app.post("/causes", async (c) => {
  try {
    const body = await c.req.json();
    const parsed = createCauseSchema.safeParse(body);

    if (!parsed.success) {
      return c.json(
        { error: "Validation failed", details: parsed.error.flatten() },
        400
      );
    }

    const data = parsed.data;

    // Check for duplicates
    const [existing] = await db
      .select({ id: causes.id })
      .from(causes)
      .where(eq(causes.causeId, data.causeId))
      .limit(1);

    if (existing) {
      return c.json({ error: "Cause with this causeId already exists" }, 409);
    }

    const [newCause] = await db
      .insert(causes)
      .values({
        causeId: data.causeId,
        tokenAddress: data.tokenAddress.toLowerCase(),
        name: data.name,
        symbol: data.symbol,
        description: data.description,
        charityWallet: data.charityWallet.toLowerCase(),
        isActive: true,
      })
      .returning();

    return c.json({ cause: newCause }, 201);
  } catch (err) {
    console.error("Error creating cause:", err);
    return c.json({ error: "Failed to create cause" }, 500);
  }
});

/**
 * PATCH /causes/:id - Update cause metadata.
 */
app.patch("/causes/:id", async (c) => {
  try {
    const causeId = c.req.param("id");
    const body = await c.req.json();
    const parsed = updateCauseSchema.safeParse(body);

    if (!parsed.success) {
      return c.json(
        { error: "Validation failed", details: parsed.error.flatten() },
        400
      );
    }

    const data = parsed.data;

    // Check cause exists
    const [existing] = await db
      .select()
      .from(causes)
      .where(eq(causes.causeId, causeId))
      .limit(1);

    if (!existing) {
      return c.json({ error: "Cause not found" }, 404);
    }

    const updateFields: Record<string, unknown> = {};
    if (data.name !== undefined) updateFields.name = data.name;
    if (data.description !== undefined) updateFields.description = data.description;
    if (data.isActive !== undefined) updateFields.isActive = data.isActive;

    if (Object.keys(updateFields).length === 0) {
      return c.json({ error: "No fields to update" }, 400);
    }

    const [updated] = await db
      .update(causes)
      .set(updateFields)
      .where(eq(causes.causeId, causeId))
      .returning();

    return c.json({ cause: updated });
  } catch (err) {
    console.error("Error updating cause:", err);
    return c.json({ error: "Failed to update cause" }, 500);
  }
});

/**
 * GET /stats - Admin dashboard stats.
 */
app.get("/stats", async (c) => {
  try {
    const [conversionStats] = await db
      .select({
        totalConversions: sql<number>`COUNT(*)::int`,
        totalChaBurned: sql<string>`COALESCE(SUM(${conversions.chaAmount}), '0')`,
        totalFeesCollected: sql<string>`COALESCE(SUM(${conversions.feeAmount}), '0')`,
        uniqueUsers: sql<number>`COUNT(DISTINCT ${conversions.userAddress})::int`,
      })
      .from(conversions);

    const [causeStats] = await db
      .select({
        totalCauses: sql<number>`COUNT(*)::int`,
        activeCauses: sql<number>`COUNT(*) FILTER (WHERE ${causes.isActive} = true)::int`,
      })
      .from(causes);

    const [userStats] = await db
      .select({
        totalUsers: sql<number>`COUNT(*)::int`,
      })
      .from(users);

    // Recent conversions (last 24 hours)
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    const [recentStats] = await db
      .select({
        conversions24h: sql<number>`COUNT(*)::int`,
        volume24h: sql<string>`COALESCE(SUM(${conversions.chaAmount}), '0')`,
      })
      .from(conversions)
      .where(sql`${conversions.timestamp} >= ${oneDayAgo}`);

    return c.json({
      conversions: {
        total: conversionStats?.totalConversions ?? 0,
        totalChaBurned: conversionStats?.totalChaBurned ?? "0",
        totalFeesCollected: conversionStats?.totalFeesCollected ?? "0",
        uniqueUsers: conversionStats?.uniqueUsers ?? 0,
      },
      causes: {
        total: causeStats?.totalCauses ?? 0,
        active: causeStats?.activeCauses ?? 0,
      },
      users: {
        total: userStats?.totalUsers ?? 0,
      },
      last24h: {
        conversions: recentStats?.conversions24h ?? 0,
        volume: recentStats?.volume24h ?? "0",
      },
    });
  } catch (err) {
    console.error("Error fetching admin stats:", err);
    return c.json({ error: "Failed to fetch admin stats" }, 500);
  }
});

export default app;
