/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f5f8ff',
          100: '#ebf1fe',
          200: '#d7e2fd',
          300: '#b4cafe',
          400: '#8ca7fd',
          500: '#637dfc',
          600: '#4b5df5',
          700: '#3a47e0',
          800: '#303abd',
          900: '#2b3397',
          950: '#1e225c',
        },
        dark: {
          50: '#f6f6f7',
          100: '#eef0f2',
          200: '#dadfe5',
          300: '#b8c3d0',
          400: '#90a1b6',
          500: '#72869f',
          600: '#5b6c84',
          700: '#4a576b',
          800: '#3f495a',
          900: '#373f4d',
          950: '#0f1115', // Sleek deep black/gray
        }
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'sans-serif'],
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
