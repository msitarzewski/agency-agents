import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { formatUnits } from "viem";

/**
 * Merge class names with Tailwind conflict resolution.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a CHA token amount (18 decimals) to a human-readable string.
 */
export function formatCHA(amount: bigint, decimals: number = 18): string {
  const formatted = formatUnits(amount, decimals);
  const num = parseFloat(formatted);

  if (num >= 1_000_000) {
    return `${(num / 1_000_000).toFixed(2)}M`;
  }
  if (num >= 1_000) {
    return `${(num / 1_000).toFixed(2)}K`;
  }
  if (num < 0.01 && num > 0) {
    return `< 0.01`;
  }
  return num.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
}

/**
 * Shorten an Ethereum address to 0x1234...5678 format.
 */
export function shortenAddress(address: string, chars: number = 4): string {
  if (!address) return "";
  return `${address.slice(0, chars + 2)}...${address.slice(-chars)}`;
}

/**
 * Cause color map for the 5 initial causes.
 */
export const causeColors: Record<
  string,
  { bg: string; text: string; border: string; light: string; badge: string }
> = {
  HEALTH: {
    bg: "bg-health-red",
    text: "text-health-red",
    border: "border-health-red",
    light: "bg-health-red-light",
    badge: "bg-red-100 text-red-800",
  },
  EDU: {
    bg: "bg-edu-blue",
    text: "text-edu-blue",
    border: "border-edu-blue",
    light: "bg-edu-blue-light",
    badge: "bg-blue-100 text-blue-800",
  },
  ENV: {
    bg: "bg-env-green",
    text: "text-env-green",
    border: "border-env-green",
    light: "bg-env-green-light",
    badge: "bg-green-100 text-green-800",
  },
  WATER: {
    bg: "bg-water-cyan",
    text: "text-water-cyan",
    border: "border-water-cyan",
    light: "bg-water-cyan-light",
    badge: "bg-cyan-100 text-cyan-800",
  },
  HUNGER: {
    bg: "bg-hunger-orange",
    text: "text-hunger-orange",
    border: "border-hunger-orange",
    light: "bg-hunger-orange-light",
    badge: "bg-orange-100 text-orange-800",
  },
};

/**
 * Static cause metadata used for display across the dApp.
 */
export interface CauseInfo {
  symbol: string;
  name: string;
  description: string;
  slug: string;
  icon: string;
}

export const CAUSES: CauseInfo[] = [
  {
    symbol: "HEALTH",
    name: "Global Health",
    description:
      "Fund medical research, healthcare access, and disease prevention worldwide.",
    slug: "health",
    icon: "Heart",
  },
  {
    symbol: "EDU",
    name: "Education",
    description:
      "Support education access, scholarships, and learning resources for communities in need.",
    slug: "education",
    icon: "GraduationCap",
  },
  {
    symbol: "ENV",
    name: "Environment",
    description:
      "Protect ecosystems, combat climate change, and promote sustainability initiatives.",
    slug: "environment",
    icon: "TreePine",
  },
  {
    symbol: "WATER",
    name: "Clean Water",
    description:
      "Provide clean drinking water and sanitation infrastructure to underserved regions.",
    slug: "water",
    icon: "Droplets",
  },
  {
    symbol: "HUNGER",
    name: "Zero Hunger",
    description:
      "Fight hunger through food aid, sustainable agriculture, and nutrition programs.",
    slug: "hunger",
    icon: "Wheat",
  },
];

/**
 * Get cause info by slug.
 */
export function getCauseBySlug(slug: string): CauseInfo | undefined {
  return CAUSES.find((c) => c.slug === slug);
}

/**
 * Fee breakdown percentages (basis points).
 */
export const FEE_BREAKDOWN = {
  charityBps: 250, // 2.5%
  liquidityBps: 150, // 1.5%
  opsBps: 100, // 1.0%
  burnPercent: 95, // 95% of CHA is burned
} as const;
