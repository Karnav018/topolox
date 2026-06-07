# Topolox landing page

The marketing site for [Topolox](https://github.com/Karnav018/topolox), built with
[Astro](https://astro.build) + [Tailwind CSS v4](https://tailwindcss.com). Fully animated, static,
zero runtime backend.

## Develop

```bash
cd site
npm install
npm run dev      # http://localhost:4321/topolox
```

## Build

```bash
npm run build    # → site/dist/
npm run preview  # serve the production build locally
```

## Sections

- **Hero** — interactive force-directed "living graph" on canvas (hover a node, click to trace its
  blast radius; auto-cycles through hubs). No graph library.
- **How it works** — the three-command flow.
- **Two-agent race** — synced self-typing terminals comparing token spend with/without Topolox.
- **Meltdown counter** — animated 120,326 → 11,647 token reduction with a 5.4× stamp.
- **Features / Works with / Quickstart / CTA / Footer.**

All animations respect `prefers-reduced-motion`.

## Deploy

Pushing to `main` with changes under `site/**` triggers `.github/workflows/site.yml`, which builds
and publishes to **GitHub Pages** at `https://karnav018.github.io/topolox/`.

One-time setup: in the GitHub repo, go to **Settings → Pages → Build and deployment → Source** and
choose **GitHub Actions**.

### Custom domain (later)

To serve from e.g. `topolox.dev`:

1. In `astro.config.mjs`, set `site: "https://topolox.dev"` and remove the `base` line.
2. Add `site/public/CNAME` containing `topolox.dev`.
3. Point the domain's DNS at GitHub Pages and set the custom domain in repo settings.
