"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";

export type Timezone = "EST" | "PST";

const IANA: Record<Timezone, string> = {
  EST: "America/New_York",
  PST: "America/Los_Angeles",
};

interface TimezoneContextValue {
  tz: Timezone;
  setTz: (tz: Timezone) => void;
}

const TimezoneContext = createContext<TimezoneContextValue>({
  tz: "EST",
  setTz: () => {},
});

export function TimezoneProvider({ children }: { children: ReactNode }) {
  const [tz, setTzState] = useState<Timezone>("EST");

  useEffect(() => {
    const stored = localStorage.getItem("coliseum-tz") as Timezone | null;
    if (stored === "EST" || stored === "PST") setTzState(stored);
  }, []);

  const setTz = (next: Timezone) => {
    setTzState(next);
    localStorage.setItem("coliseum-tz", next);
  };

  return (
    <TimezoneContext.Provider value={{ tz, setTz }}>
      {children}
    </TimezoneContext.Provider>
  );
}

export function useTimezone() {
  return useContext(TimezoneContext);
}

/** Format a Date into the selected timezone, e.g. "03/07/2026, 02:14 PM EST" */
export function formatInTz(date: Date, tz: Timezone): string {
  const formatted = new Intl.DateTimeFormat("en-US", {
    timeZone: IANA[tz],
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  }).format(date);
  return `${formatted} ${tz}`;
}
