import type { Metadata } from "next";

export const metadata: Metadata = {
  // REPLACE: Update with client name
  title: "[CLIENT NAME] — AI Content Generator",
  description: "Generate on-brand marketing copy",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0 }}>{children}</body>
    </html>
  );
}
