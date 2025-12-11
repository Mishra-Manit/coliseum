"use client"

import { useState } from "react"
import { ChevronLeft, ChevronDown, TrendingUp, Vote, Trophy, Zap, Globe, Film, Cpu, DollarSign } from "lucide-react"

const liveEvents = [
  {
    id: "us-election",
    name: "2024 US Election",
    category: "Politics",
    viewers: "142.1K",
    icon: Vote,
    color: "text-blue-500",
    bgColor: "bg-blue-500/20",
    modelsActive: 8,
  },
  {
    id: "super-bowl",
    name: "Super Bowl LIX Winner",
    category: "Sports",
    viewers: "89.3K",
    icon: Trophy,
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/20",
    modelsActive: 8,
  },
  {
    id: "fed-rate",
    name: "Fed Rate Decision",
    category: "Finance",
    viewers: "67.2K",
    icon: TrendingUp,
    color: "text-green-500",
    bgColor: "bg-green-500/20",
    modelsActive: 8,
  },
  {
    id: "bitcoin-100k",
    name: "Bitcoin Hits $100K",
    category: "Crypto",
    viewers: "54.8K",
    icon: DollarSign,
    color: "text-orange-500",
    bgColor: "bg-orange-500/20",
    modelsActive: 7,
  },
  {
    id: "spacex-launch",
    name: "SpaceX Starship Success",
    category: "Technology",
    viewers: "43.1K",
    icon: Zap,
    color: "text-purple-500",
    bgColor: "bg-purple-500/20",
    modelsActive: 8,
  },
  {
    id: "taiwan-conflict",
    name: "Taiwan Strait Escalation",
    category: "Geopolitics",
    viewers: "38.7K",
    icon: Globe,
    color: "text-red-500",
    bgColor: "bg-red-500/20",
    modelsActive: 6,
  },
  {
    id: "oscar-winner",
    name: "Best Picture Oscar 2025",
    category: "Entertainment",
    viewers: "31.4K",
    icon: Film,
    color: "text-pink-500",
    bgColor: "bg-pink-500/20",
    modelsActive: 8,
  },
  {
    id: "ai-regulation",
    name: "US AI Regulation Bill",
    category: "Technology",
    viewers: "28.9K",
    icon: Cpu,
    color: "text-cyan-500",
    bgColor: "bg-cyan-500/20",
    modelsActive: 8,
  },
]

interface SidebarProps {
  selectedEvent: string
  onSelectEvent: (eventId: string) => void
}

export function Sidebar({ selectedEvent, onSelectEvent }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={`fixed left-0 top-[50px] bottom-0 ${collapsed ? "w-[50px]" : "w-[240px]"} bg-[#1f1f23] border-r border-[#2f2f35] overflow-y-auto transition-all duration-200 z-40`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-2.5">
        {!collapsed && (
          <span className="text-[#efeff1] font-semibold text-sm uppercase tracking-wide">Live Events</span>
        )}
        <button onClick={() => setCollapsed(!collapsed)} className="p-1 hover:bg-[#26262c] rounded text-[#adadb8]">
          <ChevronLeft size={20} className={`transition-transform ${collapsed ? "rotate-180" : ""}`} />
        </button>
      </div>

      {/* Event list */}
      <div className="space-y-0.5">
        {liveEvents.map((event) => {
          const Icon = event.icon
          const isSelected = selectedEvent === event.id
          return (
            <button
              key={event.id}
              onClick={() => onSelectEvent(event.id)}
              className={`w-full flex items-center gap-2.5 px-2.5 py-2 hover:bg-[#26262c] transition-colors text-left ${
                isSelected ? "bg-[#26262c] border-l-2 border-[#9147ff]" : ""
              }`}
            >
              <div className={`relative p-2 rounded ${event.bgColor}`}>
                <Icon size={collapsed ? 20 : 18} className={event.color} />
                <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-[#eb0400] rounded-full border-2 border-[#1f1f23]"></span>
              </div>
              {!collapsed && (
                <>
                  <div className="flex-1 min-w-0">
                    <div className="text-[#efeff1] text-sm font-semibold truncate">{event.name}</div>
                    <div className="text-[#adadb8] text-xs truncate">{event.category}</div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-1 text-[#adadb8] text-xs">
                      <span className="w-2 h-2 bg-[#eb0400] rounded-full"></span>
                      {event.viewers}
                    </div>
                    <div className="text-[#9147ff] text-xs">{event.modelsActive} AIs</div>
                  </div>
                </>
              )}
            </button>
          )
        })}
      </div>

      {/* Show More */}
      {!collapsed && (
        <button className="flex items-center gap-1 px-2.5 py-2 text-[#9147ff] hover:underline text-sm font-semibold">
          Show More
          <ChevronDown size={16} />
        </button>
      )}
    </aside>
  )
}
