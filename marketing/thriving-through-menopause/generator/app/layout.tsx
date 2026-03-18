import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TTM Marketing Generator | Thriving Through Menopause 2026",
  description:
    "AI-powered marketing copy and image prompt generator for the Thriving Through Menopause Symposium 2026.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
