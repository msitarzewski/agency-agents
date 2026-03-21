import { Hono } from "hono";
import { db } from "../db/index.js";
import { users, conversions, causes } from "../db/schema.js";
import { eq, sql, desc } from "drizzle-orm";
import { cacheMiddleware } from "../middleware/cache.js";

const app = new Hono();

app.use("*", cacheMiddleware(15));

/**
 * GET /:address/portfolio - User's conversion history, cause token balances, total impact stats.
 */
app.get("/:address/portfolio", async (c) => {
  try {
    const address = c.req.param("address").toLowerCase();

    // Get user record
    const [user] = await db
      .select()
      .from(users)
      .where(eq(users.address, address))
      .limit(1);

    if (!user) {
      return c.json({
        address,
        totalChaConverted: "0",
        totalCausesSupported: 0,
        firstConversionAt: null,
        lastConversionAt: null,
        causeBreakdown: [],
      });
    }

    // Get per-cause breakdown for the user
    const causeBreakdown = await db
      .select({
        causeTokenAddress: conversions.causeTokenAddress,
        totalChaAmount: sql<string>`SUM(${conversions.chaAmount})`,
        totalCauseTokenAmount: sql<string>`SUM(${conversions.causeTokenAmount})`,
        conversionCount: sql<number>`COUNT(*)::int`,
        lastConversion: sql<string>`MAX(${conversions.timestamp})::text`,
      })
      .from(conversions)
      .where(eq(conversions.userAddress, address))
      .groupBy(conversions.causeTokenAddress)
      .orderBy(sql`SUM(${conversions.chaAmount}) DESC`);

    // Enrich with cause metadata
    const enrichedBreakdown = await Promise.all(
      causeBreakdown.map(async (entry) => {
        const [cause] = await db
          .select({ name: causes.name, symbol: causes.symbol, causeId: causes.causeId })
          .from(causes)
          .where(
            sql`LOWER(${causes.tokenAddress}) = ${entry.causeTokenAddress.toLowerCase()}`
          )
          .limit(1);

        return {
          ...entry,
          causeName: cause?.name ?? "Unknown",
          causeSymbol: cause?.symbol ?? "???",
          causeId: cause?.causeId ?? null,
        };
      })
    );

    return c.json({
      address,
      totalChaConverted: user.totalChaConverted,
      totalCausesSupported: user.totalCausesSupported,
      firstConversionAt: user.firstConversionAt,
      lastConversionAt: user.lastConversionAt,
      causeBreakdown: enrichedBreakdown,
    });
  } catch (err) {
    console.error("Error fetching user portfolio:", err);
    return c.json({ error: "Failed to fetch user portfolio" }, 500);
  }
});

/**
 * GET /:address/history - Paginated transaction history for a user.
 */
app.get("/:address/history", async (c) => {
  try {
    const address = c.req.param("address").toLowerCase();
    const page = parseInt(c.req.query("page") || "1", 10);
    const limit = Math.min(parseInt(c.req.query("limit") || "20", 10), 100);
    const offset = (page - 1) * limit;

    const [history, totalCount] = await Promise.all([
      db
        .select({
          id: conversions.id,
          causeTokenAddress: conversions.causeTokenAddress,
          chaAmount: conversions.chaAmount,
          causeTokenAmount: conversions.causeTokenAmount,
          feeAmount: conversions.feeAmount,
          txHash: conversions.txHash,
          blockNumber: conversions.blockNumber,
          timestamp: conversions.timestamp,
        })
        .from(conversions)
        .where(eq(conversions.userAddress, address))
        .orderBy(desc(conversions.timestamp))
        .limit(limit)
        .offset(offset),
      db
        .select({ count: sql<number>`COUNT(*)::int` })
        .from(conversions)
        .where(eq(conversions.userAddress, address)),
    ]);

    // Enrich with cause metadata
    const enriched = await Promise.all(
      history.map(async (tx) => {
        const [cause] = await db
          .select({ name: causes.name, symbol: causes.symbol, causeId: causes.causeId })
          .from(causes)
          .where(
            sql`LOWER(${causes.tokenAddress}) = ${tx.causeTokenAddress.toLowerCase()}`
          )
          .limit(1);

        return {
          ...tx,
          causeName: cause?.name ?? "Unknown",
          causeSymbol: cause?.symbol ?? "???",
          causeId: cause?.causeId ?? null,
        };
      })
    );

    return c.json({
      address,
      history: enriched,
      pagination: {
        page,
        limit,
        total: totalCount[0]?.count ?? 0,
        totalPages: Math.ceil((totalCount[0]?.count ?? 0) / limit),
      },
    });
  } catch (err) {
    console.error("Error fetching user history:", err);
    return c.json({ error: "Failed to fetch user history" }, 500);
  }
});

export default app;
