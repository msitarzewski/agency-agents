import "dotenv/config";
import { serve } from "@hono/node-server";
import { Hono } from "hono";
import { cors } from "hono/cors";
import { logger } from "hono/logger";

import causesRoutes from "./routes/causes.js";
import analyticsRoutes from "./routes/analytics.js";
import userRoutes from "./routes/user.js";
import adminRoutes from "./routes/admin.js";
import { startIndexer } from "./services/indexer.js";

const app = new Hono();

// Global middleware
app.use("*", cors());
app.use("*", logger());

// Health check
app.get("/api/health", (c) => {
  return c.json({
    status: "ok",
    timestamp: new Date().toISOString(),
  });
});

// Mount routes
app.route("/api/causes", causesRoutes);
app.route("/api/analytics", analyticsRoutes);
app.route("/api/user", userRoutes);
app.route("/api/admin", adminRoutes);

// 404 handler
app.notFound((c) => {
  return c.json({ error: "Not found" }, 404);
});

// Global error handler
app.onError((err, c) => {
  console.error("Unhandled error:", err);
  return c.json({ error: "Internal server error" }, 500);
});

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
