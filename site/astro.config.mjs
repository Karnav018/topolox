// @ts-check
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

// Deployed on Vercel (served at the domain root).
// `site` is used for canonical/OG URLs — update it once a custom domain
// (e.g. https://topolox.dev) is attached in the Vercel dashboard.
export default defineConfig({
  site: "https://topolox.vercel.app",
  vite: {
    plugins: [tailwindcss()],
  },
});
