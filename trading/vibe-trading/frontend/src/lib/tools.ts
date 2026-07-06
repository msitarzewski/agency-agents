/**
 * Single source of truth for tool name → user-facing label.
 */
export const TOOL_LABELS: Record<string, string> = {
  load_skill: "Load strategy knowledge",
  write_file: "Generate code",
  edit_file: "Edit code",
  read_file: "Read file",
  run_backtest: "Run backtest",
  bash: "Run command",
  read_url: "Read webpage",
  read_document: "Read document",
  trading_connections: "List trading connectors",
  trading_select_connection: "Select trading connector",
  trading_check: "Check trading connector",
  trading_account: "Read connector account",
  trading_positions: "Read connector positions",
  trading_orders: "Read connector orders",
  trading_quote: "Read connector quote",
  trading_history: "Read connector history",
  compact: "Summarize conversation",
  create_task: "Create task",
  update_task: "Update task",
  spawn_subagent: "Spawn sub-agent",
};

export function localizeToolName(tool: string, fallback?: string): string {
  if (tool in TOOL_LABELS) {
    return TOOL_LABELS[tool];
  }
  if (fallback !== undefined) {
    return fallback;
  }
  return tool;
}
