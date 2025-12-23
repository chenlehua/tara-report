/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-blue': '#3B82F6',
        'brand-purple': '#8B5CF6',
        'brand-pink': '#EC4899',
        'brand-cyan': '#06B6D4',
        'bg-primary': '#0A0F1A',
        'bg-secondary': '#111827',
        'bg-tertiary': '#1E293B',
        'bg-card': 'rgba(255,255,255,0.03)',
      },
    },
  },
  plugins: [],
}
