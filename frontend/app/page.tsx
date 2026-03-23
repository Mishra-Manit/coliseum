"use client";

import { useState } from "react";
import { DashboardNavbar } from "@/components/dashboard/dashboard-navbar";
import { OpportunitiesFeed } from "@/components/dashboard/opportunities-feed";
import { OpportunityDetailView } from "@/components/dashboard/opportunity-detail";
import { PositionsLedgerPanel } from "@/components/dashboard/positions-ledger-panel";

export default function Home() {
  const [selectedOpportunityId, setSelectedOpportunityId] = useState<
    string | null
  >(null);

  return (
    <div className="flex flex-col h-screen bg-background tech-grid noise-bg overflow-hidden">
      <DashboardNavbar />

      <main className="flex-1 flex overflow-hidden">
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-0 overflow-hidden">
          {/* Left panel — positions + ledger */}
          <div className="lg:col-span-3 border-r border-border flex flex-col min-h-0 overflow-hidden">
            <PositionsLedgerPanel
              onSelectOpportunity={setSelectedOpportunityId}
            />
          </div>

          {/* Center panel — opportunities feed */}
          <div className="lg:col-span-3 border-r border-border flex flex-col min-h-0 overflow-hidden">
            <OpportunitiesFeed
              onSelectOpportunity={setSelectedOpportunityId}
              selectedId={selectedOpportunityId}
            />
          </div>

          {/* Right panel — opportunity detail */}
          <div className="lg:col-span-6 flex flex-col min-h-0 overflow-hidden">
            <OpportunityDetailView
              opportunityId={selectedOpportunityId}
              onClose={() => setSelectedOpportunityId(null)}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
