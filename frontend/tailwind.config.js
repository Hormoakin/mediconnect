// ══════════════════════════════════════════════════════════════
// frontend/tailwind.config.js
//
// MEDICONNECT DESIGN TOKEN SYSTEM
// ────────────────────────────────
// Grounded in subject: a Nigerian clinical/health-tech platform —
// deliberately avoiding the generic "SaaS blue gradient" look AND
// the cream+terracotta / near-black+neon / broadsheet AI-default
// clichés. The palette pairs a deep clinical teal (trust, calm,
// medical without being sterile) with a warm amber accent (human
// warmth, energy) on a cool off-white surface (not cream).
//
// Typography pairs Space Grotesk (confident, geometric, technical —
// used with restraint for headings) with IBM Plex Sans (highly
// legible, built for data-dense interfaces — body/UI text) and
// IBM Plex Mono (timestamps, IDs, status badges, vitals/metrics).
// This pairing reflects the dual identity of the product: a
// healthcare platform built with serious engineering rigor.
// ══════════════════════════════════════════════════════════════
export default {
  content: ["./index.html", "./src/**\/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink:          '#15211F',
        'ink-soft':   '#4B5A56',
        'ink-faint':  '#7C8B87',
        surface:      '#F7F9F8',
        'surface-raised': '#FFFFFF',
        'border-soft': '#DCE6E2',
        brand: {
          ink:        '#0B1F1C',
          teal:       '#0F6F5C',
          'teal-deep':'#0A4F41',
          'teal-tint':'#E4F3EF',
          amber:      '#E2A33B',
          'amber-tint':'#FBF0DC',
          coral:      '#E2664B',
          'coral-tint':'#FBE7E1',
        },
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body:    ['"IBM Plex Sans"', 'sans-serif'],
        mono:    ['"IBM Plex Mono"', 'monospace'],
      },
      borderRadius: {
        'xl2': '1.25rem',
      },
      boxShadow: {
        card: '0 1px 2px rgba(11,31,28,0.04), 0 4px 16px rgba(11,31,28,0.06)',
        'card-hover': '0 2px 4px rgba(11,31,28,0.06), 0 8px 24px rgba(11,31,28,0.10)',
      },
      keyframes: {
        pulseLine: {
          '0%, 100%': { strokeDashoffset: '0' },
          '50%':      { strokeDashoffset: '-24' },
        },
      },
      animation: {
        pulseLine: 'pulseLine 3.2s linear infinite',
      },
    },
  },
  plugins: [],
}

