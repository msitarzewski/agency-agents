"use client";

import { useState, useEffect } from "react";
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
import { Vote, Clock, CheckCircle2, XCircle, Loader2 } from "lucide-react";

interface Proposal {
  id: number;
  proposalId: string;
  title: string;
  description: string;
  status: string;
  votesFor: string;
  votesAgainst: string;
  startBlock: number;
  endBlock: number;
  proposer: string;
  createdAt: string;
}

const SAMPLE_PROPOSALS: Proposal[] = [
  {
    id: 1,
    proposalId: "1",
    title: "Add Disaster Relief as a new cause category",
    description:
      "Proposal to create a RELIEF cause token for rapid disaster relief funding with verified NGO partners.",
    status: "active",
    votesFor: "245000000000000000000000",
    votesAgainst: "12000000000000000000000",
    startBlock: 100000,
    endBlock: 136000,
    proposer: "0x1234567890123456789012345678901234567890",
    createdAt: new Date().toISOString(),
  },
  {
    id: 2,
    proposalId: "2",
    title: "Reduce conversion fee from 5% to 4%",
    description:
      "Lower the total fee to increase the burn rate and make conversions more attractive for users.",
    status: "active",
    votesFor: "180000000000000000000000",
    votesAgainst: "95000000000000000000000",
    startBlock: 98000,
    endBlock: 134000,
    proposer: "0x2345678901234567890123456789012345678901",
    createdAt: new Date().toISOString(),
  },
  {
    id: 3,
    proposalId: "3",
    title: "Partner with UNICEF for Education cause",
    description:
      "Establish UNICEF as the verified charity partner for the EDU cause token.",
    status: "passed",
    votesFor: "520000000000000000000000",
    votesAgainst: "30000000000000000000000",
    startBlock: 80000,
    endBlock: 116000,
    proposer: "0x3456789012345678901234567890123456789012",
    createdAt: new Date(Date.now() - 7 * 86400000).toISOString(),
  },
];

function formatVotes(raw: string): string {
  const n = Number(raw) / 1e18;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return n.toFixed(0);
}

function getStatusBadge(status: string) {
  switch (status) {
    case "active":
      return { bg: "bg-green-100 text-green-800", icon: Clock, label: "Active" };
    case "passed":
    case "executed":
      return { bg: "bg-gray-100 text-gray-600", icon: CheckCircle2, label: "Passed" };
    case "defeated":
      return { bg: "bg-red-100 text-red-800", icon: XCircle, label: "Defeated" };
    default:
      return { bg: "bg-yellow-100 text-yellow-800", icon: Clock, label: status };
  }
}

export default function GovernancePage() {
  const { isConnected } = useAccount();
  const [proposals, setProposals] = useState<Proposal[]>(SAMPLE_PROPOSALS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001/api";
    fetch(`${apiUrl}/governance`)
      .then((res) => res.json())
      .then((data) => {
        if (data.proposals && data.proposals.length > 0) {
          setProposals(data.proposals);
        }
      })
      .catch(() => {
        // Keep sample data on error
      })
      .finally(() => setLoading(false));
  }, []);

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
                  {isConnected ? "0 CHA" : "--"}
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

        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
          </div>
        )}

        {!loading &&
          proposals.map((proposal) => {
            const forNum = Number(proposal.votesFor) / 1e18;
            const againstNum = Number(proposal.votesAgainst) / 1e18;
            const total = forNum + againstNum;
            const forPercent = total > 0 ? (forNum / total) * 100 : 0;
            const badge = getStatusBadge(proposal.status);
            const StatusIcon = badge.icon;

            return (
              <Card key={proposal.proposalId}>
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
                      className={`shrink-0 inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${badge.bg}`}
                    >
                      <StatusIcon className="h-3 w-3" />
                      {badge.label}
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
                    Proposed by {proposal.proposer.slice(0, 6)}...
                    {proposal.proposer.slice(-4)}
                  </p>
                </CardContent>
              </Card>
            );
          })}

        {!loading && proposals.length === 0 && (
          <Card>
            <CardContent className="p-12 text-center text-gray-500">
              No proposals yet. Connect your wallet and create the first one.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
