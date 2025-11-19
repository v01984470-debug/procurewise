"use client"

import { useState, useRef, useEffect } from "react"
import Link from "next/link"
import Image from "next/image"
import { usePathname } from "next/navigation"
import { Menu, User, Settings, LogOut, ChevronDown, Info } from "lucide-react"

interface HeaderProps {
  toggleSidebar: () => void
}

export default function Header({ toggleSidebar }: HeaderProps) {
  // State for user menu
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  // State for Beta‐info pop-over
  const [infoOpen, setInfoOpen] = useState(false)
  const infoRef = useRef<HTMLDivElement>(null)

  const pathname = usePathname()

  // Click-outside handler for user menu
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  // Click-outside handler for info pop-over
  useEffect(() => {
    function handleClickOutsideInfo(event: MouseEvent) {
      if (infoRef.current && !infoRef.current.contains(event.target as Node)) {
        setInfoOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutsideInfo)
    return () => document.removeEventListener("mousedown", handleClickOutsideInfo)
  }, [])

  const linkClass = (href: string) =>
    `${pathname === href
       ? "text-accent-blue font-bold"
       : "text-primary-grey"
    } hover:text-accent-blue transition-colors`

  return (
    <header className="fixed top-0 left-0 right-0 bg-white shadow-sm z-10 border-b border-secondary-grey">
      <div className="flex items-center justify-between h-16 px-4">
        {/* Sidebar toggle + Logo + Beta label + Info button */}
        <div className="flex items-center relative">
          <button
            onClick={toggleSidebar}
            className="mr-4 text-primary-grey hover:text-primary-dark focus:outline-none focus:ring-2 focus:ring-accent-blue rounded"
            aria-label="Toggle sidebar"
          >
            <Menu className="h-6 w-6" />
          </button>

          <Link href="/" className="flex items-center">
            <div className="relative w-10 h-10 mr-2">
              <Image
                src="/images/title_icon.svg"
                alt="ProcureWise AI Logo"
                fill
                className="object-contain"
              />
            </div>
            <span className="text-xl font-bold text-primary-dark">
              ProcureWise AI <span className="text-xl" style={{ fontWeight: "lighter" }}>| BETA</span>
            </span>
          </Link>

          {/* Info (“ℹ️”) button */}
          <button
            onClick={() => setInfoOpen(!infoOpen)}
            className="ml-2 text-primary-grey hover:text-primary-dark focus:outline-none focus:ring-2 focus:ring-accent-blue rounded"
            aria-label="Beta info"
          >
            <Info className="h-5 w-5" />
          </button>

          {/* Beta disclaimer pop-over */}
          {infoOpen && (
            <div
              ref={infoRef}
              className="absolute w-64 right-0 bg-white rounded-md shadow-lg border border-secondary-grey p-3 text-sm z-20 fade-in"
              style={{marginTop:"20em"}}
            >
              <p className="text-primary-dark font-medium">
                ProcureWise AI is currently in <span className="font-semibold">Beta</span> and under active development.
              </p>
              
              <p className="mt-1" style={{color:"rgb(255, 96, 96)"}}>
              While we strive to deliver accurate and reliable insights, there may be occasional inaccuracies or feature gaps. <br />
                If you encounter any issues or have suggestions, please flag the conversation with feedback so we can address it promptly.
              </p>
            </div>
          )}
        </div>

        {/* Navigation with active highlighting */}
        <nav className="hidden md:flex items-center space-x-6 mr-6">
          <Link href="/dashboard" className={linkClass("/dashboard")}>
            Dashboard
          </Link>
          <Link href="/alerts" className={linkClass("/alerts")}>
            Alerts
          </Link>
          <Link href="/help" className={linkClass("/help")}>
            Help
          </Link>
        </nav>

        {/* User menu */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center space-x-2 focus:outline-none focus:ring-2 focus:ring-accent-blue rounded"
            aria-label="User menu"
          >
            <div className="w-8 h-8 rounded-full bg-accent-blue flex items-center justify-center text-white font-bold">
              PS
            </div>
            <ChevronDown className="h-4 w-4 text-primary-grey" />
          </button>
          {userMenuOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-20 fade-in">
              <div className="px-4 py-2 border-b border-secondary-grey">
                <p className="text-sm font-medium text-primary-dark">
                  Priya Sharma
                </p>
                <p className="text-xs text-primary-grey">
                  Procurement Manager
                </p>
              </div>
              <Link
                href="/profile"
                className="flex items-center px-4 py-2 text-sm text-primary-dark hover:bg-secondary-light"
              >
                <User size={16} className="mr-2 text-primary-grey" />
                Profile
              </Link>
              <Link
                href="/settings"
                className="flex items-center px-4 py-2 text-sm text-primary-dark hover:bg-secondary-light"
              >
                <Settings size={16} className="mr-2 text-primary-grey" />
                Settings
              </Link>
              <div className="border-t border-secondary-grey my-1"></div>
              <Link
                href="/logout"
                className="flex items-center px-4 py-2 text-sm text-primary-dark hover:bg-secondary-light"
              >
                <LogOut size={16} className="mr-2 text-primary-grey" />
                Logout
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
