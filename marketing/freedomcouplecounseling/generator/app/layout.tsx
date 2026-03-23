import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FCC Marketing Generator | Freedom Couple Counselling",
  description:
    "AI-powered marketing copy and image prompt generator for Freedom Couple Counselling.",
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
