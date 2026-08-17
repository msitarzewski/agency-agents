import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js';
import { AgentCatalog } from '../catalog.js';

export function registerResources(server: McpServer, catalog: AgentCatalog): void {
  // Resource 1: agency://divisions
  server.resource(
    'divisions',
    'agency://divisions',
    async (uri) => {
      const divisions = catalog.getDivisions();
      return {
        contents: [
          {
            uri: uri.href,
            text: JSON.stringify(divisions, null, 2),
            mimeType: 'application/json'
          }
        ]
      };
    }
  );

  // Resource 2: agency://agents/{division}/{slug}
  server.resource(
    'agent-spec',
    new ResourceTemplate('agency://agents/{division}/{slug}', { list: undefined }),
    async (uri, { division, slug }) => {
      const divStr = Array.isArray(division) ? division[0] : division;
      const slugStr = Array.isArray(slug) ? slug[0] : slug;
      const key = `${divStr}/${slugStr}`;

      const agent = catalog.getAgent(key) || catalog.getAgent(slugStr);
      if (!agent) {
        throw new Error(`Agent not found for ${uri.href}`);
      }

      return {
        contents: [
          {
            uri: uri.href,
            text: agent.content,
            mimeType: 'text/markdown'
          }
        ]
      };
    }
  );
}
