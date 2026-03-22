"use client";

import { useAccount } from "wagmi";
import { ConnectButton } from "@rainbow-me/rainbowkit";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Vote, Clock, CheckCircle2, XCircle } from "lucide-react";

const SAMPLE_PROPOSALS = [
  {
    id: 1,
    title: "Add Disaster Relief as a new cause category",
    description:
      "Proposal to create a RELIEF cause token for rapid disaster relief funding with verified NGO partners.",
    status: "active" as const,
    votesFor: 245_000,
    votesAgainst: 12_000,
    endDate: "2026-04-05",
  },
  {
    id: 2,
    title: "Reduce conversion fee from 5% to 4%",
    description:
      "Lower the total fee to increase the burn rate and make conversions more attractive for users.",
    status: "active" as const,
    votesFor: 180_000,
    votesAgainst: 95_000,
    endDate: "2026-04-02",
  },
  {
    id: 3,
    title: "Partner with UNICEF for Education cause",
    description:
      "Establish UNICEF as the verified charity partner for the EDU cause token.",
    status: "passed" as const,
    votesFor: 520_000,
    votesAgainst: 30_000,
    endDate: "2026-03-15",
  },
];

function formatVotes(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return n.toString();
}

export default function GovernancePage() {
  const { isConnected } = useAccount();

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-gray-900">Governance</h1>
        <p className="mt-3 text-gray-500 max-w-2xl">
          CHA holders can vote on proposals to shape the future of Charity Coin.
          Propose new causes, adjust fees, and govern the protocol.
        </p>
      </div>

      {/* Voting Power */}
      <Card className="mb-8">
        <CardContent className="p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100 text-primary-700">
                <Vote className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Your Voting Power</p>
                <p className="text-xl font-bold text-gray-900">
                  {isConnected ? "0 CHA" : "—"}
                </p>
              </div>
            </div>
            {!isConnected ? (
              <ConnectButton />
            ) : (
              <Button>Create Proposal</Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Proposals */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-900">Proposals</h2>
        {SAMPLE_PROPOSALS.map((proposal) => {
          const total = proposal.votesFor + proposal.votesAgainst;
          const forPercent = total > 0 ? (proposal.votesFor / total) * 100 : 0;

          return (
            <Card key={proposal.id}>
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <CardTitle className="text-base">
                      {proposal.title}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      {proposal.description}
                    </CardDescription>
                  </div>
                  <span
                    className={`shrink-0 inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      proposal.status === "active"
                        ? "bg-green-100 text-green-800"
                        : "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {proposal.status === "active" ? (
                      <Clock className="h-3 w-3" />
                    ) : (
                      <CheckCircle2 className="h-3 w-3" />
                    )}
                    {proposal.status === "active" ? "Active" : "Passed"}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                {/* Vote Bar */}
                <div className="mb-3">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-green-700">
                      For: {formatVotes(proposal.votesFor)}
                    </span>
                    <span className="text-red-600">
                      Against: {formatVotes(proposal.votesAgainst)}
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-red-100 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-green-500"
                      style={{ width: `${forPercent}%` }}
                    />
                  </div>
                </div>

                {proposal.status === "active" && isConnected && (
                  <div className="flex gap-2 mt-4">
                    <Button size="sm" className="flex-1">
                      <CheckCircle2 className="h-4 w-4" /> Vote For
                    </Button>
                    <Button size="sm" variant="outline" className="flex-1">
                      <XCircle className="h-4 w-4" /> Vote Against
                    </Button>
                  </div>
                )}

                <p className="text-xs text-gray-400 mt-3">
                  {proposal.status === "active"
                    ? `Voting ends ${proposal.endDate}`
                    : `Ended ${proposal.endDate}`}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
