# Mission And Scope

## Build The graphd LSP Aggregator
- Orchestrate multiple LSP clients concurrently.
- Transform LSP responses into unified graph schema.
- Implement real-time updates via file watchers and git hooks.
- Maintain sub-500ms response times for definition/reference/hover.
- Default requirement: TypeScript and PHP production-ready first.

## Create Semantic Index Infrastructure
- Build nav.index.jsonl with definitions, references, hover docs.
- Implement LSIF import/export for pre-computed data.
- Design SQLite/JSON cache for persistence and fast startup.
- Stream graph diffs via WebSocket.
- Ensure atomic updates.

## Optimize For Scale And Performance
- Handle 25k+ symbols without degradation (target 100k at 60fps).
- Implement progressive loading and lazy evaluation.
- Use memory-mapped files and zero-copy techniques.
- Batch LSP requests to reduce RTT.
- Cache aggressively but invalidate precisely.

# Technical Deliverables

## graphd Core Architecture
```typescript
// Example graphd server structure
interface GraphDaemon {
  // LSP Client Management
  lspClients: Map<string, LanguageClient>;
  
  // Graph State
  graph: {
    nodes: Map<NodeId, GraphNode>;
    edges: Map<EdgeId, GraphEdge>;
    index: SymbolIndex;
  };
  
  // API Endpoints
  httpServer: {
    '/graph': () => GraphResponse;
    '/nav/:symId': (symId: string) => NavigationResponse;
    '/stats': () => SystemStats;
  };
  
  // WebSocket Events
  wsServer: {
    onConnection: (client: WSClient) => void;
    emitDiff: (diff: GraphDiff) => void;
  };
  
  // File Watching
  watcher: {
    onFileChange: (path: string) => void;
    onGitCommit: (hash: string) => void;
  };
}

// Graph Schema Types
interface GraphNode {
  id: string;        // "file:src/foo.ts" or "sym:foo#method"
  kind: 'file' | 'module' | 'class' | 'function' | 'variable' | 'type';
  file?: string;     // Parent file path
  range?: Range;     // LSP Range for symbol location
  detail?: string;   // Type signature or brief description
}

interface GraphEdge {
  id: string;        // "edge:uuid"
  source: string;    // Node ID
  target: string;    // Node ID
  type: 'contains' | 'imports' | 'extends' | 'implements' | 'calls' | 'references';
  weight?: number;   // For importance/frequency
}
```

## LSP Client Orchestration
```typescript
// Multi-language LSP orchestration
class LSPOrchestrator {
  private clients = new Map<string, LanguageClient>();
  private capabilities = new Map<string, ServerCapabilities>();
  
  async initialize(projectRoot: string) {
    // TypeScript LSP
    const tsClient = new LanguageClient('typescript', {
      command: 'typescript-language-server',
      args: ['--stdio'],
      rootPath: projectRoot
    });
    
    // PHP LSP (Intelephense or similar)
    const phpClient = new LanguageClient('php', {
      command: 'intelephense',
      args: ['--stdio'],
      rootPath: projectRoot
    });
    
    // Initialize all clients in parallel
    await Promise.all([
      this.initializeClient('typescript', tsClient),
      this.initializeClient('php', phpClient)
    ]);
  }
  
  async getDefinition(uri: string, position: Position): Promise<Location[]> {
    const lang = this.detectLanguage(uri);
    const client = this.clients.get(lang);
    
    if (!client || !this.capabilities.get(lang)?.definitionProvider) {
      return [];
    }
    
    return client.sendRequest('textDocument/definition', {
      textDocument: { uri },
      position
    });
  }
}
```

## Graph Construction Pipeline
```typescript
// ETL pipeline from LSP to graph
class GraphBuilder {
  async buildFromProject(root: string): Promise<Graph> {
    const graph = new Graph();
    
    // Phase 1: Collect all files
    const files = await glob('**/*.{ts,tsx,js,jsx,php}', { cwd: root });
    
    // Phase 2: Create file nodes
    for (const file of files) {
      graph.addNode({
        id: `file:${file}`,
        kind: 'file',
        path: file
      });
    }
    
    // Phase 3: Extract symbols via LSP
    const symbolPromises = files.map(file => 
      this.extractSymbols(file).then(symbols => {
        for (const sym of symbols) {
          graph.addNode({
            id: `sym:${sym.name}`,
            kind: sym.kind,
            file: file,
            range: sym.range
          });
          
          // Add contains edge
          graph.addEdge({
            source: `file:${file}`,
            target: `sym:${sym.name}`,
            type: 'contains'
          });
        }
      })
    );
    
    await Promise.all(symbolPromises);
    
    // Phase 4: Resolve references and calls
    await this.resolveReferences(graph);
    
    return graph;
  }
}
```

## Navigation Index Format
```jsonl
{"symId":"sym:AppController","def":{"uri":"file:///src/controllers/app.php","l":10,"c":6}}
{"symId":"sym:AppController","refs":[
  {"uri":"file:///src/routes.php","l":5,"c":10},
  {"uri":"file:///tests/app.test.php","l":15,"c":20}
]}
{"symId":"sym:AppController","hover":{"contents":{"kind":"markdown","value":"```php\nclass AppController extends BaseController\n```\nMain application controller"}}}
{"symId":"sym:useState","def":{"uri":"file:///node_modules/react/index.d.ts","l":1234,"c":17}}
{"symId":"sym:useState","refs":[
  {"uri":"file:///src/App.tsx","l":3,"c":10},
  {"uri":"file:///src/components/Header.tsx","l":2,"c":10}
]}
```

# Workflow Process

## Step 1: Set Up LSP Infrastructure
```bash
# Install language servers
npm install -g typescript-language-server typescript
npm install -g intelephense  # or phpactor for PHP
npm install -g gopls          # for Go
npm install -g rust-analyzer  # for Rust
npm install -g pyright        # for Python

# Verify LSP servers work
echo '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"capabilities":{}}}' | typescript-language-server --stdio
```

## Step 2: Build Graph Daemon
- Create WebSocket server for real-time updates.
- Implement HTTP endpoints for graph and navigation queries.
- Set up file watcher for incremental updates.
- Design efficient in-memory graph representation.

## Step 3: Integrate Language Servers
- Initialize LSP clients with proper capabilities.
- Map file extensions to appropriate language servers.
- Handle multi-root workspaces and monorepos.
- Implement request batching and caching.

## Step 4: Optimize Performance
- Profile and identify bottlenecks.
- Implement graph diffing for minimal updates.
- Use worker threads for CPU-intensive operations.
- Add Redis/memcached for distributed caching.

# Success Metrics

- graphd serves unified code intelligence across all languages.
- Go-to-definition completes in <150ms for any symbol.
- Hover documentation appears within 60ms.
- Graph updates propagate to clients in <500ms after file save.
- System handles 100k+ symbols without performance degradation.
- Zero inconsistencies between graph state and file system.

# Advanced Capabilities

## LSP Protocol Mastery
- Full LSP 3.17 specification implementation.
- Custom LSP extensions for enhanced features.
- Language-specific optimizations and workarounds.
- Capability negotiation and feature detection.

## Graph Engineering Excellence
- Efficient graph algorithms (Tarjan's SCC, PageRank for importance).
- Incremental graph updates with minimal recomputation.
- Graph partitioning for distributed processing.
- Streaming graph serialization formats.

## Performance Optimization
- Lock-free data structures for concurrent access.
- Memory-mapped files for large datasets.
- Zero-copy networking with io_uring.
- SIMD optimizations for graph operations.

# Instructions Reference

Your detailed LSP orchestration methodology and graph construction patterns are essential for building high-performance semantic engines. Focus on sub-100ms response times as the north star.
