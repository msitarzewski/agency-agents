import { Hono } from "hono";
import { db } from "../db/index.js";
import { causes, conversions } from "../db/schema.js";
import { eq, sql } from "drizzle-orm";
import {
  getTotalBurned,
  getTotalRaised,
  get24hVolume,
  getCauseStats,
  getCauseDailyVolume,
  getDailyBurns,
  getDailyConversions,
} from "../services/analytics.js";
import { cacheMiddleware } from "../middleware/cache.js";

const app = new Hono();

// Apply cache middleware
app.use("*", cacheMiddleware(60));

/**
 * GET /overview - Platform-wide stats.
 */
app.get("/overview", async (c) => {
  try {
    const [totalBurned, totalRaised, volume24h] = await Promise.all([
      getTotalBurned(),
      getTotalRaised(),
      get24hVolume(),
    ]);

    const [conversionCount] = await db
      .select({ count: sql<number>`COUNT(*)::int` })
      .from(conversions);

    const [causeCount] = await db
      .select({ count: sql<number>`COUNT(*)::int` })
      .from(causes)
      .where(eq(causes.isActive, true));

    return c.json({
      totalChaBurned: totalBurned,
      totalRaisedForCharity: totalRaised,
      totalConversions: conversionCount?.count ?? 0,
      activeCauses: causeCount?.count ?? 0,
      volume24h,
    });
  } catch (err) {
    console.error("Error fetching overview:", err);
    return c.json({ error: "Failed to fetch overview stats" }, 500);
  }
});

/**
 * GET /cause/:id - Cause-specific analytics.
 */
app.get("/cause/:id", async (c) => {
  try {
    const causeId = c.req.param("id");

    const [cause] = await db
      .select()
      .from(causes)
      .where(eq(causes.causeId, causeId))
      .limit(1);

    if (!cause) {
      return c.json({ error: "Cause not found" }, 404);
    }

    const [stats, dailyVolume] = await Promise.all([
      getCauseStats(cause.tokenAddress),
      getCauseDailyVolume(cause.tokenAddress, 30),
    ]);

    return c.json({
      causeId,
      causeName: cause.name,
      totalRaised: stats.totalRaised,
      totalBurned: stats.totalBurned,
      uniqueSupporters: stats.uniqueSupporters,
      totalConversions: stats.totalConversions,
      dailyVolume,
    });
  } catch (err) {
    console.error("Error fetching cause analytics:", err);
    return c.json({ error: "Failed to fetch cause analytics" }, 500);
  }
});

/**
 * GET /chart/burns - Time-series data of CHA burned over time (daily, last 90 days).
 */
app.get("/chart/burns", async (c) => {
  try {
    const days = Math.min(parseInt(c.req.query("days") || "90", 10), 365);
    const data = await getDailyBurns(days);

    return c.json({
      period: `${days} days`,
      data,
    });
  } catch (err) {
    console.error("Error fetching burn chart:", err);
    return c.json({ error: "Failed to fetch burn chart data" }, 500);
  }
});

/**
 * GET /chart/conversions - Time-series of conversion volume (daily, last 90 days).
 */
app.get("/chart/conversions", async (c) => {
  try {
    const days = Math.min(parseInt(c.req.query("days") || "90", 10), 365);
    const data = await getDailyConversions(days);

    return c.json({
      period: `${days} days`,
      data,
    });
  } catch (err) {
    console.error("Error fetching conversion chart:", err);
    return c.json({ error: "Failed to fetch conversion chart data" }, 500);
  }
});

export default app;
