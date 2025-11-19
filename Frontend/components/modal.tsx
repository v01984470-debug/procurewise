"use client"

import type React from "react"
import { useEffect, useRef } from "react"
import { X } from "lucide-react"

interface ModalProps {
  children: React.ReactNode
  onClose: () => void
  /** if true, modal content fills 80–90% of viewport */
  fullScreen?: boolean
}

export default function Modal({ children, onClose, fullScreen = true }: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    const handleClickOutside = (e: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
        onClose()
      }
    }

    document.addEventListener("keydown", handleEscape)
    document.addEventListener("mousedown", handleClickOutside)
    return () => {
      document.removeEventListener("keydown", handleEscape)
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [onClose])

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 fade-in"
      style={{ borderRadius: "3px" }}
    >
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        className={
          `bg-white rounded-lg p-6 glass-effect border-2 border-accent-blue ` +
          (fullScreen ? "w-[90vw] h-[90vh] max-w-none max-h-none mx-0" : "max-w-lg w-full mx-4")
        }
        style={{ borderRadius: "3px" }}
      >
        <div className="flex justify-between items-center mb-4" style={{ borderRadius: "3px" }}>
          <div></div>
          <button
            onClick={onClose}
            className="text-primary-grey hover:text-primary-dark transition-colors"
            aria-label="Close modal"
          >
            <X className="h-6 w-6" />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}
