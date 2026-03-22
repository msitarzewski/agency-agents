import { Hono } from "hono";
import { db } from "../db/index.js";
import { users, conversions, causes } from "../db/schema.js";
import { eq, sql, desc, inArray } from "drizzle-orm";
import { cacheMiddleware } from "../middleware/cache.js";

const ETH_ADDRESS_REGEX = /^0x[0-9a-fA-F]{40}$/;

const app = new Hono();

app.use("*", cacheMiddleware(15));

/**
 * GET /:address/portfolio - User's conversion history, cause token balances, total impact stats.
 */
app.get("/:address/portfolio", async (c) => {
  try {
    const rawAddress = c.req.param("address");
    if (!ETH_ADDRESS_REGEX.test(rawAddress)) {
      return c.json({ error: "Invalid Ethereum address" }, 400);
    }
    const address = rawAddress.toLowerCase();

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

    // Batch fetch cause metadata instead of N+1 queries
    const uniqueAddresses = causeBreakdown.map((e) => e.causeTokenAddress);
    let causeMap = new Map<
      string,
      { name: string; symbol: string; causeId: string }
    >();

    if (uniqueAddresses.length > 0) {
      const causeList = await db
        .select({
          tokenAddress: causes.tokenAddress,
          name: causes.name,
          symbol: causes.symbol,
          causeId: causes.causeId,
        })
        .from(causes)
        .where(inArray(causes.tokenAddress, uniqueAddresses));

      causeMap = new Map(
        causeList.map((c) => [c.tokenAddress.toLowerCase(), c])
      );
    }

    const enrichedBreakdown = causeBreakdown.map((entry) => {
      const cause = causeMap.get(entry.causeTokenAddress.toLowerCase());
      return {
        ...entry,
        causeName: cause?.name ?? "Unknown",
        causeSymbol: cause?.symbol ?? "???",
        causeId: cause?.causeId ?? null,
      };
    });

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
    const rawAddress = c.req.param("address");
    if (!ETH_ADDRESS_REGEX.test(rawAddress)) {
      return c.json({ error: "Invalid Ethereum address" }, 400);
    }
    const address = rawAddress.toLowerCase();
    const page = Math.max(parseInt(c.req.query("page") || "1", 10), 1);
    const limit = Math.min(
      Math.max(parseInt(c.req.query("limit") || "20", 10), 1),
      100
    );
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

    // Batch fetch cause metadata instead of N+1 queries
    const uniqueAddresses = [
      ...new Set(history.map((tx) => tx.causeTokenAddress)),
    ];
    let causeMap = new Map<
      string,
      { name: string; symbol: string; causeId: string }
    >();

    if (uniqueAddresses.length > 0) {
      const causeList = await db
        .select({
          tokenAddress: causes.tokenAddress,
          name: causes.name,
          symbol: causes.symbol,
          causeId: causes.causeId,
        })
        .from(causes)
        .where(inArray(causes.tokenAddress, uniqueAddresses));

      causeMap = new Map(
        causeList.map((c) => [c.tokenAddress.toLowerCase(), c])
      );
    }

    const enriched = history.map((tx) => {
      const cause = causeMap.get(tx.causeTokenAddress.toLowerCase());
      return {
        ...tx,
        causeName: cause?.name ?? "Unknown",
        causeSymbol: cause?.symbol ?? "???",
        causeId: cause?.causeId ?? null,
      };
    });

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
