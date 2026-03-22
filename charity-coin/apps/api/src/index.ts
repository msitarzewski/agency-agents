import "dotenv/config";
import { serve } from "@hono/node-server";
import { Hono } from "hono";
import { cors } from "hono/cors";
import { logger } from "hono/logger";

import causesRoutes from "./routes/causes.js";
import analyticsRoutes from "./routes/analytics.js";
import userRoutes from "./routes/user.js";
import adminRoutes from "./routes/admin.js";
import governanceRoutes from "./routes/governance.js";
import { startIndexer } from "./services/indexer.js";
import { db } from "./db/index.js";
import { sql } from "drizzle-orm";
import { getRedisClient } from "./middleware/cache.js";

const app = new Hono();

// Global middleware
const allowedOrigins = process.env.ALLOWED_ORIGINS
  ? process.env.ALLOWED_ORIGINS.split(",")
  : ["http://localhost:3000"];

app.use(
  "*",
  cors({
    origin: allowedOrigins,
    allowMethods: ["GET", "POST", "PATCH", "DELETE"],
    allowHeaders: ["Content-Type", "x-api-key"],
    credentials: true,
  })
);
app.use("*", logger());

// Health check with dependency verification
app.get("/api/health", async (c) => {
  const checks: Record<string, string> = {};

  // DB check
  try {
    await db.execute(sql`SELECT 1`);
    checks.database = "ok";
  } catch {
    checks.database = "error";
  }

  // Redis check
  const redis = getRedisClient();
  if (redis) {
    try {
      await redis.ping();
      checks.redis = "ok";
    } catch {
      checks.redis = "error";
    }
  } else {
    checks.redis = "not_configured";
  }

  const healthy = Object.values(checks).every(
    (v) => v === "ok" || v === "not_configured"
  );

  return c.json(
    {
      status: healthy ? "ok" : "degraded",
      checks,
      timestamp: new Date().toISOString(),
    },
    healthy ? 200 : 503
  );
});

// Mount routes
app.route("/api/causes", causesRoutes);
app.route("/api/analytics", analyticsRoutes);
app.route("/api/user", userRoutes);
app.route("/api/admin", adminRoutes);
app.route("/api/governance", governanceRoutes);

// 404 handler
app.notFound((c) => {
  return c.json({ error: "Not found" }, 404);
});

// Global error handler
app.onError((err, c) => {
  console.error("Unhandled error:", err);
  return c.json({ error: "Internal server error" }, 500);
});

// Graceful shutdown
function gracefulShutdown(signal: string) {
  console.log(`Received ${signal}, shutting down gracefully...`);
  const redis = getRedisClient();
  if (redis) {
    redis.quit().catch(() => {});
  }
  process.exit(0);
}

process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
process.on("SIGINT", () => gracefulShutdown("SIGINT"));

// Start server
const port = parseInt(process.env.PORT || "3001", 10);

serve(
  {
    fetch: app.fetch,
    port,
  },
  (info) => {
    console.log(`Charity Coin API running on http://localhost:${info.port}`);

    // Start the on-chain event indexer in the background
    startIndexer().catch((err) => {
      console.error("Failed to start indexer:", err);
    });
  }
);

export default app;
