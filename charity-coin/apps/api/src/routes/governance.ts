import { Hono } from "hono";
import { db } from "../db/index.js";
import { governanceProposals } from "../db/schema.js";
import { eq, desc, sql } from "drizzle-orm";
import { cacheMiddleware } from "../middleware/cache.js";

const app = new Hono();

app.use("*", cacheMiddleware(30));

/**
 * GET / - List all governance proposals.
 */
app.get("/", async (c) => {
  try {
    const status = c.req.query("status");
    const page = Math.max(parseInt(c.req.query("page") || "1", 10), 1);
    const limit = Math.min(parseInt(c.req.query("limit") || "20", 10), 100);
    const offset = (page - 1) * limit;

    let query = db.select().from(governanceProposals);

    if (status) {
      query = query.where(eq(governanceProposals.status, status)) as typeof query;
    }

    const proposals = await query
      .orderBy(desc(governanceProposals.createdAt))
      .limit(limit)
      .offset(offset);

    const [countResult] = await db
      .select({ count: sql<number>`COUNT(*)::int` })
      .from(governanceProposals);

    return c.json({
      proposals,
      pagination: {
        page,
        limit,
        total: countResult?.count ?? 0,
      },
    });
  } catch (err) {
    console.error("Error fetching proposals:", err);
    return c.json({ error: "Failed to fetch proposals" }, 500);
  }
});

/**
 * GET /:id - Get a single proposal by proposalId.
 */
app.get("/:id", async (c) => {
  try {
    const proposalId = c.req.param("id");

    const [proposal] = await db
      .select()
      .from(governanceProposals)
      .where(eq(governanceProposals.proposalId, proposalId))
      .limit(1);

    if (!proposal) {
      return c.json({ error: "Proposal not found" }, 404);
    }

    return c.json({ proposal });
  } catch (err) {
    console.error("Error fetching proposal:", err);
    return c.json({ error: "Failed to fetch proposal" }, 500);
  }
});

export default app;
