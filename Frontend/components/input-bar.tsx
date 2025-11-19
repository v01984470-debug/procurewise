"use client"

import type React from "react"

import { useState } from "react"
import { Send, Paperclip, Mic } from "lucide-react"

interface InputBarProps {
  onSendMessage: (text: string) => void
}

export default function InputBar({ onSendMessage }: InputBarProps) {
  const [input, setInput] = useState("")
  const [showSuggestions, setShowSuggestions] = useState(true)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) {
      onSendMessage(input.trim())
      setInput("")
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    onSendMessage(suggestion)
  }

  const suggestions = [
    "Find suppliers for ITM-001",
    "Track PO-2023-089",
    "Check inventory levels",
    "Compare supplier costs",
  ]

  return (
    <div className="bg-secondary-mediumGrey border-t border-border-grey p-4">
      <div className="max-w-3xl mx-auto">
        {showSuggestions && (
          <div className="mb-3 flex flex-wrap gap-2">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => handleSuggestionClick(suggestion)}
                className="px-3 py-1 bg-primary-accent text-white rounded-full text-sm hover:scale-105 transition-transform duration-300"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex items-center gap-2">
          <button
            type="button"
            className="p-2 text-text-grey hover:text-primary-grey transition-colors"
            aria-label="Attach file"
          >
            <Paperclip size={20} />
          </button>

          <div className="relative flex-1">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about suppliers, orders..."
              className="w-full p-2 pr-10 rounded-lg border border-border-grey focus:border-primary-accent focus:outline-none"
              aria-label="Message input"
            />
            <button
              type="button"
              className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 text-text-grey hover:text-primary-grey transition-colors"
              aria-label="Voice input"
            >
              <Mic size={20} />
            </button>
          </div>

          <button
            type="submit"
            className="p-2 bg-primary-accent rounded-full hover:bg-primary-accent/80 transition-all hover:scale-105 duration-300"
            aria-label="Send message"
            disabled={!input.trim()}
          >
            <Send size={20} className="text-white" />
          </button>
        </form>

        <div className="mt-2 text-center md:hidden">
          <button
            onClick={() => setShowSuggestions(!showSuggestions)}
            className="text-sm text-text-grey hover:text-primary-grey transition-colors"
          >
            {showSuggestions ? "Hide Suggestions" : "Show Suggestions"}
          </button>
        </div>
      </div>
    </div>
  )
}
