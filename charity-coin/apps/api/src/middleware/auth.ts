import type { Context, Next } from "hono";

/**
 * Simple API key authentication middleware for admin routes.
 * Checks the x-api-key header against the ADMIN_API_KEY environment variable.
 */
export async function adminAuth(c: Context, next: Next): Promise<Response | void> {
  const apiKey = c.req.header("x-api-key");
  const expectedKey = process.env.ADMIN_API_KEY;

  if (!expectedKey) {
    console.error("ADMIN_API_KEY environment variable is not set");
    return c.json({ error: "Server configuration error" }, 500);
  }

  if (!apiKey) {
    return c.json({ error: "Missing x-api-key header" }, 401);
  }

  if (apiKey !== expectedKey) {
    return c.json({ error: "Invalid API key" }, 401);
  }

  await next();
}
