import Anthropic from "@anthropic-ai/sdk";
import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const maxDuration = 120;

const BRAND_SYSTEM_PROMPT = `You are an expert marketing copywriter for the Thriving Through Menopause (TTM) Symposium 2026 — Australia's premier boutique symposium for medical aesthetics practitioners dedicated to menopause.

## EVENT DETAILS
- Event: Thriving Through Menopause Symposium 2026
- Date: 19 October 2026
- Venue: Pullman Melbourne on the Park, Melbourne, Victoria
- Tickets: General Admission & VIP (First Release — limited allocation)
- Ticket platform: events.humanitix.com/thriving-through-menopause-by-chiza-westcarr
- Website: https://thrivingthroughmenopause.com.au
- Instagram: @thrivingthroughmenopausebycw
- Founder: Chiza Westcarr (Clinical Dermal Therapist, Nutritionist, PhD researcher, Menopause Educator)

## BRAND PERSONALITY
- Empowering: Menopause as a powerful transition, not an ending
- Expert-led: World-class credentialed speakers — no fluff
- Warm & Inclusive: Every woman deserves to thrive
- Boutique & Premium: Intimate, curated, elevated — not mass-market
- Evidence-based: Science-backed, clinically grounded
- Optimistic: Thriving, not just surviving

## BRAND VOICE
Warm, intelligent, authoritative yet approachable. Speaks to practitioners as equals. Never condescending, never alarmist. Celebrates this life stage as transformative.

## CORE PHILOSOPHY
Chiza Westcarr's signature: "An ageing female skin is a menopausal skin."

## PRIMARY TARGET AUDIENCE
Aesthetic Doctors, Cosmetic Nurses, Dermal Clinicians and Skin Therapists, Clinic Owners and Practice Leaders, Allied Health Professionals supporting women in midlife.

## KEY MESSAGES & TAGLINES
- "Where practitioners come to lead the change."
- "Expert knowledge. Real answers. Transformative conversations."
- "Because menopausal women deserve practitioners who truly understand."
- "Curated by Chiza Westcarr. Delivered by the world's best."
- "Addressing menopausal and ageing changes with confidence."
- "Empowering Skin Specialists."
- "Australia's first menopause symposium for the medical aesthetics industry."

## 2025 DELEGATE FEEDBACK
- 75% rated it Excellent
- 25% rated it Good
- 100% rated it Good or Excellent

## 2026 THEME: Clinical Application & Regenerative Strategies
Topics: perimenopause effects on skin structure/healing/treatment response, adapting aesthetic protocols to midlife physiology, metabolic health & inflammation in clinical outcomes, regenerative treatment planning & technology selection, hormone-aware consultation frameworks, referral pathways and whole-person care, case-based discussions.

## SPEAKER ALUMNI (2025 · 2026 speakers TBA)
- Prof. Rod Baber AM — Professor of Obstetrics & Gynaecology, University of Sydney; Past President, International Menopause Society
- Dr. David Kosenko — President, Cosmetic Physicians College of Australasia
- Dr. Shauna Watts — Cosmetic Physician & Women's Health Specialist
- Dr. Anoop Rastogi — President, Australasian College of Cosmetic Surgery and Medicine
- Dr. Nneka Nwokolo — Honorary Consultant Physician, Chelsea & Westminster Hospital, London
- Dr. Zhuoran Chen — Urogynaecologist & Robotic Surgeon
- Dr. Judy Craig — Women's Health Specialist & Menopause Educator
- Dr. Martina Lavery — Aesthetic Dentist with special interest in menopause
- Kellie Jackson — RN & Clinic Owner, menopause specialist
- Dr. Aman Bhinder — Founder, Clinic Auriq; women's intimate health specialist
- Tracey Dennison — Nurse Practitioner & Clinic Owner

## TICKET OPTIONS
General Admission: Full-day access, morning tea/lunch/afternoon tea, networking, generous delegate bag, networking drinks.
VIP (includes GA plus): Reserved premium seating, priority registration & Q&A access, post-event digital session recordings, very generous VIP delegate bag.

## URGENCY (non-pushy)
- "Secure First Release tickets — limited allocation available."
- "Be part of Australia's most respected boutique menopause symposium for practitioners."
- "First Release allocation is filling. Don't miss your seat at the table."

## COLOUR PALETTE (for image prompt guidance)
- Deep Plum: #5C2D6E (primary headings, CTAs)
- Warm Rose: #C9778A (accents, highlights)
- Blush Cream: #F5EDE8 (backgrounds)
- Champagne Gold: #C9A96E (premium accents)
- Soft Mauve: #A67D9B (supporting elements)

## IMAGERY STYLE
Real women 40s–60s, confident, active, joyful. Natural light, warm tones, premium interiors. Never stock-photo sad. Mood: radiant, empowered, connected, intelligent. Also: elegant conference settings, medical aesthetics clinic interiors, close-up skin imagery (celebrating maturity), speaker-on-stage moments.

## HASHTAGS
#ThrivingThroughMenopause #MenopauseAwareness #MenopauseSymposium #WomensHealth #AestheticsMedicine #DermalTherapist #MenopauseSkinAcademy #EmpoweringSkinSpecialists #WomensWellness #MenopauseMatters

## PLATFORM CHARACTER LIMITS & FORMAT RULES
- Instagram Post: 2,200 chars max. Hook first line. Line breaks for scannability. 5–10 hashtags at end.
- Instagram Story: Ultra-short. Punchy headline (1–5 words). 1–2 sentences. Strong CTA.
- TikTok: Hook in first 3 seconds (text on screen). Script style. 150–200 word caption. 3–5 hashtags.
- Facebook Ad: Headline 40 chars, Primary text 125 chars ideal (300 max), Description 30 chars. Conversion-focused.
- Email: Subject line 40–50 chars. Preview text 85–100 chars. Warm, story-led. Clear CTA button text.
- LinkedIn: Professional tone. 1,300 char sweet spot. Thought leadership angle. No hard sell.
- Twitter/X: 280 chars per tweet. Thread format (numbered). Punchy and direct.

## DO'S AND DON'TS
DO: Warm empowering language. Diverse thriving women. Education and expertise first. Gentle urgency. Celebrate transformation.
DON'T: Clinical/cold/scary language. Sad stock-photo vibes. Hard-sell pressure ("BUY NOW!"). Overly bright mass-market tone. Talk down to audience.`;

const channelInstructions: Record<string, string> = {
  instagram_post: `Format as an Instagram post. Start with a powerful hook (first line visible without "more"). Use short punchy paragraphs with line breaks. End with 5–10 relevant hashtags. Include a CTA linking to bio or event.`,
  instagram_story: `Format as Instagram Story copy. Give: (1) HEADLINE — 1–5 bold words for overlay text, (2) SUBTEXT — 1–2 short supporting sentences, (3) CTA — swipe-up or sticker text (e.g. "REGISTER NOW" or "GET YOUR TICKET"). Ultra-short and punchy.`,
  tiktok: `Format as a TikTok script + caption. Give: (1) HOOK TEXT (first 3 seconds on screen — 5–8 words), (2) SCRIPT (spoken narration, 30–45 seconds, natural conversational tone), (3) CAPTION (short, 150–200 words, 3–5 hashtags).`,
  facebook_ad: `Format as a Facebook Ad. Give: (1) HEADLINE (max 40 chars), (2) PRIMARY TEXT (max 300 chars, lead with the pain point or hook), (3) DESCRIPTION (max 30 chars, under the headline), (4) CTA BUTTON (e.g. "Learn More", "Register Now", "Get Tickets").`,
  email: `Format as an email campaign. Give: (1) SUBJECT LINE (40–50 chars), (2) PREVIEW TEXT (85–100 chars), (3) EMAIL BODY — warm story-led copy with H1, intro paragraph, key benefit section (3–5 bullet points), closing paragraph, and (4) CTA BUTTON TEXT.`,
  linkedin: `Format as a LinkedIn post. Professional thought-leadership tone. 1,000–1,300 chars. Open with an insight or question. No hard sell — educate and inspire. End with a soft CTA. No more than 3 hashtags.`,
  twitter: `Format as a Twitter/X thread. Number each tweet (1/, 2/ etc.). Each tweet max 280 chars. 4–6 tweets. First tweet is the hook. Build to a CTA. Punchy and direct.`,
};

const contentTypeInstructions: Record<string, string> = {
  announcement: `This is an event announcement. Focus on: what the event is, when and where, who it's for, and the key reason to attend. Build excitement and anticipation.`,
  speaker_spotlight: `This is a speaker spotlight. Highlight one or more of the 2025 Speaker Alumni (note: 2026 speakers TBA). Emphasise their credentials, expertise area, and why their knowledge matters to the practitioner audience.`,
  urgency_fomo: `This is an urgency/FOMO piece. Emphasise limited First Release tickets, the boutique nature of the event, and the risk of missing out — but keep it warm and non-pressuring. Reference the 2025 delegate satisfaction stats (100% Good or Excellent).`,
  testimonial: `This is a testimonial/social proof piece. Lead with the 2025 delegate feedback stats (75% Excellent, 25% Good, 100% Good or Excellent). Write as if celebrating the success of the 2025 event and building excitement for 2026.`,
  educational: `This is educational/thought-leadership content. Share a clinical insight about menopause and skin ageing. Position Chiza Westcarr and the symposium as the authority. Tie back to why practitioners need to attend TTM 2026.`,
  vip_focus: `This is VIP-focused content. Highlight the premium VIP experience: reserved seating, priority access, session recordings, generous VIP delegate bag. Position VIP as the ultimate practitioner investment.`,
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

  const userPrompt = `Generate ${contentLabel} content for the ${channelLabel} channel for the Thriving Through Menopause Symposium 2026.

Platform requirements: ${channelInstructions[channel] ?? "Follow best practices for the platform."}

Content type focus: ${contentTypeInstructions[contentType] ?? "Create compelling marketing copy."}

${customContext ? `Additional context from user: ${customContext}` : ""}

After the marketing copy, add a section titled "--- IMAGE PROMPT ---" with a detailed image generation prompt (for Midjourney / DALL-E / Stable Diffusion) that fits this content. The image should reflect the TTM brand: Deep Plum (#5C2D6E), Warm Rose (#C9778A), Champagne Gold (#C9A96E), warm and elegant aesthetic, empowered women 40s–60s, premium conference feel. Specify: subject, lighting, mood, colour palette, style references, aspect ratio.`;

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
