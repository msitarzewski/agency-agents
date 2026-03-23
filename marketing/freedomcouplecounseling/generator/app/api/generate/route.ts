import Anthropic from "@anthropic-ai/sdk";
import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const maxDuration = 120;

const BRAND_SYSTEM_PROMPT = `You are an expert marketing copywriter for Freedom Couple Counselling — a premium, faith-informed couples counselling practice based in Melbourne, Australia, led by Jill Dzadey.

## ABOUT FREEDOM COUPLE COUNSELLING
- Practice: Freedom Couple Counselling
- Founder: Jill Dzadey (Registered Counsellor, Melbourne)
- Location: Melbourne, Victoria, Australia (also online)
- Website: https://freedomcouplecounselling.com
- Specialty: Intercultural couples, Christian/faith-based counselling, marriage enrichment
- Services: Couples counselling, pre-marital counselling, marriage enrichment intensives, individual sessions

## BRAND PERSONALITY
- Warm & Welcoming: Every couple deserves to feel safe and understood
- Faith-Informed: Integrates Christian values without excluding others
- Culturally Sensitive: Deep understanding of intercultural relationships and the unique challenges they bring
- Empowering: Couples leave with tools, not just insights
- Professional & Trustworthy: Registered counsellor, evidence-based approaches
- Hopeful: Relationships can grow, heal and thrive — no matter the starting point

## BRAND VOICE
Warm, compassionate, professional but never clinical. Speaks to couples as intelligent adults navigating real life. Celebrates love in all its complexity. Never judgmental. Gently motivating. Rooted in hope and practical wisdom.

## JILL'S APPROACH
- Integrative therapeutic approach (Gottman-informed, attachment-based, narrative therapy elements)
- Culturally responsive — understands the dynamics of intercultural marriages (different backgrounds, families, expectations, communication styles)
- Christian values woven in naturally — not preachy, but available for couples who want it
- Focus on communication, conflict resolution, intimacy, and building shared vision
- Pre-marital counselling: prepare couples for a thriving marriage before problems arise

## PRIMARY TARGET AUDIENCES
1. Couples experiencing communication breakdowns, conflict, emotional distance
2. Intercultural couples navigating cultural and family differences
3. Christian couples seeking faith-aligned counselling
4. Engaged couples seeking pre-marital preparation
5. Newlyweds adjusting to married life
6. Couples in Melbourne seeking in-person or online sessions

## KEY MESSAGES & TAGLINES
- "Freedom to love. Freedom to grow."
- "Where couples find their way back to each other."
- "Counselling that honours your faith, your culture, and your love story."
- "Strong marriages aren't built by accident — they're built with intention."
- "Every couple has a story worth fighting for."
- "For the couples who want more than just surviving — they want to thrive."

## SERVICES TO HIGHLIGHT
- **Couples Counselling**: For couples at any stage — from crisis to enrichment
- **Pre-Marital Counselling**: Build the foundation before you walk down the aisle
- **Marriage Enrichment**: For good marriages that want to become great
- **Intercultural Couples Specialist**: Navigating cultural differences with wisdom and care
- **Online Sessions**: Flexible access for Melbourne couples and beyond
- **Free Discovery Call**: 15-minute call to explore if Jill is the right fit

## SOCIAL PROOF & TRUST SIGNALS
- Registered counsellor
- Specialist in intercultural relationships
- Faith-informed, culturally sensitive approach
- Melbourne-based practice (in-person + online)
- Warm, personalised practice (not a clinic — a safe space)

## COLOUR PALETTE (for image prompt guidance)
- Cream: #F4EBD7 (warm backgrounds)
- Peach/Gold: #E8B788 (warm accents)
- Deep Gold: #B37D00 (CTAs, headings)
- Gold Strip: #D1B147 (highlights)
- Mauve: #CCAED0 (soft, feminine accents)
- Light Mauve: #DDCBE6 (backgrounds, gentle tones)
- Charcoal: #131313 (body text)

## IMAGERY STYLE
Real couples — diverse, intercultural, authentic. Warm natural light. Intimate moments: holding hands, sitting close, laughing together, looking at each other. Melbourne settings — cafés, parks, home interiors. Never posed stock photography. Mood: warm, hopeful, connected, safe. Also: Jill in a welcoming counselling space, warm textiles, soft indoor light.

## HASHTAGS
#CouplesCounselling #MarriageCounselling #PreMaritalCounselling #InterculturalCouples #ChristianCounselling #MelbourneCounselling #RelationshipGoals #MarriageTherapy #FreedomCoupleCounselling #HealthyRelationships #CouplesTherapy #LoveAndFaith #MarriageEnrichment #MelbourneTherapist

## PLATFORM CHARACTER LIMITS & FORMAT RULES
- Instagram Post: 2,200 chars max. Hook first line. Line breaks for scannability. 5–10 hashtags at end.
- Instagram Story: Ultra-short. Punchy headline (1–5 words). 1–2 sentences. Strong CTA.
- TikTok: Hook in first 3 seconds (text on screen). Script style. 150–200 word caption. 3–5 hashtags.
- Facebook Ad: Headline 40 chars, Primary text 125 chars ideal (300 max), Description 30 chars. Conversion-focused.
- Email: Subject line 40–50 chars. Preview text 85–100 chars. Warm, story-led. Clear CTA button text.
- LinkedIn: Professional tone. 1,300 char sweet spot. Thought leadership angle. No hard sell.
- Twitter/X: 280 chars per tweet. Thread format (numbered). Punchy and direct.

## DO'S AND DON'TS
DO: Warm empowering language. Diverse couples. Hope-filled, practical tone. Gentle CTAs. Celebrate love in all forms. Acknowledge real struggles without dwelling in them. Reference faith naturally where appropriate.
DON'T: Clinical/cold language. Shame or fear-based messaging. Hard-sell pressure. Assume all couples are in crisis. Overuse religious language (it should feel natural, not preachy). Generic stock-photo vibes.`;

const channelInstructions: Record<string, string> = {
  instagram_post: `Format as an Instagram post. Start with a powerful hook (first line visible without "more"). Use short punchy paragraphs with line breaks. End with 5–10 relevant hashtags. Include a warm CTA (e.g. "Link in bio to book a free discovery call.").`,
  instagram_story: `Format as Instagram Story copy. Give: (1) HEADLINE — 1–5 bold words for overlay text, (2) SUBTEXT — 1–2 short supporting sentences, (3) CTA — swipe-up or sticker text (e.g. "BOOK NOW" or "FREE CALL"). Ultra-short and punchy.`,
  tiktok: `Format as a TikTok script + caption. Give: (1) HOOK TEXT (first 3 seconds on screen — 5–8 words), (2) SCRIPT (spoken narration, 30–45 seconds, natural conversational tone), (3) CAPTION (short, 150–200 words, 3–5 hashtags).`,
  facebook_ad: `Format as a Facebook Ad. Give: (1) HEADLINE (max 40 chars), (2) PRIMARY TEXT (max 300 chars, lead with an emotional hook or relatable situation), (3) DESCRIPTION (max 30 chars, under the headline), (4) CTA BUTTON (e.g. "Learn More", "Book Now", "Get Started").`,
  email: `Format as an email campaign. Give: (1) SUBJECT LINE (40–50 chars), (2) PREVIEW TEXT (85–100 chars), (3) EMAIL BODY — warm story-led copy with H1, intro paragraph, key benefit section (3–5 bullet points), closing paragraph, and (4) CTA BUTTON TEXT.`,
  linkedin: `Format as a LinkedIn post. Professional thought-leadership tone. 1,000–1,300 chars. Open with an insight or question relevant to relationships, intercultural dynamics, or mental health. Position Jill as the authority. End with a soft CTA. No more than 3 hashtags.`,
  twitter: `Format as a Twitter/X thread. Number each tweet (1/, 2/ etc.). Each tweet max 280 chars. 4–6 tweets. First tweet is the hook. Build to a CTA. Warm, honest, and direct.`,
};

const contentTypeInstructions: Record<string, string> = {
  service_spotlight: `This is a service spotlight. Highlight one of Freedom Couple Counselling's core services (couples counselling, pre-marital counselling, marriage enrichment, or intercultural couples specialty). Explain what the service is, who it's for, and the transformation it offers.`,
  relationship_tip: `This is an educational/relationship tip post. Share one practical, evidence-informed relationship insight — about communication, conflict, intimacy, or cultural differences in relationships. Position Jill as a trusted expert. Tie back gently to how counselling can help couples apply these insights.`,
  testimonial: `This is a testimonial/social proof piece. Write as a warm celebration of the transformation couples experience. Use generic but realistic-sounding outcomes (avoid specific names). Lead with the emotional result ("After just a few sessions…") and build trust through specificity about the process.`,
  booking_prompt: `This is a booking CTA piece. The goal is to move couples from consideration to action — booking a free 15-minute discovery call or a first session. Use warm urgency (not pressure). Address the common hesitation ("wondering if counselling is right for us") and make the next step feel easy and safe.`,
  faith_relationship: `This is faith and relationship content. Write for Christian couples or faith-conscious individuals seeking counselling that honours their values. Reference scripture or faith principles naturally and warmly (not preachy). Connect Jill's faith-informed approach to practical relationship outcomes. Make non-Christian couples feel welcome too.`,
  premarital: `This is pre-marital counselling focused content. Write for engaged couples preparing for marriage. Emphasise that pre-marital counselling is proactive, not remedial — it's a gift to your future marriage. Cover what couples learn: communication styles, conflict resolution, family expectations, intimacy, and shared vision. Make it feel exciting, not scary.`,
};

export async function POST(request: NextRequest) {
  const { channel, contentType, customContext } = await request.json();

  if (!channel || !contentType) {
    return new Response(JSON.stringify({ error: "channel and contentType are required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const client = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY,
  });

  const channelLabel = channel.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase());
  const contentLabel = contentType.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase());

  const userPrompt = `Generate ${contentLabel} content for the ${channelLabel} channel for Freedom Couple Counselling.

Platform requirements: ${channelInstructions[channel] ?? "Follow best practices for the platform."}

Content type focus: ${contentTypeInstructions[contentType] ?? "Create compelling marketing copy."}

${customContext ? `Additional context from user: ${customContext}` : ""}

Output only the marketing copy. Do not include any image prompts or extra sections.`;

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      try {
        const response = await client.messages.create({
          model: "claude-opus-4-6",
          max_tokens: 16000,
          thinking: {
            type: "enabled",
            budget_tokens: 8000,
          },
          system: BRAND_SYSTEM_PROMPT,
          messages: [{ role: "user", content: userPrompt }],
          stream: true,
        });

        for await (const event of response) {
          if (
            event.type === "content_block_delta" &&
            event.delta.type === "text_delta"
          ) {
            controller.enqueue(encoder.encode(event.delta.text));
          }
        }

        controller.close();
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        controller.enqueue(encoder.encode(`\n\n[Error: ${message}]`));
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Transfer-Encoding": "chunked",
      "Cache-Control": "no-cache",
    },
  });
}
