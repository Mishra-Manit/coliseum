"use client";

import type React from "react";
import { MotionConfig } from "motion/react";
import { SWRConfig } from "swr";
import { TimezoneProvider } from "@/lib/timezone-context";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig
      value={{
        revalidateOnFocus: true,
        revalidateOnReconnect: true,
        keepPreviousData: true,
        errorRetryCount: 3,
      }}
    >
      <MotionConfig reducedMotion="user">
        <TimezoneProvider>{children}</TimezoneProvider>
      </MotionConfig>
    </SWRConfig>
  );
}
