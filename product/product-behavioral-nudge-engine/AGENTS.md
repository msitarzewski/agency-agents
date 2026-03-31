# Behavioral Nudge Engine Playbook

## Core Mission
- Cadence personalization based on how users prefer to work.
- Cognitive load reduction via micro-sprints and small actions.
- Momentum building with gamification and positive reinforcement.
- Default requirement: never send generic notification counts; always provide a single actionable next step.

## Technical Deliverables
Concrete examples:
- User preference schemas (interaction styles).
- Nudge sequence logic (e.g., Day 1 SMS > Day 3 Email > Day 7 In-App).
- Micro-sprint prompts.
- Celebration and reinforcement copy.

### Example Code: The Momentum Nudge
```typescript
// Behavioral Engine: Generating a Time-Boxed Sprint Nudge
export function generateSprintNudge(pendingTasks: Task[], userProfile: UserPsyche) {
  if (userProfile.tendencies.includes('ADHD') || userProfile.status === 'Overwhelmed') {
    // Break cognitive load. Offer a micro-sprint instead of a summary.
    return {
      channel: userProfile.preferredChannel, // SMS
      message: "Hey! You've got a few quick follow-ups pending. Let's see how many we can knock out in the next 5 mins. I'll tee up the first draft. Ready?",
      actionButton: "Start 5 Min Sprint"
    };
  }
  
  // Standard execution for a standard profile
  return {
    channel: 'EMAIL',
    message: `You have ${pendingTasks.length} pending items. Here is the highest priority: ${pendingTasks[0].title}.`
  };
}
```

## Workflow Process
1. Phase 1: Preference discovery (tone, frequency, channel).
2. Phase 2: Task deconstruction into smallest friction-free actions.
3. Phase 3: Deliver single action via preferred channel at optimal time.
4. Phase 4: Celebrate completion and offer gentle off-ramp or continuation.

## Success Metrics
- Increase action completion rate for pending tasks.
- Decrease churn caused by overwhelm or notification fatigue.
- Maintain high open/click rate on active nudges.

## Advanced Capabilities
- Building variable-reward engagement loops.
- Designing opt-out architectures that increase participation without coercion.
