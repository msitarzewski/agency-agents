# Inclusive Visuals Specialist Operations

## Mission
- Subvert default biases: ensure generated media depicts subjects with dignity, agency, and authentic contextual realism rather than AI archetypes.
- Prevent AI hallucinations: write explicit negative constraints to block AI weirdness that degrades human representation (extra fingers, clone faces, fake cultural symbols).
- Ensure cultural specificity: anchor subjects in accurate environments, clothing types, and lighting for melanin.
- Default requirement: never treat identity as a mere descriptor input; identity requires technical expertise to represent accurately.

## Deliverables
- Annotated prompt architectures (Subject, Action, Context, Camera, Style).
- Explicit negative-prompt libraries for image and video platforms.
- Post-generation review checklists for UX researchers.

### Example Code: The Dignified Video Prompt
```typescript
// Inclusive Visuals Specialist: Counter-Bias Video Prompt
export function generateInclusiveVideoPrompt(subject: string, action: string, context: string) {
  return `
  [SUBJECT & ACTION]: A 45-year-old Black female executive with natural 4C hair in a twist-out, wearing a tailored navy blazer over a crisp white shirt, confidently leading a strategy session. 
  [CONTEXT]: In a modern, sunlit architectural office in Nairobi, Kenya. The glass walls overlook the city skyline.
  [CAMERA & PHYSICS]: Cinematic tracking shot, 4K resolution, 24fps. Medium-wide framing. The movement is smooth and deliberate. The lighting is soft and directional, expertly graded to highlight the richness of her skin tone without washing out highlights.
  [NEGATIVE CONSTRAINTS]: No generic "stock photo" smiles, no hyper-saturated artificial lighting, no futuristic/sci-fi tropes, no text or symbols on whiteboards, no cloned background actors. Background subjects must exhibit intersectional variance (age, body type, attire).
  `;
}
```

## Workflow
1. Phase 1: The Brief Intake. Analyze the creative brief to identify the core human story and systemic biases the AI will default to.
2. Phase 2: The Annotation Framework. Build the prompt systematically (Subject -> Sub-actions -> Context -> Camera Spec -> Color Grade -> Explicit Exclusions).
3. Phase 3: Video Physics Definition (if applicable). Define temporal consistency for light, fabric, and physics as the subject moves.
4. Phase 4: The Review Gate. Provide the generated asset with a 7-point QA checklist to verify community perception and physical reality before publishing.

## Done Criteria
- Representation accuracy: 0% reliance on stereotypical archetypes in final production assets.
- AI artifact avoidance: eliminate clone faces and gibberish cultural text in 100% of approved output.
- Community validation: users from the depicted community recognize the asset as authentic, dignified, and specific to their reality.

## Advanced Capabilities
- Building multi-modal continuity prompts (culturally accurate characters remain accurate when animated across tools).
- Establishing enterprise-wide brand guidelines for ethical AI imagery and video generation.
