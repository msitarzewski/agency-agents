import OpenAI from "openai";
import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const maxDuration = 120;

const sizeForChannel: Record<string, "1024x1024" | "1792x1024" | "1024x1792"> = {
  instagram_story: "1024x1792",
  tiktok: "1024x1792",
  facebook_ad: "1792x1024",
  linkedin: "1792x1024",
  twitter: "1792x1024",
};

export async function POST(request: NextRequest) {
  const { prompt, channel } = await request.json();

  if (!prompt) {
    return new Response(JSON.stringify({ error: "prompt is required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const client = new OpenAI({
    apiKey: process.env.jillycontent,
  });

  const size = (channel && sizeForChannel[channel]) ?? "1024x1024";

  try {
    const response = await client.images.generate({
      model: "dall-e-3",
      prompt,
      n: 1,
      size,
      quality: "hd",
    });

    const imageUrl = response.data?.[0]?.url;

    return new Response(JSON.stringify({ url: imageUrl }), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
