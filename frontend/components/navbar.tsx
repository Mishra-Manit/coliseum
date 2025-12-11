import { Search, Bell, User, MoreHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 h-[50px] bg-[#18181b] border-b border-[#2f2f35] z-50 flex items-center justify-between px-2.5">
      {/* Left section */}
      <div className="flex items-center gap-2">
        <a href="/" className="flex items-center gap-1 px-2.5 py-2 hover:bg-[#26262c] rounded">
          <svg width="24" height="28" viewBox="0 0 24 28" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M5.25 0L0 5.25V22.75H6V28L11.25 22.75H15.75L24 14.5V0H5.25ZM21.75 13.375L17.25 17.875H12.75L8.75 21.875V17.875H5.25V2.25H21.75V13.375Z"
              fill="#9147ff"
            />
            <path d="M18.75 6.25H16.5V12.5H18.75V6.25Z" fill="#9147ff" />
            <path d="M13.125 6.25H10.875V12.5H13.125V6.25Z" fill="#9147ff" />
          </svg>
          <span className="font-bold text-[#efeff1] text-lg ml-1">Coliseum</span>
        </a>
        <button className="flex items-center gap-2 px-2.5 py-1.5 text-[#efeff1] hover:bg-[#26262c] rounded font-semibold text-sm">
          Browse
        </button>
        <button className="p-1.5 hover:bg-[#26262c] rounded text-[#efeff1]">
          <MoreHorizontal size={20} />
        </button>
      </div>

      {/* Center - Search */}
      <div className="flex items-center max-w-[400px] w-full">
        <div className="relative flex-1">
          <Input
            type="text"
            placeholder="Search"
            className="w-full bg-[#464649] border-none h-9 rounded-l-md rounded-r-none text-[#efeff1] placeholder:text-[#adadb8] focus-visible:ring-0 focus-visible:ring-offset-0"
          />
        </div>
        <Button className="h-9 px-3 bg-[#3a3a3d] hover:bg-[#464649] rounded-l-none rounded-r-md border-l border-[#2f2f35]">
          <Search size={18} className="text-[#adadb8]" />
        </Button>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon" className="text-[#efeff1] hover:bg-[#26262c] relative">
          <Bell size={20} />
          <span className="absolute -top-0.5 -right-0.5 bg-[#eb0400] text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
            3
          </span>
        </Button>
        <Button className="bg-transparent hover:bg-[#26262c] text-[#efeff1] font-semibold text-sm">Log In</Button>
        <Button className="bg-[#9147ff] hover:bg-[#772ce8] text-white font-semibold text-sm">Sign Up</Button>
        <Button variant="ghost" size="icon" className="text-[#efeff1] hover:bg-[#26262c]">
          <User size={20} />
        </Button>
      </div>
    </nav>
  )
}
