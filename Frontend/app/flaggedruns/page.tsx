"use client"

import { useState } from "react"
import Header from "@/components/header"
import Sidebar from "@/components/sidebar"
import InspectionWindow from "@/components/flagged-runs"

export default function Home() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen flex-col">
      <Header  toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar isOpen={isSidebarOpen} />
        <main className="flex-1 p-4 overflow-y-auto"  style={{marginTop:"4em"}}>
          <InspectionWindow />
        </main>
      </div>
    </div>
  )
}
