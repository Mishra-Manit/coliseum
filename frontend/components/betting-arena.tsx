"use client"

import { useState, useEffect } from "react"
import {
  Play,
  Volume2,
  Settings,
  Maximize2,
  Pause,
  TrendingUp,
  TrendingDown,
  Minus,
  Heart,
  Star,
  Users,
  Share2,
  MoreHorizontal,
} from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

const aiModels = [
  { id: "gpt-4o", name: "GPT-4o", color: "bg-green-500", textColor: "text-green-500", avatar: "GPT" },
  { id: "claude-3.5", name: "Claude 3.5", color: "bg-orange-500", textColor: "text-orange-500", avatar: "CL" },
  { id: "grok-2", name: "Grok-2", color: "bg-blue-500", textColor: "text-blue-500", avatar: "GK" },
  { id: "gemini-pro", name: "Gemini Pro", color: "bg-purple-500", textColor: "text-purple-500", avatar: "GM" },
  { id: "llama-3.1", name: "Llama 3.1", color: "bg-red-500", textColor: "text-red-500", avatar: "LL" },
  { id: "mistral", name: "Mistral Large", color: "bg-cyan-500", textColor: "text-cyan-500", avatar: "MS" },
  { id: "deepseek", name: "DeepSeek V2", color: "bg-yellow-500", textColor: "text-yellow-500", avatar: "DS" },
  { id: "qwen", name: "Qwen Max", color: "bg-pink-500", textColor: "text-pink-500", avatar: "QW" },
]

const eventDataExtended: Record<
  string,
  {
    title: string
    question: string
    currentPrice: number
    category: string
    subcategory: string
    tags: string[]
    marketContext: string
    viewers: number
  }
> = {
  "us-election": {
    title: "Will Trump win the 2024 election?",
    question: "Will Trump win the 2024 election?",
    currentPrice: 0.52,
    category: "Prediction Markets",
    subcategory: "AI Debate",
    tags: ["Politics", "Election", "High Volume"],
    marketContext: "Current polling shows tight race. Key swing states remain contested.",
    viewers: 89432,
  },
  "super-bowl": {
    title: "Will the Chiefs win Super Bowl LIX?",
    question: "Will the Chiefs win Super Bowl LIX?",
    currentPrice: 0.31,
    category: "Prediction Markets",
    subcategory: "AI Debate",
    tags: ["Sports", "NFL", "Championship"],
    marketContext: "Chiefs seeking three-peat. Mahomes in MVP form.",
    viewers: 45231,
  },
  "fed-rate": {
    title: "Will Fed cut rates in January 2025?",
    question: "Will Fed cut rates in January 2025?",
    currentPrice: 0.67,
    category: "Prediction Markets",
    subcategory: "AI Debate",
    tags: ["Finance", "Economy", "Fed"],
    marketContext: "Inflation cooling, labor market softening. Markets pricing in cuts.",
    viewers: 32156,
  },
  "bitcoin-100k": {
    title: "Will BTC break $100k by Friday?",
    question: "Will BTC break $100k by Friday?",
    currentPrice: 0.65,
    category: "Prediction Markets",
    subcategory: "AI Debate",
    tags: ["Finance", "Crypto", "High Volatility"],
    marketContext: "Bitcoin is currently trading at $98,500. Market sentiment is mixed.",
    viewers: 15402,
  },
  "spacex-launch": {
    title: "Will Starship reach orbit by Q1 2025?",
    question: "Will Starship reach orbit by Q1 2025?",
    currentPrice: 0.78,
    category: "Prediction Markets",
    subcategory: "AI Debate",
    tags: ["Tech", "Space", "SpaceX"],
    marketContext: "Recent test flight successful. Orbital attempt imminent.",
    viewers: 28934,
  },
  "taiwan-conflict": {
    title: "Military escalation in Taiwan Strait 2025?",
    question: "Will there be military escalation in 2025?",
    currentPrice: 0.12,
    category: "Prediction Markets",
    subcategory: "AI Debate",
    tags: ["Geopolitics", "Asia", "Low Probability"],
    marketContext: "Tensions elevated but diplomatic channels active.",
    viewers: 18234,
  },
  "oscar-winner": {
    title: "Will 'The Brutalist' win Best Picture?",
    question: "Will 'The Brutalist' win Best Picture?",
    currentPrice: 0.38,
    category: "Prediction Markets",
    subcategory: "AI Debate",
    tags: ["Entertainment", "Oscars", "Film"],
    marketContext: "Strong critical reception. Awards season favorite.",
    viewers: 12453,
  },
  "ai-regulation": {
    title: "Will AI regulation bill pass in 2025?",
    question: "Will AI regulation bill pass in 2025?",
    currentPrice: 0.55,
    category: "Prediction Markets",
    subcategory: "AI Debate",
    tags: ["Tech", "Policy", "AI"],
    marketContext: "Bipartisan support growing. Industry lobbying intensifies.",
    viewers: 21567,
  },
}

interface BettingArenaProps {
  selectedEvent: string
}

export function BettingArena({ selectedEvent }: BettingArenaProps) {
  const [isPlaying, setIsPlaying] = useState(true)
  const [currentTime, setCurrentTime] = useState("2:47:32")
  const [modelBets, setModelBets] = useState<
    Record<string, { position: "YES" | "NO" | "NEUTRAL"; shares: number; avgPrice: number; pnl: number }>
  >({})

  const event = eventDataExtended[selectedEvent] || eventDataExtended["bitcoin-100k"]

  // Initialize and simulate bets
  useEffect(() => {
    const initialBets: Record<
      string,
      { position: "YES" | "NO" | "NEUTRAL"; shares: number; avgPrice: number; pnl: number }
    > = {}
    aiModels.forEach((model, i) => {
      const positions: ("YES" | "NO" | "NEUTRAL")[] = ["YES", "NO", "NEUTRAL"]
      const position = positions[i % 3]
      initialBets[model.id] = {
        position,
        shares: Math.floor(Math.random() * 5000) + 1000,
        avgPrice: event.currentPrice + (Math.random() - 0.5) * 0.1,
        pnl: (Math.random() - 0.4) * 3000,
      }
    })
    setModelBets(initialBets)
  }, [selectedEvent, event.currentPrice])

  useEffect(() => {
    if (isPlaying) {
      const interval = setInterval(() => {
        setCurrentTime((prev) => {
          const [h, m, s] = prev.split(":").map(Number)
          let newS = s + 1
          let newM = m
          let newH = h
          if (newS >= 60) {
            newS = 0
            newM++
          }
          if (newM >= 60) {
            newM = 0
            newH++
          }
          return `${newH}:${String(newM).padStart(2, "0")}:${String(newS).padStart(2, "0")}`
        })
      }, 1000)
      return () => clearInterval(interval)
    }
  }, [isPlaying])

  const topBettor = aiModels.reduce((best, model) => {
    const bet = modelBets[model.id]
    const bestBet = modelBets[best.id]
    if (!bet || !bestBet) return best
    return bet.pnl > bestBet.pnl ? model : best
  }, aiModels[0])

  const topBettorPnl = modelBets[topBettor.id]?.pnl || 0

  const yesPercentage = Math.round(event.currentPrice * 100)
  const noPercentage = 100 - yesPercentage

  return (
    <div className="flex-1">
      {/* Main Arena Display */}
      <div className="relative aspect-[16/10] bg-[#0e0e10] rounded-lg overflow-hidden group">
        {/* Live badge */}
        <div className="absolute top-3 left-3 z-10 flex items-center gap-2">
          <span className="bg-[#eb0400] text-white text-xs font-bold px-1.5 py-0.5 rounded uppercase">Live</span>
          <span className="bg-[#9147ff] text-white text-xs font-bold px-2 py-0.5 rounded">8 AIs Competing</span>
        </div>

        {/* Betting Display */}
        <div className="absolute inset-0 flex flex-col bg-gradient-to-br from-[#18181b] via-[#0e0e10] to-[#18181b] p-6">
          {/* Event Header */}
          <div className="text-center mb-4">
            <h2 className="text-[#efeff1] text-2xl font-bold">{event.title}</h2>
            <p className="text-[#9147ff] text-lg mt-1">{event.question}</p>
            <div className="flex items-center justify-center gap-4 mt-2">
              <span className="text-[#00ff7f] text-xl font-bold">YES ${event.currentPrice.toFixed(2)}</span>
              <span className="text-[#adadb8]">|</span>
              <span className="text-[#ff4d4d] text-xl font-bold">NO ${(1 - event.currentPrice).toFixed(2)}</span>
            </div>
          </div>

          {/* AI Model Bets Grid */}
          <div className="grid grid-cols-4 gap-3 flex-1">
            {aiModels.map((model) => {
              const bet = modelBets[model.id]
              if (!bet) return null
              return (
                <div
                  key={model.id}
                  className="bg-[#1f1f23] rounded-lg p-3 border border-[#2f2f35] hover:border-[#9147ff] transition-colors"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Avatar className={`w-8 h-8 ${model.color}`}>
                      <AvatarFallback className="text-white text-xs font-bold">{model.avatar}</AvatarFallback>
                    </Avatar>
                    <span className={`font-semibold text-sm ${model.textColor}`}>{model.name}</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-[#adadb8] text-xs">Position</span>
                      <span
                        className={`font-bold text-sm flex items-center gap-1 ${
                          bet.position === "YES"
                            ? "text-[#00ff7f]"
                            : bet.position === "NO"
                              ? "text-[#ff4d4d]"
                              : "text-[#adadb8]"
                        }`}
                      >
                        {bet.position === "YES" ? (
                          <TrendingUp size={12} />
                        ) : bet.position === "NO" ? (
                          <TrendingDown size={12} />
                        ) : (
                          <Minus size={12} />
                        )}
                        {bet.position}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[#adadb8] text-xs">Shares</span>
                      <span className="text-[#efeff1] text-sm">{bet.shares.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[#adadb8] text-xs">Avg Price</span>
                      <span className="text-[#efeff1] text-sm">${bet.avgPrice.toFixed(2)}</span>
                    </div>
                    <div className="flex items-center justify-between pt-1 border-t border-[#2f2f35]">
                      <span className="text-[#adadb8] text-xs">P&L</span>
                      <span className={`font-bold text-sm ${bet.pnl >= 0 ? "text-[#00ff7f]" : "text-[#ff4d4d]"}`}>
                        {bet.pnl >= 0 ? "+" : ""}${bet.pnl.toFixed(0)}
                      </span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Video controls */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3 opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="text-white hover:text-[#9147ff] transition-colors"
              >
                {isPlaying ? <Pause size={24} /> : <Play size={24} />}
              </button>
              <button className="text-white hover:text-[#9147ff] transition-colors">
                <Volume2 size={20} />
              </button>
              <span className="text-white text-xs ml-2">{currentTime}</span>
            </div>
            <div className="flex items-center gap-2">
              <button className="text-white hover:text-[#9147ff] transition-colors">
                <Settings size={20} />
              </button>
              <button className="text-white hover:text-[#9147ff] transition-colors">
                <Maximize2 size={20} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Stream info */}
      <div className="mt-3">
        {/* Top row: Avatar, title, follow/subscribe */}
        <div className="flex items-start gap-3">
          <div className="relative">
            <Avatar className="w-16 h-16 bg-gradient-to-br from-[#9147ff] to-[#772ce8]">
              <AvatarFallback className="text-white font-bold text-xl">AI</AvatarFallback>
            </Avatar>
            <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 bg-[#eb0400] text-white text-[10px] font-bold px-1.5 py-0.5 rounded uppercase">
              Live
            </span>
          </div>

          <div className="flex-1">
            <h2 className="text-[#efeff1] font-bold text-lg leading-tight">{event.title}</h2>
            <div className="flex items-center gap-2 mt-0.5">
              <a href="#" className="text-[#efeff1] hover:text-[#9147ff] font-semibold text-sm">
                Coliseum
              </a>
              <span className="text-[#9147ff] text-xs font-semibold">Verified</span>
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <a href="#" className="text-[#9147ff] hover:underline text-sm">
                {event.category}
              </a>
              <span className="text-[#adadb8]">•</span>
              <span className="text-[#adadb8] text-sm">{event.subcategory}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button className="flex items-center gap-1.5 bg-[#9147ff] hover:bg-[#772ce8] text-white font-semibold text-sm px-4 py-1.5 rounded transition-colors">
              <Heart size={16} fill="currentColor" />
              Follow
            </button>
            <button className="flex items-center gap-1.5 bg-transparent border border-[#3d3d40] hover:bg-[#3d3d40] text-[#efeff1] font-semibold text-sm px-4 py-1.5 rounded transition-colors">
              <Star size={16} />
              Subscribe
            </button>
          </div>
        </div>

        {/* Tags and viewer count row */}
        <div className="flex items-center justify-between mt-3">
          <div className="flex items-center gap-2">
            {event.tags.map((tag) => (
              <span
                key={tag}
                className="bg-transparent border border-[#3d3d40] text-[#efeff1] text-xs px-2.5 py-1 rounded hover:bg-[#3d3d40] cursor-pointer transition-colors"
              >
                {tag}
              </span>
            ))}
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 text-[#efeff1]">
              <Users size={16} />
              <span className="text-sm font-semibold">{event.viewers.toLocaleString()}</span>
            </div>
            <button className="flex items-center gap-1.5 text-[#efeff1] hover:text-[#9147ff] transition-colors">
              <Share2 size={16} />
              <span className="text-sm">Share</span>
            </button>
            <button className="text-[#efeff1] hover:text-[#9147ff] transition-colors">
              <MoreHorizontal size={20} />
            </button>
          </div>
        </div>

        {/* Market Context and Top Bettor card */}
        <div className="mt-4 bg-[#18181b] rounded-lg p-4">
          <div className="flex gap-6">
            {/* Market Context section */}
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp size={16} className="text-[#efeff1]" />
                <span className="text-[#efeff1] font-semibold">Market Context</span>
              </div>
              <p className="text-[#adadb8] text-sm mb-4">{event.marketContext}</p>

              {/* Yes/No probability bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-[#adadb8]">Yes</span>
                  <span className="text-[#adadb8]">No</span>
                </div>
                <div className="flex h-2 rounded-full overflow-hidden">
                  <div className="bg-[#00c853]" style={{ width: `${yesPercentage}%` }} />
                  <div className="bg-[#ff4d4d]" style={{ width: `${noPercentage}%` }} />
                </div>
                <div className="flex justify-between text-sm font-semibold">
                  <span className="text-[#00c853]">{yesPercentage}%</span>
                  <span className="text-[#ff4d4d]">{noPercentage}%</span>
                </div>
              </div>
            </div>

            {/* Divider */}
            <div className="w-px bg-[#3d3d40]" />

            {/* Top Bettor section */}
            <div className="w-48">
              <span className="text-[#efeff1] font-semibold">Top Bettor</span>
              <div className="flex items-center gap-3 mt-3">
                <Avatar className={`w-10 h-10 ${topBettor.color}`}>
                  <AvatarFallback className="text-white text-sm font-bold">{topBettor.avatar}</AvatarFallback>
                </Avatar>
                <div>
                  <div className={`font-semibold ${topBettor.textColor}`}>{topBettor.name}</div>
                  <div className="text-[#adadb8] text-sm">
                    Total Profit: <span className="text-[#00c853]">+${Math.abs(topBettorPnl).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
