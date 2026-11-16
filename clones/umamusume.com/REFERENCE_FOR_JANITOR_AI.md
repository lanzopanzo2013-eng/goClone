# Umamusume.com CSS reference for a profile-design agent

## Start here: provenance and coverage

This is a **reference archive**, not a complete, runnable website clone. The original minified stylesheet bytes are in `_raw/css/` and `_raw/external/parts.umamusume.com/assets/css/`; they have not been prettified or rewritten. The separately maintained `index.html` and `CLONE_SPEC.md` are an earlier reconstructed visual approximation, **not official site source**. When those conflict with the archived stylesheets, trust the stylesheets.

The snapshot is from 2026-11-16; production deployments can change. The original successful fetch recorded nine app stylesheets and five rendered pages. A later raw Wayback capture supplied `1.BFJOTM7r.css` (Wayback capture dated 2026-11-13), and the two shared header/footer stylesheets were fetched from parts.umamusume.com. Original and supplemental manifests record source and SHA-256. See `_raw/FETCH_MANIFEST.json`, `_raw/FETCH_MANIFEST-0.json`, `_raw/FETCH_MANIFEST-2.json`, and `_raw/additional-css-fetch.json`. Some supplemental files saved by the interrupted shard have no surviving per-file fetch record; do not infer whether those particular files came from the live host or Wayback. Matching SHA-256 values verify local integrity against the saved manifests, not a fresh comparison to today's live site.

**Incomplete coverage:** the captured app bundle names 20 stylesheet files. Ten were obtained; ten known app files are still missing after the live origin returned HTTP 403 and Wayback returned HTTP 429. Their names are listed by `python3 clones/umamusume.com/verify_archive.py`. Additional unvisited routes, dynamic content, images, or externally hosted resources may also be missing. The tool exits 0 for verified complete known coverage, 1 for missing known CSS, and 2 for integrity errors. It does not prove site-wide completeness or authenticity beyond the recorded hashes. Use `additional-css-fetch.json` for the attempted URLs and errors.

To attempt the missing files again, the repository's `fetch-umamusume-css` GitHub Actions workflow can be run manually on this branch. It preserves previously recorded provenance, saves any newly fetched stylesheet, and reports incomplete coverage as a failed final check. Running it cannot guarantee that the live host or Wayback will allow access.

The `_raw` folders group assets for inspection, rather than preserving every URL-relative path. Consequently CSS `url(...)` references may not resolve locally; this archive is not a drop-in offline deployment. The archived pages contain production markup and Svelte-generated classes, not Janitor AI's markup. Confirm the target platform's current CSS features, selectors, and policy independently; do not assume site-specific Svelte selectors work on a Janitor AI profile. Official assets and brand elements may be subject to copyright and trademark rights.

## Where to look

| File | What to study |
| --- | --- |
| `_raw/css/0.CeerEmeO.css` | Reset, fonts, root colors, common responsive/interaction and loading styles. |
| `_raw/css/2.BtMVfDfi.css` | Home page layout, decorative sections, transitions and patterns. |
| `_raw/css/4.DBnK5a_4.css` | Character page styles. |
| `_raw/css/8.CadhOIyJ.css` | Media page styles. |
| `_raw/css/9.CVDkr8qk.css` | News page styles. |
| `_raw/css/1.BFJOTM7r.css` | Additional route/layout CSS from Wayback. |
| `_raw/css/ButtonBase.DAU0tdJM.css` | Reusable pill button, decorative endcaps, shadows and hover. |
| `_raw/css/LowerLayout.OrFN1E7Y.css` | Secondary-page shell and skewed title banner. |
| `_raw/css/NewsItem.BW2Y3wsu.css` | Rounded news card, category accents and entry animation. |
| `_raw/css/Modal.DqwlE6Qt.css` | Full-screen overlay, content layout, modal transitions. |
| `_raw/external/parts.umamusume.com/assets/css/{header.7t5x1aId,footer.DrBbS_Io}.css` | Header and footer styles from the shared parts service. |
| `_raw/pages/` | Five rendered pages from the original crawl, useful for class/markup context. |
| `_raw/external/parts.umamusume.com/{header,footer}/index.html` | Shared component markup; injected by the shared component script. |
| `_raw/js/app.D_SVNIEA.js` | Archived application bundle naming the route stylesheet chunks. |

## Actual root colors

These names and values are transcribed from `0.CeerEmeO.css`. The `rbg` spelling in the last two custom properties is the site's spelling, not a correction.

```css
:root {
  --color-text-base: #4d4d4d;
  --color-text-gray: #141414;
  --color-gray: #d2d2d2;
  --color-gray-2: #898989;
  --color-error: #ff0000;
  --color-rgb-blue: 42, 93, 250;
  --color-rgb-pink: 255, 110, 203;
  --color-rgb-green: 60, 167, 50;
  --color-rgb-news: 255, 121, 208;
  --color-rgb-news-sub: 255, 239, 247;
  --color-rgb-news-dark: 227, 108, 185;
  --color-rgb-characters: 140, 131, 255;
  --color-rgb-characters-dark: 125, 117, 227;
  --color-rgb-characters-light: 241, 239, 255;
  --color-rgb-media: 76, 174, 255;
  --color-rgb-media-dark: 68, 155, 227;
  --color-rbg-news-game: 181, 217, 19;
  --color-rbg-news-media: 255, 145, 28;
}
```

The root stylesheet defines variable **Roboto** and **Roboto Condensed**, weights 100–900, from `parts.cygames.co.jp` and uses `font-display: swap`. The body uses `roboto, sans-serif`, weight 400, `line-height: 1`, dark-gray text and white background. Fonts are archived under `_raw/external/parts.cygames.co.jp/assets/fonts/`; use a safe sans-serif fallback if the target cannot load custom fonts.

## Responsive and motion patterns

- Recurring tiers: mobile `max-width: 899.98px`; mid-size desktop `min-width: 900px` and `max-width: 1999.98px`; wide desktop `min-width: 2000px`. Many dimensions scale in `vw` at the first two tiers, then switch to fixed pixels at the widest tier. `LowerLayout` also caps the page at `2000px`.
- The news card example uses `padding: 3.2vw; border-radius: 2.1333333333vw` on mobile, `1.3888888889vw; .5555555556vw` on mid-sized desktop, and `27.7777777778px; 11.1111111111px` at 2000px and above. These are site-specific, not automatically appropriate for a profile card.
- Motion commonly uses `cubic-bezier(.19,1,.22,1)` for a soft finish, `cubic-bezier(.175,.885,.32,1.275)` for springy scale changes, and `cubic-bezier(.165,.84,.44,1)` for fading. The news card enters over `.7s`; the base button changes scale over `.3s` normally and `.5s` on hover.
- Desktop hover is gated with `(hover: hover) and (pointer: fine) and (min-width: 900px)`. The base button scales to `.95`; news cards scale to `.97` on hover. Avoid hover-only functionality on touch devices.
- Add a `prefers-reduced-motion: reduce` override in a new adaptation; this is an accessibility recommendation, **not a claim that every source animation includes one**. Avoid leaving profile content permanently transparent if the original site's `.loaded`/`.is-show` JavaScript states do not exist.

## Transferable component cues

1. **Buttons:** white pill, bold colored text and outline, `border-radius: 999px`, a subtle drop shadow and mirrored decorative SVG endcaps. Color comes from `--color-button`. Use an actual button or link with a visible keyboard focus state.
2. **News/profile cards:** white rounded surfaces, soft dark translucent drop shadow, slight letter spacing and a small category color marker. Use a simplified local class or the platform's actual exposed selector rather than copying `.svelte-…` hash classes.
3. **Section title:** a strongly colored, skewed (`-15deg`) banner, white text, subtle image texture and a multiply overlay (`LowerLayout`). Preserve readable text by applying skew to the decoration or counter-skewing content as needed.
4. **Modal:** fixed full-screen container, near-white translucent backdrop (`#ffffffe6`), centered foreground and short `.2s` open/close animation. Implement focus trapping, keyboard dismissal and correct accessible labels yourself if the target supports a modal.
5. **Color system:** choose a main accent (pink for news, purple for characters, blue for media), pair it with a darker accent and pale background, and keep the primary text neutral gray. Check contrast before using the brighter colors for small text.

## Handoff instructions

Read the relevant original CSS and example markup first; then write a **new scoped stylesheet** against the actual selectors and constraints provided by Janitor AI. Do not paste the production reset or the whole site CSS into a profile: it can affect unrelated interface elements, references site-specific markup and images, and may not be permitted by the target. Scope rules to the profile area, use responsive/clamped values suitable for a narrower card, preserve keyboard accessibility and reduced motion, and test desktop and mobile layouts. The missing production files above mean this reference is partial, not evidence of the complete site's styling.
