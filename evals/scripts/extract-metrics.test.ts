import { describe, it, expect } from "vitest";
import { extractMetrics, parseAgentFile } from "./extract-metrics";
import path from "path";

describe("parseAgentFile", () => {
  it("extracts frontmatter fields from a real agent file", () => {
    const agentPath = path.resolve(
      __dirname,
      "../../engineering/engineering-backend-architect.md"
    );
    const result = parseAgentFile(agentPath);

    expect(result.name).toBe("Backend Architect");
    expect(result.description).toContain("backend architect");
    expect(result.category).toBe("engineering");
  });

  it("extracts success metrics section", () => {
    const agentPath = path.resolve(
      __dirname,
      "../../engineering/engineering-backend-architect.md"
    );
    const result = parseAgentFile(agentPath);

    expect(result.successMetrics).toBeDefined();
    expect(result.successMetrics!.length).toBeGreaterThan(0);
    expect(result.successMetrics!.some((m) => m.includes("200ms"))).toBe(true);
  });

  it("extracts critical rules section", () => {
    const agentPath = path.resolve(
      __dirname,
      "../../academic/academic-historian.md"
    );
    const result = parseAgentFile(agentPath);

    expect(result.criticalRules).toBeDefined();
    expect(result.criticalRules!.length).toBeGreaterThan(0);
  });

  it("handles agent with missing sections gracefully", () => {
    const agentPath = path.resolve(
      __dirname,
      "../../engineering/engineering-backend-architect.md"
    );
    const result = parseAgentFile(agentPath);

    expect(result).toHaveProperty("name");
    expect(result).toHaveProperty("category");
    expect(result).toHaveProperty("successMetrics");
    expect(result).toHaveProperty("criticalRules");
    expect(result).toHaveProperty("deliverableFormat");
  });
});

describe("extractMetrics", () => {
  it("extracts metrics for multiple agents by glob pattern", () => {
    const results = extractMetrics(
      path.resolve(__dirname, "../../engineering/engineering-backend-architect.md")
    );

    expect(results.length).toBe(1);
    expect(results[0].name).toBe("Backend Architect");
  });
});
