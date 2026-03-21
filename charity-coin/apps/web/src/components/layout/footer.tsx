import Link from "next/link";
import { Coins } from "lucide-react";

const FOOTER_LINKS = {
  Product: [
    { href: "/causes", label: "Causes" },
    { href: "/convert", label: "Convert" },
    { href: "/portfolio", label: "Portfolio" },
    { href: "/governance", label: "Governance" },
  ],
  Resources: [
    { href: "#", label: "Documentation" },
    { href: "#", label: "Whitepaper" },
    { href: "#", label: "Smart Contracts" },
    { href: "#", label: "Audits" },
  ],
  Community: [
    { href: "#", label: "Twitter / X" },
    { href: "#", label: "Discord" },
    { href: "#", label: "Telegram" },
    { href: "#", label: "GitHub" },
  ],
};

export function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-700 text-white">
                <Coins className="h-4 w-4" />
              </div>
              <span className="text-lg font-bold text-gray-900">
                Charity<span className="text-primary-700">Coin</span>
              </span>
            </Link>
            <p className="mt-3 text-sm text-gray-500">
              Convert value into impact. A deflationary token powering
              charitable causes on Base.
            </p>
          </div>

          {/* Link sections */}
          {Object.entries(FOOTER_LINKS).map(([section, links]) => (
            <div key={section}>
              <h3 className="text-sm font-semibold text-gray-900">{section}</h3>
              <ul className="mt-3 space-y-2">
                {links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-sm text-gray-500 transition-colors hover:text-primary-700"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 border-t border-gray-200 pt-6">
          <p className="text-center text-sm text-gray-400">
            &copy; {new Date().getFullYear()} Charity Coin. Built on Base. All
            rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
