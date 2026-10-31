/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 60% White / Light base
        navy: {
          950: '#F8FAFC', // Slate-50: Main Canvas / Page Background
          900: '#FFFFFF', // Pure White: Cards, Headers, Modals
          850: '#F1F5F9', // Slate-100: Secondary card surface / Table hover
          800: '#F8FAFC', // Slate-50: Inner container / Input field base
          700: '#E2E8F0', // Slate-200: Crisp card & divider border
          600: '#CBD5E1', // Slate-300: Active / Focus border
          500: '#94A3B8',
        },
        // Readable Dark Typography
        slate: {
          50: '#FFFFFF',
          100: '#0F172A', // Main Headings, Titles, Big Numbers (Slate 900)
          200: '#1E293B', // Subheadings, Card Titles (Slate 800)
          300: '#334155', // Body Paragraphs, Table Data (Slate 700)
          400: '#64748B', // Secondary Labels, Meta, Filters (Slate 500)
          500: '#94A3B8', // Captions, Timestamps, Muted Icons (Slate 400)
          600: '#475569',
          700: '#334155',
          800: '#1E293B',
          900: '#0F172A',
          950: '#020617',
        },
        // 30% Professional Blue Palette
        blue: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6',
          600: '#2563EB', // Primary Corporate Blue
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A', // Deep Royal Blue
          950: '#0F275A', // High-end Navy
        },
        // 10% Warm Amber-Gold Accent
        amber: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#F59E0B',
          600: '#D97706', // Premium Amber Gold Accent
          700: '#B45309',
          800: '#92400E',
          900: '#78350F',
        },
        brand: {
          accent: '#2563EB', // 30% Royal Blue (primary)
          blue: '#1D4ED8',
          navy: '#0F275A',
          teal: '#0D9488',   // Balanced Teal
          gold: '#D97706',   // 10% Accent Amber-Gold
          red: '#DC2626',    // Financial Negative / Downward
          green: '#16A34A',  // Financial Positive / Upward
        }
      }
    },
  },
  plugins: [],
}
