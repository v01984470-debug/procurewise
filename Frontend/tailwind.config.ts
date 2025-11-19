import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}", "*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
          light: "#F0F7FF", // Very light blue for backgrounds
          grey: "#6B7280", // Medium grey for text
          dark: "#374151", // Dark grey for headings
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
          light: "#F9FAFB", // Very light grey for backgrounds
          grey: "#E5E7EB", // Light grey for UI elements
          dark: "#9CA3AF", // Medium grey for borders
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
          blue: "#60A5FA", // Light blue for accents
          grey: "#4B5563", // Dark grey for buttons
          light: "#93C5FD", // Very light blue for highlights
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        inter: ["var(--font-inter)", "sans-serif"],
        "roboto-mono": ["var(--font-roboto-mono)", "monospace"],
      },
      backgroundImage: {
        "hero-pattern": "url('/images/background.png')",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
