#!/usr/bin/env node

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { AgentCatalog } from './catalog.js';
import { registerTools } from './tools/index.js';
import { registerResources } from './resources/index.js';

async function main() {
  const catalog = new AgentCatalog();
  await catalog.init();

  const server = new McpServer({
    name: 'agency-agents-mcp',
    version: '1.0.0'
  });

  registerTools(server, catalog);
  registerResources(server, catalog);

  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error('Fatal error starting agency-agents MCP server:', error);
  process.exit(1);
});
