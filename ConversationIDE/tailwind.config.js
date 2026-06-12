/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/renderer/**/*.{js,ts,jsx,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#0a0a0a',
          secondary: '#1a1a1a',
          card: '#1a2333'
        },
        accent: {
          cyan: '#00ffcc',
          gold: '#ffcc00',
          orange: '#ff9966'
        },
        text: {
          primary: '#e0e0e0',
          muted: '#94a3b8'
        },
        border: '#2e3d52'
      },
      fontFamily: {
        mono: ['SF Mono', 'Fira Code', 'monospace'],
        sans: ['Segoe UI', 'Roboto', 'Helvetica', 'Arial', 'sans-serif']
      }
    }
  },
  plugins: []
};
