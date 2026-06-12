/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'codex': {
          dark: '#0a0a0a',
          panel: '#1a1a1a',
          blue: '#007acc',
          orange: '#ff8c00',
          steel: '#2d2d2d',
          text: '#e0e0e0',
          muted: '#888888',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      }
    },
  },
  plugins: [],
}