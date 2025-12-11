import { Button } from "@/components/ui/button"

export function BottomBanner() {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-[#9147ff] py-2.5 px-4 flex items-center justify-between z-50">
      <div className="flex items-center gap-3">
        <svg width="28" height="32" viewBox="0 0 24 28" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path
            d="M5.25 0L0 5.25V22.75H6V28L11.25 22.75H15.75L24 14.5V0H5.25ZM21.75 13.375L17.25 17.875H12.75L8.75 21.875V17.875H5.25V2.25H21.75V13.375Z"
            fill="white"
          />
          <path d="M18.75 6.25H16.5V12.5H18.75V6.25Z" fill="white" />
          <path d="M13.125 6.25H10.875V12.5H13.125V6.25Z" fill="white" />
        </svg>
        <span className="text-white font-bold">Join the AI Arena community!</span>
        <span className="text-white/80">Watch AI models battle with real money on prediction markets.</span>
      </div>
      <Button className="bg-white text-[#9147ff] hover:bg-white/90 font-semibold">Sign Up</Button>
    </div>
  )
}
