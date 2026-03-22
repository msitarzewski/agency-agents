"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Flame, DollarSign, ArrowRightLeft, Plus, Users, Loader2 } from "lucide-react";
import { CAUSES, causeColors } from "@/lib/utils";

interface AdminStats {
  conversions: {
    total: number;
    totalChaBurned: string;
    totalFeesCollected: string;
    uniqueUsers: number;
  };
  causes: {
    total: number;
    active: number;
  };
  users: {
    total: number;
  };
  last24h: {
    conversions: number;
    volume: string;
  };
}

function formatBigNumber(raw: string): string {
  const n = Number(raw) / 1e18;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toFixed(0);
}

export default function AdminPage() {
  const [showForm, setShowForm] = useState(false);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    name: "",
    symbol: "",
    charityWallet: "",
    description: "",
  });

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001/api";
    fetch(`${apiUrl}/admin/stats`, {
      headers: { "x-api-key": "dev-admin-key-change-in-production" },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.conversions) setStats(data);
      })
      .catch(() => {
        // Stats not available
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4" /> Add Cause
        </Button>
      </div>

      {/* Platform Stats */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-4 mb-10">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary-100 text-secondary-700">
                <Flame className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total CHA Burned</p>
                <p className="text-2xl font-bold text-gray-900">
                  {loading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    formatBigNumber(stats?.conversions.totalChaBurned || "0")
                  )}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100 text-green-700">
                <DollarSign className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Fees Collected</p>
                <p className="text-2xl font-bold text-gray-900">
                  {loading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    formatBigNumber(stats?.conversions.totalFeesCollected || "0")
                  )}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
                <ArrowRightLeft className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Conversions</p>
                <p className="text-2xl font-bold text-gray-900">
                  {loading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    (stats?.conversions.total || 0).toLocaleString()
                  )}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100 text-purple-700">
                <Users className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Unique Users</p>
                <p className="text-2xl font-bold text-gray-900">
                  {loading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    (stats?.users.total || 0).toLocaleString()
                  )}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Add Cause Form */}
      {showForm && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Create New Cause</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="grid grid-cols-1 gap-4 md:grid-cols-2"
              onSubmit={(e) => {
                e.preventDefault();
                // TODO: Submit to API
                alert("Cause creation will be submitted via the API");
              }}
            >
              <div>
                <label
                  htmlFor="cause-name"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Cause Name
                </label>
                <input
                  id="cause-name"
                  type="text"
                  placeholder="e.g. Disaster Relief"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                />
              </div>
              <div>
                <label
                  htmlFor="cause-symbol"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Token Symbol
                </label>
                <input
                  id="cause-symbol"
                  type="text"
                  placeholder="e.g. RELIEF"
                  value={formData.symbol}
                  onChange={(e) =>
                    setFormData({ ...formData, symbol: e.target.value })
                  }
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                />
              </div>
              <div className="md:col-span-2">
                <label
                  htmlFor="charity-wallet"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Charity Wallet Address
                </label>
                <input
                  id="charity-wallet"
                  type="text"
                  placeholder="0x..."
                  value={formData.charityWallet}
                  onChange={(e) =>
                    setFormData({ ...formData, charityWallet: e.target.value })
                  }
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                />
              </div>
              <div className="md:col-span-2">
                <label
                  htmlFor="cause-description"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Description
                </label>
                <textarea
                  id="cause-description"
                  rows={3}
                  placeholder="Describe the cause..."
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                />
              </div>
              <div className="md:col-span-2">
                <Button type="submit">Create Cause Token</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Cause Management Table */}
      <Card>
        <CardHeader>
          <CardTitle>Cause Management</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-2 font-medium text-gray-500">
                    Cause
                  </th>
                  <th className="text-left py-3 px-2 font-medium text-gray-500">
                    Symbol
                  </th>
                  <th className="text-left py-3 px-2 font-medium text-gray-500">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                {CAUSES.map((cause) => {
                  const colors = causeColors[cause.symbol];
                  return (
                    <tr
                      key={cause.symbol}
                      className="border-b border-gray-100 last:border-0"
                    >
                      <td className="py-3 px-2 font-medium text-gray-900">
                        {cause.name}
                      </td>
                      <td className="py-3 px-2">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${colors?.badge || "bg-gray-100 text-gray-800"}`}
                        >
                          {cause.symbol}
                        </span>
                      </td>
                      <td className="py-3 px-2">
                        <span className="inline-flex rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                          Active
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
