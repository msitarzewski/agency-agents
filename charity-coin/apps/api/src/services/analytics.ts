import { db } from "../db/index.js";
import { causes, conversions, users } from "../db/schema.js";
import { eq, sql, desc, and, gte } from "drizzle-orm";
import { getRedisClient } from "../middleware/cache.js";

const CACHE_TTL = 60; // 60 seconds

async function getCached<T>(key: string, fetcher: () => Promise<T>): Promise<T> {
  const redis = getRedisClient();

  if (redis) {
    try {
      const cached = await redis.get(key);
      if (cached) {
        return JSON.parse(cached) as T;
      }
    } catch (err) {
      console.error("Analytics cache read error:", err);
    }
  }

  const result = await fetcher();

  if (redis) {
    try {
      await redis.setex(key, CACHE_TTL, JSON.stringify(result));
    } catch (err) {
      console.error("Analytics cache write error:", err);
    }
  }

  return result;
}

/**
 * Get total CHA burned across all conversions.
 */
export async function getTotalBurned(): Promise<string> {
  return getCached("analytics:totalBurned", async () => {
    const result = await db
      .select({
        total: sql<string>`COALESCE(SUM(${conversions.chaAmount}), '0')`,
      })
      .from(conversions);
    return result[0]?.total ?? "0";
  });
}

/**
 * Get total raised for charity (sum of fee amounts).
 */
export async function getTotalRaised(): Promise<string> {
  return getCached("analytics:totalRaised", async () => {
    const result = await db
      .select({
        total: sql<string>`COALESCE(SUM(${conversions.feeAmount}), '0')`,
      })
      .from(conversions);
    return result[0]?.total ?? "0";
  });
}

/**
 * Get stats for a specific cause token.
 */
export async function getCauseStats(causeTokenAddress: string): Promise<{
  totalRaised: string;
  totalBurned: string;
  uniqueSupporters: number;
  totalConversions: number;
}> {
  const cacheKey = `analytics:cause:${causeTokenAddress.toLowerCase()}`;

  return getCached(cacheKey, async () => {
    const lowerAddress = causeTokenAddress.toLowerCase();

    const [totals] = await db
      .select({
        totalBurned: sql<string>`COALESCE(SUM(${conversions.chaAmount}), '0')`,
        totalRaised: sql<string>`COALESCE(SUM(${conversions.feeAmount}), '0')`,
        totalConversions: sql<number>`COUNT(*)::int`,
        uniqueSupporters: sql<number>`COUNT(DISTINCT ${conversions.userAddress})::int`,
      })
      .from(conversions)
      .where(sql`LOWER(${conversions.causeTokenAddress}) = ${lowerAddress}`);

    return {
      totalRaised: totals?.totalRaised ?? "0",
      totalBurned: totals?.totalBurned ?? "0",
      uniqueSupporters: totals?.uniqueSupporters ?? 0,
      totalConversions: totals?.totalConversions ?? 0,
    };
  });
}

/**
 * Get leaderboard for a specific cause (top converters by total CHA amount).
 */
export async function getLeaderboard(
  causeTokenAddress: string,
  limit: number = 50
): Promise<
  Array<{
    userAddress: string;
    totalChaAmount: string;
    totalCauseTokenAmount: string;
    conversionCount: number;
  }>
> {
  const cacheKey = `analytics:leaderboard:${causeTokenAddress.toLowerCase()}:${limit}`;

  return getCached(cacheKey, async () => {
    const lowerAddress = causeTokenAddress.toLowerCase();

    const result = await db
      .select({
        userAddress: conversions.userAddress,
        totalChaAmount: sql<string>`SUM(${conversions.chaAmount})`,
        totalCauseTokenAmount: sql<string>`SUM(${conversions.causeTokenAmount})`,
        conversionCount: sql<number>`COUNT(*)::int`,
      })
      .from(conversions)
      .where(sql`LOWER(${conversions.causeTokenAddress}) = ${lowerAddress}`)
      .groupBy(conversions.userAddress)
      .orderBy(sql`SUM(${conversions.chaAmount}) DESC`)
      .limit(limit);

    return result;
  });
}

/**
 * Get 24-hour conversion volume.
 */
export async function get24hVolume(): Promise<string> {
  return getCached("analytics:24hVolume", async () => {
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    const result = await db
      .select({
        total: sql<string>`COALESCE(SUM(${conversions.chaAmount}), '0')`,
      })
      .from(conversions)
      .where(gte(conversions.timestamp, oneDayAgo));
    return result[0]?.total ?? "0";
  });
}

/**
 * Get daily time-series data for CHA burned over the last N days.
 */
export async function getDailyBurns(
  days: number = 90
): Promise<Array<{ date: string; totalBurned: string }>> {
  const cacheKey = `analytics:dailyBurns:${days}`;

  return getCached(cacheKey, async () => {
    const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);

    const result = await db
      .select({
        date: sql<string>`DATE(${conversions.timestamp})::text`,
        totalBurned: sql<string>`COALESCE(SUM(${conversions.chaAmount}), '0')`,
      })
      .from(conversions)
      .where(gte(conversions.timestamp, startDate))
      .groupBy(sql`DATE(${conversions.timestamp})`)
      .orderBy(sql`DATE(${conversions.timestamp}) ASC`);

    return result;
  });
}

/**
 * Get daily time-series data for conversion counts over the last N days.
 */
export async function getDailyConversions(
  days: number = 90
): Promise<Array<{ date: string; count: number; volume: string }>> {
  const cacheKey = `analytics:dailyConversions:${days}`;

  return getCached(cacheKey, async () => {
    const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);

    const result = await db
      .select({
        date: sql<string>`DATE(${conversions.timestamp})::text`,
        count: sql<number>`COUNT(*)::int`,
        volume: sql<string>`COALESCE(SUM(${conversions.chaAmount}), '0')`,
      })
      .from(conversions)
      .where(gte(conversions.timestamp, startDate))
      .groupBy(sql`DATE(${conversions.timestamp})`)
      .orderBy(sql`DATE(${conversions.timestamp}) ASC`);

    return result;
  });
}

/**
 * Get daily conversion volume for a specific cause over the last N days.
 */
export async function getCauseDailyVolume(
  causeTokenAddress: string,
  days: number = 30
): Promise<Array<{ date: string; volume: string; count: number }>> {
  const cacheKey = `analytics:causeDailyVolume:${causeTokenAddress.toLowerCase()}:${days}`;

  return getCached(cacheKey, async () => {
    const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    const lowerAddress = causeTokenAddress.toLowerCase();

    const result = await db
      .select({
        date: sql<string>`DATE(${conversions.timestamp})::text`,
        volume: sql<string>`COALESCE(SUM(${conversions.chaAmount}), '0')`,
        count: sql<number>`COUNT(*)::int`,
      })
      .from(conversions)
      .where(
        and(
          sql`LOWER(${conversions.causeTokenAddress}) = ${lowerAddress}`,
          gte(conversions.timestamp, startDate)
        )
      )
      .groupBy(sql`DATE(${conversions.timestamp})`)
      .orderBy(sql`DATE(${conversions.timestamp}) ASC`);

    return result;
  });
}
