# Mission And Scope

Build production-quality MCP servers with:
1. Tool design with clear names, typed parameters, and helpful descriptions.
2. Resource exposure so agents can read required data sources.
3. Error handling with graceful failures and actionable messages.
4. Security with input validation, authentication handling, and rate limiting.
5. Testing with unit tests for tools and integration tests for the server.

# MCP Server Structure
```typescript
// TypeScript MCP server skeleton
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({ name: "my-server", version: "1.0.0" });

server.tool("search_items", { query: z.string(), limit: z.number().optional() },
  async ({ query, limit = 10 }) => {
    const results = await searchDatabase(query, limit);
    return { content: [{ type: "text", text: JSON.stringify(results, null, 2) }] };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
```
