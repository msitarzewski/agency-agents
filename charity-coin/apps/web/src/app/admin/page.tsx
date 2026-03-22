"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Flame, DollarSign, ArrowRightLeft, Plus } from "lucide-react";
import { CAUSES, causeColors } from "@/lib/utils";

const DEMO_STATS = {
  totalBurned: "12,450,000",
  totalRaised: "$845,000",
  totalConversions: "3,287",
};

export default function AdminPage() {
  const [showForm, setShowForm] = useState(false);

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4" /> Add Cause
        </Button>
      </div>

      {/* Platform Stats */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3 mb-10">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary-100 text-secondary-700">
                <Flame className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total CHA Burned</p>
                <p className="text-2xl font-bold text-gray-900">
                  {DEMO_STATS.totalBurned}
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
                <p className="text-sm text-gray-500">Total Raised</p>
                <p className="text-2xl font-bold text-gray-900">
                  {DEMO_STATS.totalRaised}
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
                  {DEMO_STATS.totalConversions}
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
            <form className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cause Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Disaster Relief"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Token Symbol
                </label>
                <input
                  type="text"
                  placeholder="e.g. RELIEF"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Charity Wallet Address
                </label>
                <input
                  type="text"
                  placeholder="0x..."
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  placeholder="Describe the cause..."
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                />
              </div>
              <div className="md:col-span-2">
                <Button type="button">Create Cause Token</Button>
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
                  <th className="text-right py-3 px-2 font-medium text-gray-500">
                    Conversions
                  </th>
                  <th className="text-right py-3 px-2 font-medium text-gray-500">
                    CHA Burned
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
                      <td className="py-3 px-2 text-right text-gray-700">
                        {Math.floor(Math.random() * 800 + 200)}
                      </td>
                      <td className="py-3 px-2 text-right text-gray-700">
                        {(Math.random() * 3 + 1).toFixed(1)}M
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
