"use client";

import { useState } from "react";
import { SWRConfig } from "swr";
import { DashboardNavbar } from "@/components/dashboard/dashboard-navbar";
import { PortfolioOverview } from "@/components/dashboard/portfolio-overview";
import { OpportunitiesFeed } from "@/components/dashboard/opportunities-feed";
import { OpportunityDetailView } from "@/components/dashboard/opportunity-detail";
import { KalshiAccount } from "@/components/dashboard/kalshi-account";

export default function Home() {
  const [selectedOpportunityId, setSelectedOpportunityId] = useState<
    string | null
  >(null);

  return (
    <SWRConfig
      value={{
        revalidateOnFocus: true,
        revalidateOnReconnect: true,
        errorRetryCount: 3,
      }}
    >
      <div className="flex flex-col min-h-screen bg-background noise-bg">
        <DashboardNavbar />

        <main className="flex-1 p-6 overflow-y-auto">
          <div className="max-w-[1800px] mx-auto space-y-6">
            <PortfolioOverview />

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-3 space-y-6">
                <KalshiAccount />
              </div>

              <div className="lg:col-span-3">
                <OpportunitiesFeed
                  onSelectOpportunity={setSelectedOpportunityId}
                  selectedId={selectedOpportunityId}
                />
              </div>

              <div className="lg:col-span-6">
                <OpportunityDetailView
                  opportunityId={selectedOpportunityId}
                  onClose={() => setSelectedOpportunityId(null)}
                />
              </div>
            </div>
          </div>
        </main>
      </div>
    </SWRConfig>
  );
}
