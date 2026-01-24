/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'ca-bg': '#0a0a0f',
        'ca-panel': '#12121a',
        'ca-cyan': '#22d3ee',
        'ca-purple': '#a78bfa',
        'ca-green': '#34d399',
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'monospace'],
        'sans': ['Space Grotesk', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
