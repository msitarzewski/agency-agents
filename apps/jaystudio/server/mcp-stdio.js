// Run Jaystudio as a stdio MCP server: `claude mcp add jaystudio -- node apps/jaystudio/server/mcp-stdio.js`
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { buildMcpServer } from "./aios-mcp.js";
import { closeAll } from "./mcp-hub.js";

const server = buildMcpServer();
await server.connect(new StdioServerTransport());
process.on("SIGINT", async () => {
  await closeAll();
  process.exit(0);
});
