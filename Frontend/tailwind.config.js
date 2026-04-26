/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        abyss: "#030711",
        neonBlue: "#48c6ff",
        neonGreen: "#49f6a4",
        neonOrange: "#ff9a3c",
        neonRose: "#ff4d8b",
        panel: "rgba(7, 14, 28, 0.84)"
      },
      boxShadow: {
        glow: "0 0 30px rgba(72, 198, 255, 0.22)",
        greenGlow: "0 0 30px rgba(73, 246, 164, 0.18)",
        orangeGlow: "0 0 30px rgba(255, 154, 60, 0.2)"
      },
      fontFamily: {
        display: ["'Space Grotesk'", "ui-sans-serif", "system-ui"],
        body: ["'Inter'", "ui-sans-serif", "system-ui"]
      },
      backgroundImage: {
        aurora:
          "radial-gradient(circle at 18% 20%, rgba(72,198,255,0.18), transparent 28%), radial-gradient(circle at 82% 18%, rgba(255,77,139,0.12), transparent 24%), radial-gradient(circle at 50% 85%, rgba(73,246,164,0.12), transparent 24%), linear-gradient(180deg, #030711 0%, #02050d 45%, #010204 100%)"
      }
    }
  },
  plugins: []
};
