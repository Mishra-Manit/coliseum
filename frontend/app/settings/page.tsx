"use client";

import { MobileSettings } from "@/components/mobile/mobile-settings";

export default function SettingsPage() {
  return (
    <>
      {/* Only show on mobile; desktop redirects via link behavior */}
      <div className="lg:hidden">
        <MobileSettings />
      </div>
      {/* Desktop: redirect back to home (settings is a modal there) */}
      <div className="hidden lg:flex items-center justify-center h-screen bg-background">
        <p className="font-mono text-xs text-muted-foreground tracking-wider">
          <a href="/" className="text-primary hover:underline">
            Return to Dashboard
          </a>
        </p>
      </div>
    </>
  );
}
