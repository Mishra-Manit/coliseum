"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, BarChart3, Settings } from "lucide-react";

const tabs = [
  { href: "/", icon: LayoutDashboard, label: "DASHBOARD" },
  { href: "/chart", icon: BarChart3, label: "CHARTS" },
  { href: "/settings", icon: Settings, label: "SETTINGS" },
] as const;

export function MobileBottomNav() {
  const pathname = usePathname();

  return (
    <div className="shrink-0 px-[21px] pt-3 pb-[21px] flex justify-center">
      <div className="flex gap-1 w-full h-[62px] rounded-[36px] bg-card border border-border p-1">
        {tabs.map(({ href, icon: Icon, label }) => {
          const isActive =
            href === "/"
              ? pathname === "/"
              : pathname.startsWith(href);

          return (
            <Link
              key={href}
              href={href}
              className={`flex-1 flex flex-col items-center justify-center gap-1 rounded-[26px] transition-colors ${
                isActive
                  ? "bg-primary/15 border border-primary/30"
                  : "border border-transparent"
              }`}
            >
              <Icon
                className={`h-[18px] w-[18px] ${
                  isActive ? "text-primary" : "text-muted-foreground/60"
                }`}
              />
              <span
                className={`font-mono text-[9px] font-semibold tracking-[0.05em] ${
                  isActive ? "text-primary" : "text-muted-foreground/60"
                }`}
              >
                {label}
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
