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
  title: "Charity Coin - Convert Value. Create Impact.",
  description:
    "A deflationary token on Base (Coinbase L2) that lets you buy CHA tokens and convert them into Cause Tokens, directing funds to verified charities while permanently burning CHA supply.",
  keywords: [
    "charity",
    "crypto",
    "base",
    "web3",
    "donate",
    "deflationary",
    "cause tokens",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen flex flex-col font-sans">
        <Providers>
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}
