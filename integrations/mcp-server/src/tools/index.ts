import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { AgentCatalog } from '../catalog.js';

export function registerTools(server: McpServer, catalog: AgentCatalog): void {
  // Tool 1: list_divisions
  server.tool(
    'list_divisions',
    'List all active agent divisions and their metadata (Engineering, Security, Design, Marketing, etc.)',
    {},
    async () => {
      const divisions = catalog.getDivisions();
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(divisions, null, 2)
          }
        ]
      };
    }
  );

  // Tool 2: list_agents
  server.tool(
    'list_agents',
    'List agents in the agency roster, optionally filtered by division',
    {
      division: z.string().optional().describe('Optional division ID to filter by (e.g. engineering, security, design)')
    },
    async ({ division }) => {
      const agents = catalog.getAgents(division);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(agents, null, 2)
          }
        ]
      };
    }
  );

  // Tool 3: search_agents
  server.tool(
    'search_agents',
    'Search for specific AI agent specialists by keyword, role, technology, or domain expertise',
    {
      query: z.string().describe('Search query, e.g. "React performance", "PostgreSQL tuning", "threat modeling"'),
      limit: z.number().optional().default(10).describe('Maximum number of agent summaries to return')
    },
    async ({ query, limit }) => {
      const results = catalog.searchAgents(query, limit);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(results, null, 2)
          }
        ]
      };
    }
  );

  // Tool 4: get_agent
  server.tool(
    'get_agent',
    'Fetch the complete agent prompt, including persona instructions, critical rules, workflow, and code deliverables',
    {
      identifier: z.string().describe('Agent slug or division/slug (e.g. "engineering-frontend-developer", "frontend-developer", or "engineering/engineering-frontend-developer")')
    },
    async ({ identifier }) => {
      const agent = catalog.getAgent(identifier);
      if (!agent) {
        return {
          isError: true,
          content: [
            {
              type: 'text',
              text: `Agent not found for identifier "${identifier}". Use list_agents or search_agents to find valid agent slugs.`
            }
          ]
        };
      }

      return {
        content: [
          {
            type: 'text',
            text: `# ${agent.name} (${agent.division})\n\n${agent.description}\n\n---\n\n${agent.content}`
          }
        ]
      };
    }
  );

  // Tool 5: route_task
  server.tool(
    'route_task',
    'Analyze a complex user task or project request and return recommended agent specialist team roster',
    {
      task: z.string().describe('Detailed description of the task, feature, or project to accomplish'),
      limit: z.number().optional().default(5).describe('Maximum number of team recommendations')
    },
    async ({ task, limit }) => {
      const recommendations = catalog.routeTask(task, limit);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(recommendations, null, 2)
          }
        ]
      };
    }
  );
}
