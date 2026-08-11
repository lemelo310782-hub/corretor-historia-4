/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        academic: {
          950: "#0a1628",
          900: "#0f2038",
          800: "#16304f",
          700: "#1e3f66",
          600: "#2a5182",
          100: "#e8edf5",
          50: "#f5f7fb",
        },
        parchment: "#f8f5ee",
      },
      fontFamily: {
        serif: ["Georgia", "Cambria", "serif"],
      },
    },
  },
  plugins: [],
}
