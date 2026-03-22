import { Hono } from "hono";
import { db } from "../db/index.js";
import { causes, conversions } from "../db/schema.js";
import { eq, sql, desc } from "drizzle-orm";
import { getLeaderboard } from "../services/analytics.js";
import { cacheMiddleware } from "../middleware/cache.js";

const ETH_ADDRESS_REGEX = /^0x[0-9a-fA-F]{40}$/;

const app = new Hono();

// Apply cache middleware to all routes
app.use("*", cacheMiddleware(30));

/**
 * GET / - List all active causes with metadata and analytics.
 * Uses a single aggregation query instead of N+1 per-cause queries.
 */
app.get("/", async (c) => {
  try {
    const activeCauses = await db
      .select()
      .from(causes)
      .where(eq(causes.isActive, true))
      .orderBy(desc(causes.createdAt));

    // Fetch all cause stats in a single query instead of N+1
    const allCauseStats = await db
      .select({
        causeTokenAddress: conversions.causeTokenAddress,
        totalBurned: sql<string>`COALESCE(SUM(${conversions.chaAmount}), '0')`,
        totalRaised: sql<string>`COALESCE(SUM(${conversions.feeAmount}), '0')`,
        totalConversions: sql<number>`COUNT(*)::int`,
        uniqueSupporters: sql<number>`COUNT(DISTINCT ${conversions.userAddress})::int`,
      })
      .from(conversions)
      .groupBy(conversions.causeTokenAddress);

    const statsMap = new Map(
      allCauseStats.map((s) => [s.causeTokenAddress, s])
    );

    const enriched = activeCauses.map((cause) => {
      const stats = statsMap.get(cause.tokenAddress.toLowerCase());
      return {
        ...cause,
        analytics: {
          totalRaised: stats?.totalRaised ?? "0",
          totalBurned: stats?.totalBurned ?? "0",
          supporterCount: stats?.uniqueSupporters ?? 0,
          totalConversions: stats?.totalConversions ?? 0,
        },
      };
    });

    return c.json({ causes: enriched });
  } catch (err) {
    console.error("Error listing causes:", err);
    return c.json({ error: "Failed to fetch causes" }, 500);
  }
});

/**
 * GET /:id - Get single cause by causeId with detailed analytics.
 */
app.get("/:id", async (c) => {
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

    const lowerAddress = cause.tokenAddress.toLowerCase();

    const [totals] = await db
      .select({
        totalBurned: sql<string>`COALESCE(SUM(${conversions.chaAmount}), '0')`,
        totalRaised: sql<string>`COALESCE(SUM(${conversions.feeAmount}), '0')`,
        totalConversions: sql<number>`COUNT(*)::int`,
        uniqueSupporters: sql<number>`COUNT(DISTINCT ${conversions.userAddress})::int`,
      })
      .from(conversions)
      .where(eq(conversions.causeTokenAddress, lowerAddress));

    return c.json({
      cause: {
        ...cause,
        analytics: {
          totalRaised: totals?.totalRaised ?? "0",
          totalBurned: totals?.totalBurned ?? "0",
          uniqueSupporters: totals?.uniqueSupporters ?? 0,
          totalConversions: totals?.totalConversions ?? 0,
        },
      },
    });
  } catch (err) {
    console.error("Error fetching cause:", err);
    return c.json({ error: "Failed to fetch cause" }, 500);
  }
});

/**
 * GET /:id/leaderboard - Top 50 converters for a cause, sorted by total amount.
 */
app.get("/:id/leaderboard", async (c) => {
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

    const leaderboard = await getLeaderboard(cause.tokenAddress, 50);

    return c.json({
      causeId,
      leaderboard,
    });
  } catch (err) {
    console.error("Error fetching leaderboard:", err);
    return c.json({ error: "Failed to fetch leaderboard" }, 500);
  }
});

/**
 * GET /:id/conversions - Recent conversions for a cause (paginated).
 */
app.get("/:id/conversions", async (c) => {
  try {
    const causeId = c.req.param("id");
    const page = Math.max(parseInt(c.req.query("page") || "1", 10), 1);
    const limit = Math.min(
      Math.max(parseInt(c.req.query("limit") || "20", 10), 1),
      100
    );
    const offset = (page - 1) * limit;

    const [cause] = await db
      .select()
      .from(causes)
      .where(eq(causes.causeId, causeId))
      .limit(1);

    if (!cause) {
      return c.json({ error: "Cause not found" }, 404);
    }

    const lowerAddress = cause.tokenAddress.toLowerCase();

    const [recentConversions, totalCount] = await Promise.all([
      db
        .select()
        .from(conversions)
        .where(eq(conversions.causeTokenAddress, lowerAddress))
        .orderBy(desc(conversions.timestamp))
        .limit(limit)
        .offset(offset),
      db
        .select({ count: sql<number>`COUNT(*)::int` })
        .from(conversions)
        .where(eq(conversions.causeTokenAddress, lowerAddress)),
    ]);

    return c.json({
      causeId,
      conversions: recentConversions,
      pagination: {
        page,
        limit,
        total: totalCount[0]?.count ?? 0,
        totalPages: Math.ceil((totalCount[0]?.count ?? 0) / limit),
      },
    });
  } catch (err) {
    console.error("Error fetching conversions:", err);
    return c.json({ error: "Failed to fetch conversions" }, 500);
  }
});

export default app;
