"use client"

import { useState } from "react"
import { Navbar } from "@/components/navbar"
import { Sidebar } from "@/components/sidebar"
import { MainContent } from "@/components/main-content"
import { BottomBanner } from "@/components/bottom-banner"

export default function Home() {
  const [selectedEvent, setSelectedEvent] = useState("us-election")

  return (
    <div className="flex flex-col min-h-screen bg-[#0e0e10]">
      <Navbar />
      <div className="flex flex-1 pt-[50px]">
        <Sidebar selectedEvent={selectedEvent} onSelectEvent={setSelectedEvent} />
        <MainContent selectedEvent={selectedEvent} />
      </div>
      <BottomBanner />
    </div>
  )
}
