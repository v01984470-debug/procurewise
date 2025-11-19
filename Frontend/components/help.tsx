"use client"

import { useState } from "react"
import { ChevronDown, Search, MessageCircle, Book, Phone } from "lucide-react"
import Image from "next/image"

export default function Help() {
  const [openFaq, setOpenFaq] = useState<number | null>(null)
  const [searchTerm, setSearchTerm] = useState("")

  const faqs = [
    {
      id: 1,
      question: "How do I track a PO with OptiBuy?",
      answer:
        'Type or say "Track PO-XXXX" in the chat. OptiBuy will display the shipment status with a detailed timeline, including customs clearance, shipping updates, and expected delivery dates.',
      category: "tracking",
    },
    {
      id: 2,
      question: "Can OptiBuy suggest sustainable suppliers?",
      answer:
        "Yes, OptiBuy analyzes your preferences and suggests suppliers with certifications like ISO 14001, LEED, or other sustainability credentials. You can also filter suppliers by their environmental impact scores.",
      category: "suppliers",
    },
    {
      id: 3,
      question: "How do I set up automated reordering?",
      answer:
        "In the dashboard, go to Inventory Management and set minimum stock thresholds for each item. OptiBuy will automatically suggest reorders when stock levels fall below these thresholds.",
      category: "automation",
    },
    {
      id: 4,
      question: "What languages does OptiBuy support?",
      answer:
        "OptiBuy currently supports English, Mandarin Chinese, and German. You can switch languages in your profile settings or ask OptiBuy to respond in your preferred language.",
      category: "general",
    },
    {
      id: 5,
      question: "How do I compare supplier quotes?",
      answer:
        'Ask OptiBuy "Compare quotes for [item]" and it will display a detailed comparison table with pricing, lead times, quality scores, and delivery terms from all available suppliers.',
      category: "suppliers",
    },
    {
      id: 6,
      question: "Can I export procurement data?",
      answer:
        "Yes, you can export data in various formats (CSV, Excel, PDF) from the dashboard or by asking OptiBuy to generate reports. Data includes supplier performance, cost analysis, and inventory reports.",
      category: "data",
    },
  ]

  const filteredFaqs = faqs.filter(
    (faq) =>
      faq.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <div className="relative max-w-4xl mx-auto">
      <div className="absolute inset-0 overflow-hidden rounded-lg">
        <Image
          src="/images/background.png"
          alt="Warehouse background"
          fill
          className="object-cover opacity-10"
          priority
        />
      </div>

      <div className="relative glass-effect rounded-lg shadow-lg p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-primary-dark mb-2">Help & Support</h1>
          <p className="text-primary-grey">Find answers to common questions and get support for ProcureWise AI</p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-secondary-grey text-center">
            <MessageCircle className="h-8 w-8 text-accent-blue mx-auto mb-3" />
            <h3 className="font-semibold text-primary-dark mb-2">Chat with OptiBuy</h3>
            <p className="text-sm text-primary-grey mb-4">Get instant help from our AI assistant</p>
            <button className="bg-accent-blue text-white px-4 py-2 rounded hover:bg-accent-blue/80 transition-all">
              Start Chat
            </button>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-secondary-grey text-center">
            <Book className="h-8 w-8 text-accent-grey mx-auto mb-3" />
            <h3 className="font-semibold text-primary-dark mb-2">User Guide</h3>
            <p className="text-sm text-primary-grey mb-4">Comprehensive documentation and tutorials</p>
            <button className="bg-accent-grey text-white px-4 py-2 rounded hover:bg-accent-grey/80 transition-all">
              View Guide
            </button>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-secondary-grey text-center">
            <Phone className="h-8 w-8 text-accent-blue mx-auto mb-3" />
            <h3 className="font-semibold text-primary-dark mb-2">Contact Support</h3>
            <p className="text-sm text-primary-grey mb-4">Speak with our support team</p>
            <button className="bg-accent-grey text-white px-4 py-2 rounded hover:bg-accent-grey/80 transition-all">
              Contact Us
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-primary-grey" />
            <input
              type="text"
              placeholder="Search FAQs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-secondary-grey rounded-lg focus:border-accent-blue focus:outline-none bg-white"
            />
          </div>
        </div>

        {/* FAQs */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-primary-dark mb-6">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {filteredFaqs.map((faq) => (
              <div key={faq.id} className="bg-white rounded-lg shadow-sm border border-secondary-grey">
                <button
                  onClick={() => setOpenFaq(openFaq === faq.id ? null : faq.id)}
                  className="w-full p-6 text-left flex justify-between items-center hover:bg-secondary-light transition-all"
                >
                  <span className="font-semibold text-primary-dark pr-4">{faq.question}</span>
                  <ChevronDown
                    className={`h-5 w-5 text-primary-grey transition-transform ${openFaq === faq.id ? "rotate-180" : ""}`}
                  />
                </button>
                {openFaq === faq.id && (
                  <div className="px-6 pb-6">
                    <p className="text-primary-grey leading-relaxed">{faq.answer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Contact Form */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-secondary-grey">
          <h2 className="text-xl font-semibold text-primary-dark mb-4">Contact Support</h2>
          <form className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Your Name"
                className="w-full p-3 border border-secondary-grey rounded-lg focus:border-accent-blue focus:outline-none"
              />
              <input
                type="email"
                placeholder="Your Email"
                className="w-full p-3 border border-secondary-grey rounded-lg focus:border-accent-blue focus:outline-none"
              />
            </div>
            <input
              type="text"
              placeholder="Subject"
              className="w-full p-3 border border-secondary-grey rounded-lg focus:border-accent-blue focus:outline-none"
            />
            <textarea
              placeholder="Describe your question or issue..."
              rows={4}
              className="w-full p-3 border border-secondary-grey rounded-lg focus:border-accent-blue focus:outline-none resize-none"
            ></textarea>
            <button className="bg-accent-grey text-white px-6 py-3 rounded-lg hover:bg-accent-grey/80 transition-all font-medium">
              Submit Request
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
