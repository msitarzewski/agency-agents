// ---------------------------------------------------------------------------
// Pattern 1a: Orchestration Layer
// Decomposes tasks into subtasks, selects skills, manages execution order.
// ---------------------------------------------------------------------------

import type {
  Id,
  OrchestrationPlan,
  Session,
  SkillOutput,
  Task,
  TransportMessage,
} from "../types/index.js";
import type { Executor } from "./executor.js";
import type { SkillRegistry } from "./registry.js";
import type { SessionManager } from "./session.js";
import type { StreamManager } from "./stream.js";
import { SessionEventType } from "../types/index.js";

let idCounter = 0;
function makeId(): Id {
  return `task_${Date.now()}_${++idCounter}`;
}

export class Orchestrator {
  constructor(
    private registry: SkillRegistry,
    private executor: Executor,
    private sessions: SessionManager,
    private stream: StreamManager,
  ) {}

  /**
   * Handle an inbound request: decompose → plan → execute phases → produce
   * response. This is the top-level entry point for every user interaction.
   */
  async handle(session: Session, request: TransportMessage): Promise<TransportMessage> {
    this.sessions.record(session, SessionEventType.RequestReceived, {
      channel: request.channel,
      content: request.content,
    });

    // 1. Decompose the request into an execution plan
    const plan = await this.decompose(session, request);

    this.sessions.record(session, SessionEventType.TaskDecomposed, {
      taskCount: plan.tasks.length,
      phases: plan.phases.size,
    });

    // 2. Execute phases sequentially; within each phase, tasks run in parallel
    for (const [phaseNum, taskIds] of plan.phases) {
      const phaseTasks = plan.tasks.filter((t) => taskIds.includes(t.id));

      this.stream.emit(session.id, {
        type: "phase_start",
        phase: phaseNum,
        tasks: phaseTasks.map((t) => t.skillName),
      });

      const results = await Promise.allSettled(
        phaseTasks.map((task) => this.executeTask(session, task)),
      );

      // Check for failures — if a critical task fails, abort remaining phases
      for (let i = 0; i < results.length; i++) {
        const result = results[i];
        const task = phaseTasks[i];
        if (result.status === "rejected" || (result.status === "fulfilled" && !result.value.success)) {
          task.status = "failed";
          task.error = result.status === "rejected"
            ? String(result.reason)
            : result.value.error;

          this.sessions.record(session, SessionEventType.Error, {
            taskId: task.id,
            skill: task.skillName,
            error: task.error,
          });
        }
      }

      this.stream.emit(session.id, {
        type: "phase_complete",
        phase: phaseNum,
        results: phaseTasks.map((t) => ({ skill: t.skillName, status: t.status })),
      });
    }

    // 3. Assemble the response from completed task results
    const response = this.assembleResponse(session, plan, request);

    this.sessions.record(session, SessionEventType.ResponseProduced, {
      channel: response.channel,
      taskResults: plan.tasks.map((t) => ({
        skill: t.skillName,
        status: t.status,
      })),
    });

    return response;
  }

  /**
   * Decompose a request into an execution plan. In a production system this
   * would use the model to reason about what skills to invoke. For now, we
   * use a deterministic router based on intent keywords.
   */
  private async decompose(
    session: Session,
    request: TransportMessage,
  ): Promise<OrchestrationPlan> {
    const content = request.content.toLowerCase();
    const tasks: Task[] = [];
    const phases = new Map<number, Id[]>();

    // Intent detection — simple keyword routing for the scaffold.
    // Production: replace with model-based intent classification.

    if (content.includes("swap") || content.includes("buy") || content.includes("sell")) {
      // Phase 0: risk assessment in parallel with portfolio scan
      const riskTask = this.makeTask("risk-assess", "Assess token risk before trade", request.structured ?? {});
      const portfolioTask = this.makeTask("portfolio-scan", "Scan current portfolio", request.structured ?? {});
      tasks.push(riskTask, portfolioTask);
      phases.set(0, [riskTask.id, portfolioTask.id]);

      // Phase 1: execute swap (depends on risk assessment passing)
      const swapTask = this.makeTask("swap", "Execute token swap", request.structured ?? {});
      tasks.push(swapTask);
      phases.set(1, [swapTask.id]);
    } else if (content.includes("risk") || content.includes("assess") || content.includes("check")) {
      const riskTask = this.makeTask("risk-assess", "Assess token risk", request.structured ?? {});
      tasks.push(riskTask);
      phases.set(0, [riskTask.id]);
    } else if (content.includes("portfolio") || content.includes("balance")) {
      const portfolioTask = this.makeTask("portfolio-scan", "Scan wallet portfolio", request.structured ?? {});
      tasks.push(portfolioTask);
      phases.set(0, [portfolioTask.id]);
    } else if (content.includes("whale") || content.includes("track") || content.includes("monitor")) {
      const whaleTask = this.makeTask("whale-track", "Monitor whale activity", request.structured ?? {});
      tasks.push(whaleTask);
      phases.set(0, [whaleTask.id]);
    } else {
      // Default: risk assessment as a safe fallback
      const riskTask = this.makeTask("risk-assess", "Assess token risk", request.structured ?? {});
      tasks.push(riskTask);
      phases.set(0, [riskTask.id]);
    }

    return { tasks, phases };
  }

  private async executeTask(session: Session, task: Task): Promise<SkillOutput> {
    task.status = "running";

    this.sessions.record(session, SessionEventType.SkillSelected, {
      taskId: task.id,
      skill: task.skillName,
    });

    const result = await this.executor.executeSkill(session, {
      skillName: task.skillName,
      params: task.params,
    });

    task.status = result.success ? "completed" : "failed";
    task.result = result;
    task.error = result.error;

    return result;
  }

  private assembleResponse(
    session: Session,
    plan: OrchestrationPlan,
    request: TransportMessage,
  ): TransportMessage {
    const completed = plan.tasks.filter((t) => t.status === "completed");
    const failed = plan.tasks.filter((t) => t.status === "failed");
    const denied = plan.tasks.filter((t) => t.status === "denied");

    const parts: string[] = [];

    for (const task of completed) {
      parts.push(`[${task.skillName}] ${JSON.stringify(task.result?.data)}`);
    }
    for (const task of failed) {
      parts.push(`[${task.skillName}] FAILED: ${task.error}`);
    }
    for (const task of denied) {
      parts.push(`[${task.skillName}] DENIED: ${task.error}`);
    }

    return {
      sessionId: session.id,
      content: parts.join("\n\n"),
      structured: {
        tasks: plan.tasks.map((t) => ({
          skill: t.skillName,
          status: t.status,
          data: t.result?.data,
          error: t.error,
        })),
      },
      channel: request.channel,
    };
  }

  private makeTask(
    skillName: string,
    description: string,
    params: Record<string, unknown>,
  ): Task {
    return {
      id: makeId(),
      description,
      skillName,
      params,
      status: "pending",
    };
  }
}
