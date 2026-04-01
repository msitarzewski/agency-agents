// ---------------------------------------------------------------------------
// Transport: CLI (stdin/stdout)
// Interactive terminal interface for the agent.
// ---------------------------------------------------------------------------

import * as readline from "node:readline";
import type { Transport, TransportMessage } from "../types/index.js";

export class CliTransport implements Transport {
  name = "cli";
  private rl: readline.Interface | null = null;

  async send(message: TransportMessage): Promise<void> {
    const prefix = message.structured ? "[kuro-7]" : "[kuro-7]";
    console.log(`\n${prefix} ${message.content}`);

    if (message.structured) {
      console.log(JSON.stringify(message.structured, null, 2));
    }
  }

  listen(handler: (message: TransportMessage) => Promise<void>): () => void {
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      prompt: "\nkuro-7 > ",
    });

    this.rl.prompt();

    this.rl.on("line", async (line) => {
      const trimmed = line.trim();
      if (!trimmed) {
        this.rl?.prompt();
        return;
      }

      if (trimmed === "exit" || trimmed === "quit") {
        console.log("[kuro-7] Session terminated.");
        process.exit(0);
      }

      try {
        // Parse structured commands: /swap SOL USDC 1.0
        const structured = this.parseCommand(trimmed);

        await handler({
          sessionId: "",
          content: trimmed,
          structured,
          channel: "cli",
        });
      } catch (err) {
        console.error(`[error] ${String(err)}`);
      }

      this.rl?.prompt();
    });

    return () => {
      this.rl?.close();
      this.rl = null;
    };
  }

  private parseCommand(input: string): Record<string, unknown> | undefined {
    if (!input.startsWith("/")) return undefined;

    const parts = input.slice(1).split(/\s+/);
    const command = parts[0];

    switch (command) {
      case "swap":
        return {
          intent: "swap",
          inputMint: parts[1],
          outputMint: parts[2],
          amount: Number(parts[3]),
        };
      case "risk":
        return {
          intent: "risk-assess",
          mint: parts[1],
        };
      case "portfolio":
        return {
          intent: "portfolio-scan",
          wallet: parts[1],
        };
      case "whale":
        return {
          intent: "whale-track",
          mint: parts[1],
          minValueUsd: Number(parts[2]) || 10_000,
        };
      default:
        return { intent: command, args: parts.slice(1) };
    }
  }
}
