import type { Context, Next } from "hono";
import { timingSafeEqual } from "crypto";

/**
 * Simple API key authentication middleware for admin routes.
 * Checks the x-api-key header against the ADMIN_API_KEY environment variable.
 * Uses timing-safe comparison to prevent timing attacks.
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

  // Use timing-safe comparison to prevent timing attacks
  const apiKeyBuffer = Buffer.from(apiKey);
  const expectedKeyBuffer = Buffer.from(expectedKey);

  if (
    apiKeyBuffer.length !== expectedKeyBuffer.length ||
    !timingSafeEqual(apiKeyBuffer, expectedKeyBuffer)
  ) {
    return c.json({ error: "Invalid API key" }, 401);
  }

  await next();
}
