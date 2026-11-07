/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'capco-black': '#000000',
        'capco-white': '#FFFFFF',
        'capco-gray': {
          50: '#FAFAFA',
          100: '#F5F5F5',
          200: '#E5E5E5',
          300: '#CCCCCC',
          400: '#999999',
          500: '#666666',
          600: '#3A3A3A',
          700: '#2A2A2A',
          800: '#1A1A1A',
          900: '#0A0A0A',
        },
      },
    },
  },
  plugins: [],
}
