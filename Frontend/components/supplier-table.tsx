"use client"

import { useState } from "react"
import type { SupplierData } from "@/lib/types"
import { ChevronUp, ChevronDown, Download } from "lucide-react"

interface SupplierTableProps {
  suppliers: SupplierData[]
  onViewDetails: (supplier: SupplierData) => void
}

export default function SupplierTable({ suppliers, onViewDetails }: SupplierTableProps) {
  const [sortField, setSortField] = useState<keyof SupplierData>("name")
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc")
  const [showJson, setShowJson] = useState(false)

  const handleSort = (field: keyof SupplierData) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc")
    } else {
      setSortField(field)
      setSortDirection("asc")
    }
  }

  const sortedSuppliers = [...suppliers].sort((a, b) => {
    const aValue = a[sortField]
    const bValue = b[sortField]

    if (typeof aValue === "number" && typeof bValue === "number") {
      return sortDirection === "asc" ? aValue - bValue : bValue - aValue
    }

    if (typeof aValue === "string" && typeof bValue === "string") {
      return sortDirection === "asc" ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue)
    }

    return 0
  })

  const handleExportCSV = () => {
    const headers = ["Supplier Name", "Capacity", "Cost", "Lead Time"]
    const csvContent = [
      headers.join(","),
      ...sortedSuppliers.map((s) => [s.name, s.capacity, `$${s.cost}`, `${s.leadTime} days`].join(",")),
    ].join("\n")

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.setAttribute("href", url)
    link.setAttribute("download", "suppliers.csv")
    link.style.visibility = "hidden"
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="bg-white rounded-lg overflow-hidden border border-border-grey">
      <div className="overflow-x-auto">
        <table className="w-full" aria-label="Supplier ranking table">
          <thead>
            <tr className="bg-primary-accent text-white">
              <th className="px-4 py-2 text-left cursor-pointer" onClick={() => handleSort("name")}>
                <div className="flex items-center">
                  Supplier Name
                  {sortField === "name" &&
                    (sortDirection === "asc" ? <ChevronUp size={16} /> : <ChevronDown size={16} />)}
                </div>
              </th>
              <th className="px-4 py-2 text-left cursor-pointer" onClick={() => handleSort("capacity")}>
                <div className="flex items-center">
                  Capacity
                  {sortField === "capacity" &&
                    (sortDirection === "asc" ? <ChevronUp size={16} /> : <ChevronDown size={16} />)}
                </div>
              </th>
              <th className="px-4 py-2 text-left cursor-pointer" onClick={() => handleSort("cost")}>
                <div className="flex items-center">
                  Cost
                  {sortField === "cost" &&
                    (sortDirection === "asc" ? <ChevronUp size={16} /> : <ChevronDown size={16} />)}
                </div>
              </th>
              <th className="px-4 py-2 text-left cursor-pointer" onClick={() => handleSort("leadTime")}>
                <div className="flex items-center">
                  Lead Time
                  {sortField === "leadTime" &&
                    (sortDirection === "asc" ? <ChevronUp size={16} /> : <ChevronDown size={16} />)}
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedSuppliers.map((supplier) => (
              <tr key={supplier.id} className="border-t border-border-grey hover:bg-border-light">
                <td className="px-4 py-2 text-text-dark">{supplier.name}</td>
                <td className="px-4 py-2 text-text-dark">{supplier.capacity.toLocaleString()}</td>
                <td className="px-4 py-2 text-text-dark">${supplier.cost.toLocaleString()}</td>
                <td className="px-4 py-2 text-text-dark">{supplier.leadTime} days</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="p-3 bg-secondary-mediumGrey flex flex-wrap gap-2 justify-between items-center">
        <div className="flex space-x-2">
          <button
            onClick={() => onViewDetails(sortedSuppliers[0])}
            className="px-4 py-1 bg-primary-accent text-white rounded hover:bg-primary-accent/80 transition-all hover:scale-105 duration-300"
          >
            View Details
          </button>
          <button className="px-4 py-1 bg-primary-accent text-white rounded hover:bg-primary-accent/80 transition-all hover:scale-105 duration-300">
            Place Order
          </button>
          <button
            onClick={handleExportCSV}
            className="px-4 py-1 flex items-center bg-primary-accent text-white rounded hover:bg-primary-accent/80 transition-all hover:scale-105 duration-300"
          >
            <Download size={14} className="mr-1" />
            Export as CSV
          </button>
        </div>

        <button
          onClick={() => setShowJson(!showJson)}
          className="text-sm text-text-grey hover:text-primary-grey transition-colors"
        >
          {showJson ? "Hide Raw Data" : "Show Raw Data"}
        </button>
      </div>

      {showJson && (
        <div className="p-3 bg-text-dark text-white font-roboto-mono text-xs overflow-x-auto">
          <pre>{JSON.stringify(sortedSuppliers, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
