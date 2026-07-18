# CLAUDE.md

Guidance for AI assistants working in this repository.

## What this repository is

A single-page static marketing website for **Vorgrow**, a digital info-product
agency ("we turn your expertise into a product that sells"). The entire site is
one self-contained file with no build step, no dependencies, and no framework.

```
.
├── index.html   # The whole site: HTML + all CSS (in <style>) + all JS (in <script>)
├── DESIGN.md    # Design-system spec (Framer.com analysis) used as the original reference
└── CLAUDE.md    # This file
```

There is no package.json, no test suite, no linter config, and no CI. Do not
introduce a build toolchain, external CSS/JS files, or npm dependencies unless
explicitly asked — the single-file architecture is intentional.

## Development workflow

- **Edit `index.html` directly.** All styles live in the `<style>` block in
  `<head>`; all behavior lives in the `<script>` block at the end of `<body>`.
- **Preview** by opening the file in a browser (or `python3 -m http.server`).
  The only external requests are Google Fonts (Bricolage Grotesque, Albert
  Sans, JetBrains Mono) — everything else is inline, including all imagery,
  which is hand-written inline SVG.
- **Commits** follow the existing style: short, imperative, descriptive
  subject lines summarizing the visual/content change (e.g. "Switch to light
  theme: white background, black text, light-blue accent"). One logical
  redesign step per commit.
- Work happens on `claude/*` feature branches; push with
  `git push -u origin <branch>`.

## Relationship between DESIGN.md and index.html

This matters and is easy to get wrong:

- `DESIGN.md` is a token-level analysis of **Framer.com's** marketing design
  system (dark canvas, GT Walsheim display type, white pill CTAs, gradient
  spotlight cards). The page was originally built from it (`d4d287d`).
- The site has since **deliberately diverged**: it is now a **light theme**
  ("tinted paper" `#fcfcfb` canvas, near-black ink, deep royal-blue
  `#1c2bb5` accent) with substituted fonts (Bricolage Grotesque for display,
  Albert Sans for body, JetBrains Mono for eyebrows). Do NOT "fix" the page
  back toward DESIGN.md's dark palette or fonts.
- What the page **still keeps** from the spec: the structural token system
  (CSS custom properties in `:root` mirroring DESIGN.md's names), the 5px-base
  spacing scale, the radius scale (10/15/20/30/100px, pills-only CTAs), the
  1199px max-width container, the 810px/520px responsive collapse points, the
  56px nav, 96px section rhythm, and the gradient hex values (retained in
  `:root` for the spotlight-card pattern).
- **`index.html` is the source of truth for the current visual state.**
  Treat DESIGN.md as historical reference for layout/spacing/component
  conventions, not as the current palette or type spec.

## Page structure (index.html)

Sections in order, each a `<section class="section">` inside a `.container`:

1. **Nav** (`#nav`) — fixed 56px bar, blur backdrop, gains a hairline border
   on scroll via the `scrolled` class.
2. **Hero** — two-column grid: left copy + CTA pills, right inline-SVG
   illustration delimited by `<!-- HERO-VISUAL-START/END -->` comments.
3. **What we do** (`#what`) — centered narrative `.prose` block.
4. **Services** (`#services`) — `.feature-grid`, a 3×2 hairline-bordered
   feature matrix with inline stroke-icon SVGs.
5. **Process** (`#process`) — the signature interactive piece: a circular
   SVG dial (`.process-dial`) with 5 clickable ring segments and positioned
   label buttons, driving tab panels (`.dpanel`). Auto-advances every 6.5s,
   pauses on hover/focus, starts when scrolled into view, and is fully
   disabled under `prefers-reduced-motion`. Segment geometry: 5 segments of
   72° each (`stroke-dasharray` on r=120 circles, rotated); the pointer
   line/dot position is computed in JS (`pt(deg, r)`).
6. **FAQ** (`#faq`) — native `<details>/<summary>` accordions.
7. **CTA** (`#contact`) — single dark navy (`--ink-deep`) conversion card;
   the only dark surface on the page.
8. **Footer** — link columns plus a giant gradient-masked "Vorgrow"
   wordmark (`.footer-wordmark`).

JS is three small vanilla pieces: nav scroll class, an IntersectionObserver
that reveals `.reveal` elements with staggered delays, and the process-dial
IIFE. No libraries.

## Conventions to follow

- **Design tokens first.** Colors, radii, spacing, and fonts are CSS custom
  properties in `:root`. Use existing tokens (`var(--ink-muted)`,
  `var(--sp-xl)`, `var(--r-pill)`, …) rather than hard-coding values; add a
  new token if a value will be reused.
- **Buttons are pills only** (`--r-pill`), min-height 44px, with an
  `:active` scale-down. Primary = royal blue fill; secondary = light surface
  with hairline border. No ghost/bordered-only buttons, no squared CTAs.
- **One accent color.** `--accent-blue` (#1c2bb5) is used for CTAs, links,
  and active states only — never as a section background. Text hierarchy is
  binary: `--ink` or `--ink-muted`.
- **Imagery is inline SVG**, hand-authored, using the palette hexes. No
  raster images, no external image URLs. Icons are 24-viewBox stroke icons
  (stroke-width ~1.7, round caps/joins, `aria-hidden="true"`).
- **Copy voice:** plain, confident, second person ("You bring the expertise.
  We bring the system."). The business is an **"agency"**, never "studio".
  **No em-dashes in site copy** — use commas, colons, or periods (an earlier
  commit purged them deliberately).
- **Accessibility is already wired in — preserve it:** `prefers-reduced-motion`
  guards on all animation, `role="tab"`/`aria-selected`/`role="tabpanel"` on
  the process dial, `aria-label`/`aria-hidden` on SVGs, native disclosure
  elements for FAQ.
- **Responsive breakpoints:** 810px (grids collapse, nav links hidden, hero
  stacks) and 520px (single column). Match these when adding layout.
- **Typography classes**, not per-element font styles: `.display-xxl/-xl/-lg/-md`
  (Bricolage, clamp()-scaled, tight negative tracking), `.subhead`, `.body-lg`,
  `.body-sm`, `.caption`, `.eyebrow` (mono, uppercase, letter-spaced).

## Things NOT to do

- Don't split the file into separate CSS/JS assets or add a bundler.
- Don't revert to the DESIGN.md dark theme, GT Walsheim/Inter fonts, or
  white-pill-on-black CTAs.
- Don't add more than one gradient spotlight card per viewport if the
  `.spotlight` pattern is used (per the design spec's scarcity rule).
- Don't introduce a second accent color or mid-tone grays outside the
  existing token set.
- Don't remove the reduced-motion guards or the reveal-on-scroll pattern.
