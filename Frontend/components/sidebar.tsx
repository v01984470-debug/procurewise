"use client"

import { Plus, Download, FileText, Calendar, Filter } from "lucide-react"

interface SidebarProps {
  isOpen: boolean
}

export default function Sidebar({ isOpen }: SidebarProps) {
  return (
    <aside
      className={`bg-white text-primary-dark h-[calc(100vh-64px)] mt-16 transition-all duration-300 border-r border-secondary-grey ${
        isOpen ? "w-60" : "w-16"
      }`}
    >
      <div className="p-4">
        {isOpen ? (
          <>
            <h2 className="text-lg font-semibold mb-4 text-primary-dark">Recent Queries</h2>
            <ul className="space-y-2 mb-6">
              <li className="flex items-center text-sm hover:bg-secondary-light p-2 rounded cursor-pointer">
                <FileText size={16} className="mr-2 text-accent-blue" />
                ITM-001 Suppliers, Japan
              </li>
              <li className="flex items-center text-sm hover:bg-secondary-light p-2 rounded cursor-pointer">
                <Calendar size={16} className="mr-2 text-accent-blue" />
                Track PO-78901
              </li>
              <li className="flex items-center text-sm hover:bg-secondary-light p-2 rounded cursor-pointer">
                <FileText size={16} className="mr-2 text-accent-blue" />
                Inventory Analysis Q2
              </li>
            </ul>

            <h2 className="text-lg font-semibold mb-4 text-primary-dark">Filters</h2>
            <div className="space-y-3 mb-6">
              <div className="relative">
                <select className="w-full p-2 bg-secondary-light border border-secondary-grey rounded appearance-none cursor-pointer focus:outline-none focus:border-accent-blue text-sm text-primary-dark">
                  <option value="">Date: All Time</option>
                  <option value="today">Today</option>
                  <option value="week">This Week</option>
                  <option value="month">This Month</option>
                </select>
                <Filter size={16} className="absolute right-2 top-3 pointer-events-none text-primary-grey" />
              </div>
              <div className="relative">
                <select className="w-full p-2 bg-secondary-light border border-secondary-grey rounded appearance-none cursor-pointer focus:outline-none focus:border-accent-blue text-sm text-primary-dark">
                  <option value="">Region: All</option>
                  <option value="asia">Asia</option>
                  <option value="europe">Europe</option>
                  <option value="americas">Americas</option>
                </select>
                <Filter size={16} className="absolute right-2 top-3 pointer-events-none text-primary-grey" />
              </div>
            </div>

            <h2 className="text-lg font-semibold mb-4 text-primary-dark">Quick Actions</h2>
            <div className="space-y-2">
              <button className="w-full flex items-center justify-center text-sm bg-accent-grey text-white px-3 py-2 rounded hover:bg-accent-grey/80 transition-all">
                <Plus className="h-4 w-4 mr-2" />
                New PO
              </button>
              <button className="w-full flex items-center justify-center text-sm bg-accent-grey text-white px-3 py-2 rounded hover:bg-accent-grey/80 transition-all">
                <Download className="h-4 w-4 mr-2" />
                Export Data
              </button>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center space-y-6 mt-4">
            <FileText size={24} className="text-accent-blue hover:text-accent-grey cursor-pointer" />
            <Calendar size={24} className="text-accent-blue hover:text-accent-grey cursor-pointer" />
            <Filter size={24} className="text-accent-blue hover:text-accent-grey cursor-pointer" />
            <Plus size={24} className="text-accent-blue hover:text-accent-grey cursor-pointer" />
            <Download size={24} className="text-accent-blue hover:text-accent-grey cursor-pointer" />
          </div>
        )}
      </div>
    </aside>
  )
}
