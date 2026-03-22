import type { Context, Next } from "hono";
import Redis from "ioredis";

let redis: Redis | null = null;

function getRedis(): Redis | null {
  if (redis) return redis;

  const redisUrl = process.env.REDIS_URL;
  if (!redisUrl) {
    console.warn("REDIS_URL not set, caching disabled");
    return null;
  }

  try {
    redis = new Redis(redisUrl, {
      maxRetriesPerRequest: 3,
      retryStrategy(times) {
        if (times > 3) return null;
        return Math.min(times * 200, 2000);
      },
      lazyConnect: true,
    });

    redis.on("error", (err) => {
      console.error("Redis connection error:", err.message);
    });

    redis.connect().catch(() => {
      console.warn("Redis connection failed, caching disabled");
      redis = null;
    });

    return redis;
  } catch {
    console.warn("Failed to initialize Redis, caching disabled");
    return null;
  }
}

/**
 * Returns the shared Redis instance for use outside of middleware.
 */
export function getRedisClient(): Redis | null {
  return getRedis();
}

/**
 * Cache middleware factory.
 * Caches GET responses by URL path with a configurable TTL.
 * POST/PATCH/PUT/DELETE requests invalidate all cache entries with a matching path prefix.
 */
export function cacheMiddleware(ttlSeconds: number = 60) {
  return async (c: Context, next: Next): Promise<Response | void> => {
    const client = getRedis();

    if (!client) {
      await next();
      return;
    }

    const method = c.req.method;
    const path = c.req.path;
    const cacheKey = `api:cache:${path}${c.req.url.includes("?") ? "?" + c.req.url.split("?")[1] : ""}`;

    // For non-GET requests, invalidate related cache entries
    if (method !== "GET") {
      try {
        const pattern = `api:cache:${path}*`;
        const keys = await client.keys(pattern);
        if (keys.length > 0) {
          await client.del(...keys);
        }
      } catch (err) {
        console.error("Cache invalidation error:", err);
      }
      await next();
      return;
    }

    // Try to serve from cache
    try {
      const cached = await client.get(cacheKey);
      if (cached) {
        const parsed = JSON.parse(cached);
        return c.json(parsed.body, parsed.status);
      }
    } catch (err) {
      console.error("Cache read error:", err);
    }

    // Execute the handler
    await next();

    // Cache the response if it was successful
    if (c.res.status >= 200 && c.res.status < 300) {
      try {
        const cloned = c.res.clone();
        const body = await cloned.json();
        await client.setex(
          cacheKey,
          ttlSeconds,
          JSON.stringify({ body, status: c.res.status })
        );
      } catch (err) {
        console.error("Cache write error:", err);
      }
    }
  };
}
