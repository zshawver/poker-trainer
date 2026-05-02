import type { Config } from "tailwindcss";

/**
 * DRC Brand Tailwind Configuration
 *
 * Brand tokens derived from the DRC Brand Guidelines document.
 * This file should be used as-is across all DRC frontend projects.
 *
 * Colors:
 *   - counsel (#505050)  — Primary dark grey. Headings, logo text, card text.
 *   - steel (#919191)    — Secondary grey. Supporting text, borders, neutral elements.
 *   - white (#FFFFFF)    — Backgrounds, reversed text on dark.
 *   - drc-yellow (#f5ea14) — Accent. Buttons, highlights, active indicators, gradients.
 *                            Avoid on white backgrounds for small text (low contrast).
 *
 * Typography:
 *   - Headings: News Gothic Bold (self-hosted, "Gothic News-Bold"). Bold, uppercase.
 *   - Body: Lato (Google Fonts). Regular weight, generous line spacing.
 *
 * Font files:
 *   - frontend/public/fonts/Gothic News-Bold.ttf  — headings
 *   - Lato loaded via Google Fonts @import in index.css
 *
 * Ranking border colors (jury selection projects):
 *   - rank-1 (#8B0000) deep red    — Strongly unfavorable
 *   - rank-2 (#CC3333) red         — Unfavorable
 *   - rank-3 (#919191) steel       — Neutral / unknown
 *   - rank-4 (#4CAF50) green       — Favorable
 *   - rank-5 (#1B5E20) dark green  — Strongly favorable
 */

const config: Config = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        counsel: "#505050",
        steel: "#919191",
        "drc-yellow": "#f5ea14",

        // Counsel tint scale (percentage opacities of #505050 on white)
        "counsel-10": "#e8e8e8",
        "counsel-20": "#d9d9d9",
        "counsel-40": "#b3b3b3",
        "counsel-60": "#8c8c8c",
        "counsel-80": "#666666",

        // Ranking palette
        rank: {
          1: "#8B0000",
          2: "#CC3333",
          3: "#919191",
          4: "#4CAF50",
          5: "#1B5E20",
        },
      },

      fontFamily: {
        heading: ['"Gothic News-Bold"', "Arial", "sans-serif"],
        body: ["Lato", "sans-serif"],
      },

      fontSize: {
        // DRC type hierarchy
        headline: ["2.5rem", { lineHeight: "1.1", fontWeight: "700", letterSpacing: "0.05em" }],
        subtitle: ["1.25rem", { lineHeight: "1.3", fontWeight: "700" }],
        "body-lg": ["1.125rem", { lineHeight: "1.7" }],
        "body-sm": ["0.875rem", { lineHeight: "1.6" }],
      },

      borderWidth: {
        "3": "3px",
        "4": "4px",
      },

      backgroundImage: {
        // DRC yellow-to-white gradient (left to right)
        "drc-gradient-lr": "linear-gradient(to right, #f5ea14, #ffffff)",
        // DRC yellow-to-white gradient (top to bottom)
        "drc-gradient-tb": "linear-gradient(to bottom, #f5ea14, #ffffff)",
      },

      boxShadow: {
        card: "0 1px 3px 0 rgba(80, 80, 80, 0.1), 0 1px 2px -1px rgba(80, 80, 80, 0.1)",
        "card-hover": "0 4px 6px -1px rgba(80, 80, 80, 0.1), 0 2px 4px -2px rgba(80, 80, 80, 0.1)",
        modal: "0 20px 25px -5px rgba(80, 80, 80, 0.15), 0 8px 10px -6px rgba(80, 80, 80, 0.1)",
      },
    },
  },
  plugins: [],
};

export default config;
