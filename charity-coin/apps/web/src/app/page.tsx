import Link from "next/link";
import { ArrowRight, Flame, Heart, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FeaturedCauses } from "./featured-causes";
import { StatsBar } from "./stats-bar";

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="gradient-hero text-white">
        <div className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
              Convert Value.{" "}
              <span className="text-secondary-400">Create Impact.</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-primary-100">
              Charity Coin (CHA) is a deflationary token on Base that lets you
              convert your crypto into real-world impact. Every conversion burns
              CHA permanently while funding verified charitable causes.
            </p>
            <div className="mt-10 flex items-center justify-center gap-4 flex-wrap">
              <Link href="/convert">
                <Button size="lg" variant="secondary">
                  Buy CHA <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/causes">
                <Button
                  size="lg"
                  variant="outline"
                  className="border-white text-white hover:bg-white/10 hover:text-white"
                >
                  Explore Causes
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <StatsBar />

      {/* How It Works */}
      <section className="py-20 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900">How It Works</h2>
            <p className="mt-3 text-gray-500">
              Three simple steps to create real-world impact
            </p>
          </div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            {/* Step 1 */}
            <div className="relative flex flex-col items-center text-center p-8">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-100 text-primary-700 mb-6">
                <Zap className="h-8 w-8" />
              </div>
              <div className="absolute top-12 left-[calc(50%+48px)] hidden w-[calc(100%-96px)] border-t-2 border-dashed border-gray-200 md:block" />
              <span className="mb-2 inline-block rounded-full bg-primary-700 px-3 py-1 text-xs font-semibold text-white">
                Step 1
              </span>
              <h3 className="text-xl font-semibold text-gray-900">Buy CHA</h3>
              <p className="mt-2 text-sm text-gray-500">
                Purchase Charity Coin (CHA) tokens on Base using ETH or any
                supported token via DEX.
              </p>
            </div>

            {/* Step 2 */}
            <div className="relative flex flex-col items-center text-center p-8">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-secondary-100 text-secondary-700 mb-6">
                <Heart className="h-8 w-8" />
              </div>
              <div className="absolute top-12 left-[calc(50%+48px)] hidden w-[calc(100%-96px)] border-t-2 border-dashed border-gray-200 md:block" />
              <span className="mb-2 inline-block rounded-full bg-secondary-500 px-3 py-1 text-xs font-semibold text-white">
                Step 2
              </span>
              <h3 className="text-xl font-semibold text-gray-900">
                Choose a Cause
              </h3>
              <p className="mt-2 text-sm text-gray-500">
                Select from verified charitable causes: Health, Education,
                Environment, Water, or Hunger.
              </p>
            </div>

            {/* Step 3 */}
            <div className="flex flex-col items-center text-center p-8">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-red-100 text-red-600 mb-6">
                <Flame className="h-8 w-8" />
              </div>
              <span className="mb-2 inline-block rounded-full bg-red-500 px-3 py-1 text-xs font-semibold text-white">
                Step 3
              </span>
              <h3 className="text-xl font-semibold text-gray-900">
                Convert &amp; Impact
              </h3>
              <p className="mt-2 text-sm text-gray-500">
                Convert CHA to Cause Tokens. 95% of CHA is burned permanently,
                5% funds the charity and operations.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Causes */}
      <section className="py-20 bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900">
              Featured Causes
            </h2>
            <p className="mt-3 text-gray-500">
              Choose a cause and start creating impact today
            </p>
          </div>
          <FeaturedCauses />
        </div>
      </section>

      {/* Deflationary Explainer */}
      <section className="py-20 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900">
              Deflationary by Design
            </h2>
            <p className="mt-3 text-gray-500">
              Every conversion permanently reduces the CHA supply, increasing
              scarcity and value for holders.
            </p>
          </div>

          <div className="mx-auto max-w-2xl">
            <div className="relative rounded-2xl border border-gray-200 bg-gradient-to-b from-white to-gray-50 p-8">
              {/* Flow visualization */}
              <div className="space-y-6">
                <div className="flex items-center gap-4 rounded-xl bg-primary-50 p-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary-700 text-white font-bold">
                    100
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">
                      100 CHA Converted
                    </p>
                    <p className="text-sm text-gray-500">
                      User initiates conversion to a Cause Token
                    </p>
                  </div>
                </div>

                <div className="ml-6 border-l-2 border-dashed border-gray-200 py-2 pl-8">
                  <div className="flex items-center gap-3 text-sm text-gray-500">
                    <Flame className="h-4 w-4 text-secondary-500" />
                    <span>
                      <strong className="text-secondary-600">
                        95 CHA burned
                      </strong>{" "}
                      - permanently removed from supply
                    </span>
                  </div>
                </div>

                <div className="ml-6 border-l-2 border-dashed border-gray-200 py-2 pl-8">
                  <div className="space-y-2 text-sm text-gray-500">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-green-500" />
                      <span>2.5 CHA to charity wallet</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-blue-500" />
                      <span>1.5 CHA to liquidity pool</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-purple-500" />
                      <span>1.0 CHA to operations</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4 rounded-xl bg-emerald-50 p-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white font-bold text-sm">
                    100
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">
                      100 Cause Tokens Minted
                    </p>
                    <p className="text-sm text-gray-500">
                      User receives Cause Tokens representing their impact
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="gradient-hero text-white py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold">Ready to Make a Difference?</h2>
          <p className="mt-4 text-lg text-primary-100 max-w-2xl mx-auto">
            Join thousands of people using crypto for good. Every CHA token
            converted creates real impact while making the remaining supply more
            valuable.
          </p>
          <div className="mt-8 flex items-center justify-center gap-4 flex-wrap">
            <Link href="/convert">
              <Button size="lg" variant="secondary">
                Start Converting <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/causes">
              <Button
                size="lg"
                variant="outline"
                className="border-white text-white hover:bg-white/10 hover:text-white"
              >
                View All Causes
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
