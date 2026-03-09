"use client";

import type React from "react";
import { SWRConfig } from "swr";
import { TimezoneProvider } from "@/lib/timezone-context";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig
      value={{
        revalidateOnFocus: true,
        revalidateOnReconnect: true,
        errorRetryCount: 3,
      }}
    >
      <TimezoneProvider>{children}</TimezoneProvider>
    </SWRConfig>
  );
}
