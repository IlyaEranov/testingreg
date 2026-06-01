/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f9f5",
          100: "#e0f0ea",
          200: "#c1e0d5",
          300: "#8fc4b0",
          400: "#5f9b8c",
          500: "#407368",
          600: "#2c5a4f",
          700: "#1f453c",
          800: "#163530",
          900: "#0f2622",
        },
        accent: {
          DEFAULT: "#c7bc9a",
          light: "#e6d5b8",
          dark: "#b5a988",
        },
      },
      borderRadius: {
        xl2: "20px",
        xl3: "24px",
        xl4: "28px",
        xl5: "36px",
      },
    },
  },
  plugins: [],
};
