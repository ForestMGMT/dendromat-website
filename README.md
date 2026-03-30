# Dendromat — Forstliche Werkzeuge

Swiss forestry tools portal at [www.dendromat.ch](https://www.dendromat.ch)

Built with [Astro](https://astro.build) · Vanilla JS · CSS custom properties

---

## Quick start

```bash
npm install
npm run dev
```

Open [http://localhost:4321](http://localhost:4321)

### Other commands

| Command           | Action                              |
|-------------------|-------------------------------------|
| `npm run dev`     | Start local dev server              |
| `npm run build`   | Build static site to `./dist/`      |
| `npm run preview` | Preview the production build locally|

### Deploy

The project is deploy-ready for **Vercel** or **Netlify**:
- Build command: `npm run build`
- Publish directory: `dist`
- No environment variables needed (static site)

---

## Placeholder assets — what goes where

### Logo
| File | Description |
|------|-------------|
| `public/logo/dendromat.svg` | Main Dendromat logo SVG. Currently using the draft (`dendromat_logo_entwurf.svg`). Replace with final artwork. |

### Tree SVGs (hero sprinkling effect)
All files go in `public/trees/`. The hero clicks randomly pick from this list.

| File | Placeholder shape | Replace with |
|------|-------------------|--------------|
| `public/trees/tree-1.svg` | Conifer / Tanne (triangle) | Your tree-1 artwork |
| `public/trees/tree-2.svg` | Deciduous / Laubbaum (round) | Your tree-2 artwork |
| `public/trees/tree-3.svg` | Slim fir / Schlanke Tanne | Your tree-3 artwork |
| `public/trees/tree-4.svg` | Broad deciduous / Breiter Laubbaum | Your tree-4 artwork |
| `public/trees/tree-5.svg` | Birch / Birke (pale trunk) | Your tree-5 artwork |

To add more tree types: add the file to `public/trees/` and add its path to the `TREE_FILES` array in `src/components/Hero.astro`.

### Tool preview images
| File | Description |
|------|-------------|
| `public/tools/timelapse-preview.jpg` | Card thumbnail for Timelapse Creator (800×500px recommended) |
| `public/tools/baumportraets-preview.jpg` | Card thumbnail for Baumarten­porträts (800×500px recommended) |

Once images are added, set the `image` field for each tool in `src/components/ToolsMosaic.astro`.

---

## How to add a new tool card

1. **Add i18n strings** in `src/i18n/translations.js` under `tools` for all 4 languages:
   ```js
   mytool: {
     title: 'Mein Werkzeug',
     desc:  'Kurze Beschreibung des Werkzeugs.',
   }
   ```

2. **Add a card** to the `tools` array in `src/components/ToolsMosaic.astro`:
   ```js
   {
     slug:      'mytool',
     i18nTitle: 'tools.mytool.title',
     i18nDesc:  'tools.mytool.desc',
     image:     '/tools/mytool-preview.jpg', // or null for placeholder
     imageAlt:  'Mein Werkzeug Vorschau',
     ready:     true,
   }
   ```

3. **Create the page** at `src/pages/tools/mytool.astro`
   (copy `timelapse.astro` or `baumportraets.astro` as a starting point).

4. **Drop the preview image** in `public/tools/mytool-preview.jpg`.

---

## Project structure

```
├── public/
│   ├── logo/
│   │   └── dendromat.svg          ← main logo
│   ├── trees/
│   │   └── tree-{1-5}.svg         ← hero sprinkling trees
│   └── tools/
│       └── *-preview.jpg          ← tool card thumbnails
├── src/
│   ├── i18n/
│   │   └── translations.js        ← all UI strings (DE/FR/IT/EN)
│   ├── layouts/
│   │   └── BaseLayout.astro       ← shared HTML shell
│   ├── components/
│   │   ├── Hero.astro             ← interactive hero banner
│   │   ├── NavBar.astro           ← sticky nav + lang switcher
│   │   ├── LanguageSwitcher.astro ← DE/FR/IT/EN toggle + i18n engine
│   │   ├── IntroBanner.astro      ← full-width intro text section
│   │   ├── ToolsMosaic.astro      ← responsive tool card grid
│   │   └── Footer.astro           ← site footer
│   └── pages/
│       ├── index.astro            ← homepage
│       └── tools/
│           ├── timelapse.astro    ← Timelapse Creator (placeholder)
│           └── baumportraets.astro← Baumarten­porträts (placeholder)
├── astro.config.mjs
├── package.json
└── README.md
```

---

## Colour palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--clr-green-deep` | `#1a3d18` | darkest green, footer |
| `--clr-green-dark` | `#2a5c28` | navbar, buttons |
| `--clr-green-mid`  | `#2e6830` | gradients |
| `--clr-yellow`     | `#ffe84e` | highlights, active states |
| `--clr-red`        | `#c02020` | accents |
| `--clr-green-pale` | `#c8e8a0` | text on dark bg |

All tokens are defined in `src/layouts/BaseLayout.astro` `:root {}`.

## Typography

- **Headings:** Lora (Google Fonts, serif)
- **Body / UI:** Inter (Google Fonts, sans-serif)
