import { BettingArena } from "@/components/betting-arena"
import { AiReasoningChat } from "@/components/ai-reasoning-chat"

interface MainContentProps {
  selectedEvent: string
}

export function MainContent({ selectedEvent }: MainContentProps) {
  return (
    <main className="flex-1 ml-[240px] p-6 overflow-y-auto">
      <div className="max-w-[1600px] mx-auto">
        {/* Betting Arena + AI Reasoning Panel */}
        <div className="flex gap-4">
          <BettingArena selectedEvent={selectedEvent} />
          <AiReasoningChat selectedEvent={selectedEvent} />
        </div>
      </div>
    </main>
  )
}
