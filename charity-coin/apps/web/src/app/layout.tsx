import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Providers } from "@/components/providers";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://charitycoin.org"),
  title: {
    default: "Charity Coin - Convert Value. Create Impact.",
    template: "%s | Charity Coin",
  },
  description:
    "A deflationary token on Base that lets you convert CHA into Cause Tokens, directing funds to verified charities while permanently burning CHA supply.",
  keywords: [
    "charity",
    "crypto",
    "base",
    "web3",
    "donate",
    "deflationary",
    "cause tokens",
  ],
  openGraph: {
    type: "website",
    siteName: "Charity Coin",
    title: "Charity Coin - Convert Value. Create Impact.",
    description:
      "A deflationary token on Base that lets you convert CHA into Cause Tokens, directing funds to verified charities while permanently burning CHA supply.",
    url: "https://charitycoin.org",
  },
  twitter: {
    card: "summary_large_image",
    title: "Charity Coin - Convert Value. Create Impact.",
    description:
      "A deflationary token on Base that lets you convert CHA into Cause Tokens, directing funds to verified charities while permanently burning CHA supply.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen flex flex-col font-sans">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-4 focus:bg-white focus:text-primary-700 focus:underline"
        >
          Skip to content
        </a>
        <Providers>
          <Header />
          <main id="main-content" className="flex-1">
            {children}
          </main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}
