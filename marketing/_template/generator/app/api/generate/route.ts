import Anthropic from "@anthropic-ai/sdk";
import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// Load brand guidelines as system context
// REPLACE: Update path to point to your client's brand-guidelines.md
function getBrandGuidelines(): string {
  try {
    const guidelinesPath = path.join(process.cwd(), "..", "brand-guidelines.md");
    return fs.readFileSync(guidelinesPath, "utf-8");
  } catch {
    return "Use a professional, warm, and empowering tone.";
  }
}

export async function POST(request: NextRequest) {
  const { channel, tone, audience, goal, cta, extraContext } = await request.json();

  const brandGuidelines = getBrandGuidelines();

  const systemPrompt = `You are an expert marketing copywriter. You always write on-brand copy based on the following brand guidelines:

${brandGuidelines}

Always follow the brand's voice, colour references, messaging hierarchy, and do's/don'ts.`;

  const userPrompt = `Generate marketing copy for the following:

Channel: ${channel}
Tone: ${tone}
Target Audience: ${audience}
Goal: ${goal}
CTA: ${cta}
${extraContext ? `Additional context: ${extraContext}` : ""}

Produce complete, ready-to-use copy. Format clearly with labels for each element (e.g. Headline, Body, CTA, Hashtags).`;

  const message = await client.messages.create({
    model: "claude-opus-4-6",
    max_tokens: 1024,
    system: systemPrompt,
    messages: [{ role: "user", content: userPrompt }],
  });

  const content = message.content[0];
  if (content.type !== "text") {
    return NextResponse.json({ error: "Unexpected response type" }, { status: 500 });
  }

  return NextResponse.json({ copy: content.text });
}
