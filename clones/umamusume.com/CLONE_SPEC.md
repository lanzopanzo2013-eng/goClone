# umamusume.com — Clone Specification (machine-readable)

> **What this file is:** a complete, self-sufficient blueprint for rebuilding the official
> *Umamusume: Pretty Derby* English website (<https://umamusume.com/>) as a static site.
> It was reverse-engineered on **2026-11-10** from the live pages, the production
> stylesheets (retrieved via the Internet Archive), and the site's public asset URLs.
>
> **How an AI should use it:** read §0 → §3, then build §5 section by section using the
> geometry and copy provided, pulling images from the manifest in §10. A finished,
> working reference implementation of the home page ships beside this file as
> `index.html` — when in doubt, mirror its markup and computed layout.
>
> **Fidelity key:** everything tagged **[EXACT]** was copied verbatim from the site
> (copy, URLs, CSS values, breakpoints). **[RECONSTRUCTED]** means the value was inferred
> and only needs to *look* right. **[GAP]** marks what could not be observed.

---

## 0. TL;DR for the rebuilding agent

| Item | Value |
|---|---|
| Type of site | Marketing / portal site for a mobile + PC game |
| Pages to build | `/` (home), `/news/`, `/news/[id]`, `/characters/`, `/characters/[slug]`, `/media/` |
| Original stack | SvelteKit (Svelte 5) + Vite, deployed on AWS CloudFront/S3, content from Kuroco headless CMS **[EXACT]** |
| Stack you may use | Any. A single static HTML/CSS/JS file is enough to reproduce the home page. |
| Canvas | Designed at **1920 px**, fluid between **900–2000 px**, hard-capped at **2000 px**; a separate **750 px** canvas is used below 900 px **[EXACT]** |
| Fonts | **Roboto** (body) + **Roboto Condensed** (display, italic/bold) **[EXACT]** |
| Core feel | Comic-book / racing-poster energy: huge italic condensed type, diagonal motion, white "ribbon" title plates, chunky rounded pills, drop-shadow "sticker" UI, pastel category colours, anime key art |
| Motion | Long, soft easings (`cubic-bezier(.19,1,.22,1)`), hover scale-down of stickers, staggered fade/slide-in on scroll, slanted loading wipe |
| Language | English (single locale) |

---

## 1. Site map & routes **[EXACT]**

| Route | Title tag | Purpose |
|---|---|---|
| `/` | `Umamusume: Pretty Derby Official Website \| Cygames` | Landing page: key visual, store links, socials, news, about movie, gameplay, characters carousel, media, footer |
| `/news/` | `News \| Umamusume: Pretty Derby Official Website \| Cygames` | News index with category filters (All News / Game / Media) and infinite "View more" |
| `/news/[id]` | `… \| Cygames` | Article page inside a white "article-box" card |
| `/characters/` | `Characters \| …` | Full roster with sort + search |
| `/characters/[slug]` | character name | Character profile: visual, profile table, voice actor, song list |
| `/media/` | `Media \| …` | Two anchored sections: `#anime` (cards with Watch links) and `#music` (album cards with Spotify links) |

Nav links on the site: **News**, **Characters**, **Media**, plus a **Play Now** CTA. The
footer is injected as a shared web component (`#umamusume-en-footer`) by the Cygames
platform — see §9.

---

## 2. Global design tokens **[EXACT]**

Copy these verbatim. They are the production `:root` variables.

```css
:root{
  /* ---- base neutrals ---- */
  --color-text-base:  #4d4d4d;   /* body copy, icons, arrow default */
  --color-text-gray:  #141414;   /* headings */
  --color-gray:       #d2d2d2;   /* borders / disabled */
  --color-gray-2:     #898989;   /* secondary meta text */
  --color-error:      #ff0000;

  /* ---- brand & category colours, stored as R,G,B triples ---- */
  --color-rgb-blue:            42, 93, 250;    /* #2A5DFA — About, play icon, links */
  --color-rgb-pink:            255, 110, 203;  /* #FF6ECB — primary CTA */
  --color-rgb-green:           60, 167, 50;    /* #3CA732 — Gameplay section */

  --color-rgb-news:            255, 121, 208;  /* #FF79D0 — News main */
  --color-rgb-news-sub:        255, 239, 247;  /* #FFEFF7 — News panel bg */
  --color-rgb-news-dark:       227, 108, 185;  /* #E36CB9 — News borders/labels */

  --color-rgb-characters:      140, 131, 255;  /* #8C83FF — Characters main */
  --color-rgb-characters-dark: 125, 117, 227;  /* #7D75E3 */
  --color-rgb-characters-light:241, 239, 255;  /* #F1EFFF */

  --color-rgb-media:           76, 174, 255;   /* #4CAEFF — Media main */
  --color-rgb-media-dark:      68, 155, 227;   /* #449BE3 */

  /* news category chips */
  --color-rbg-news-game:       181, 217, 19;   /* #B5D913 — "Game"  (note: typo "rbg" is in prod) */
  --color-rbg-news-media:      255, 145, 28;   /* #FF911C — "Media" */
}
```

Supporting values seen in the stylesheets:

| Use | Value |
|---|---|
| News section background behind the pink panel | `#f2ffea` (pale green) **[EXACT]** |
| Article/legal card background | `#fff`, border `1px solid #b9bed2` **[EXACT]** |
| Table zebra rows in articles | `#ebf0f9` **[EXACT]** |
| Kicker/label grey on ribbon buttons | `#73788c` **[EXACT]** |
| Shadow colour | `rgba(0,0,0,.25)` (stickers) / `rgba(0,0,0,.3)` (artwork) **[EXACT]** |
| Loading screen bg | `#fff`, text/art `#4d4d4d` **[EXACT]** |

### Easing curves **[EXACT]**
```css
--ease-out: cubic-bezier(.19, 1, .22, 1);      /* default reveal / hover-out  */
--ease-pop: cubic-bezier(.175,.885,.32,1.275); /* sticker pop / hover-in      */
--ease-in:  cubic-bezier(.77, 0, .175, 1);     /* loading wipe                */
/* secondary */
cubic-bezier(.165,.84,.44,1)  /* image zoom */
cubic-bezier(.25,.46,.45,.94) /* fades */
```

---

## 3. Typography & the scaling system **[EXACT]**

### 3.1 Families

```css
@font-face{
  font-family:roboto;
  src:url(https://parts.cygames.co.jp/assets/fonts/Roboto-VariableFont_wdth,wght.woff2) format("woff2");
  font-weight:100 900; font-display:swap;
}
@font-face{
  font-family:roboto-condensed;
  src:url(https://parts.cygames.co.jp/assets/fonts/RobotoCondensed-VariableFont_wght.woff2) format("woff2");
  font-weight:100 900; font-display:swap;
}
body{ font-family: roboto, sans-serif; font-weight:400; line-height:1;
      color:var(--color-text-base); background:#fff; }
```

Fallback (used in the reference build): Google Fonts
`https://fonts.googleapis.com/css2?family=Roboto+Condensed:ital,wght@0,300..900;1,300..900&family=Roboto:ital,wght@0,300..900;1,300..900&display=swap`

### 3.2 Usage rules

* **Roboto Condensed, weight 700, italic, letter-spacing .05–.06em** → every "UI voice"
  element: nav links, chips, buttons, section titles, character names, dates
  (actually 500 for dates). This is the single most important stylistic rule.
* **Roboto 400** → body copy, article text, table content.
* Headings are *not* semantic-H-weight driven; the site sets `font-size:inherit;
  font-weight:inherit` in the reset and styles each component.

### 3.3 Breakpoints **[EXACT]**

| Range | Meaning | Canvas |
|---|---|---|
| `max-width: 899.98px` | phone (`.is-SP` shown) | **750 px** design width |
| `900px – 1999.98px` | desktop (`.is-PC` shown) | **1920 px** design width |
| `min-width: 2000px` | large desktop | everything freezes at its 2000 px pixel value |

### 3.4 The `--u` unit (reproduce this!)

Every length on the production site is expressed three times (vw for desktop, vw for
phone, fixed px above 2000). The reference build collapses that into one unit:

```css
:root{ --u: 0.1333333333vw; }                 /* phone: 1 design px on a 750 canvas */
@media (min-width:900px){ :root{ --u: min(0.0520833333vw, 1px); } }  /* 1920 canvas, capped */
```

`1 design px = 0.0520833vw` at 1920 (because `100vw / 1920 = 0.0520833vw`), which equals
exactly `1px` on a 1920-wide viewport and stops growing beyond 2000 px. Then write every
dimension as `calc(120 * var(--u))` = "120 px at 1920". Conversion from the production
vw values: `design_px = vw_value × 19.2` for desktop, `× 7.5` for phone.

Also cap the page: `max-width:2000px; margin-inline:auto;` on `body`.

### 3.5 Reference type scale (design px @1920)

| Element | Size / weight |
|---|---|
| Section title (main word) | 56–60 cond. 700 italic |
| Section kicker | 13–15 cond. 700 italic, `.28em` tracking, uppercase |
| Nav link | 20 cond. 700 italic |
| Pill button ("View more", CTA) | 22–25 cond. 700 italic |
| News item title | 19 roboto 700, line-height 1.5 |
| News meta/date | 14 cond. 500 |
| Character name / VA | 22 cond. 700 / 13 roboto |
| Body copy | 16–18 roboto 400 |
| Article body (`.article-box`) | `1.1111vw` ≈ 21 px @1920, line-height 1.5, letter-spacing .02em |

---

## 4. Page shell **[EXACT structure / RECONSTRUCTED header]**

```
body
└─ .site-wrapper                     width:100%; max-width:2000px; overflow:hidden
   ├─ .pattern-bg                    fixed full-bleed background image, z-index:-10
   ├─ header                         fixed, transparent over KV → white on scroll
   ├─ main                           padding-bottom ≈ 134px
   │   └─ section…                  (see §5)
   └─ #umamusume-en-footer           injected shared footer
```

* `.pattern-bg` has `position:fixed; height:100dvh; object-fit:cover; object-position:top;`
  and sits at `z-index:-10`. **[EXACT]** (visible mostly behind the Characters/Media area
  as `bg.BorAeoXQ.jpeg`.)
* Body sets `min-height:100dvh` with a `--vh` fallback for iOS. **[EXACT]**
* `main` bottom padding: **12vw** phone / **6.9444vw** desktop (= **134 px @1920**). **[EXACT]**
* Fixed elements need `padding-right` compensation when a scrollbar exists; the site
  exposes `--scroll-padding-right` and shifts `.pattern-bg` by `-50%` of it. **[EXACT]**

### 4.1 Header **[RECONSTRUCTED]**

Height ≈ **88 design px**. Container: flex, space-between, `padding: 0 40u`.

* Logo image `logo_umamusume.png`, width ≈ **300u**, links to `/`.
* Nav: `News`, `Characters`, `Media` in white condensed italic 20u; hover = underline
  grows from the left in pink + slight fade. Active page = pink underline.
* CTA pill: pink `rgb(--color-rgb-pink)`, white italic text `Play Now`, height 52u,
  radius 999px, drop-shadow, hover `scale(.95)`.
* Scroll state: after ~80 px the bar becomes `#fff` with
  `box-shadow: 0 2px 20px rgba(0,0,0,.12)`, links turn `--color-text-base`.
* Phone: hamburger (3 white bars, turning dark after scroll); panel drops from under the
  bar, white, stacked links at ~36u.

### 4.2 Loading screen **[EXACT]**

Full-viewport white overlay `#loading`. A character bust slides in from the right
(`translate3d(70%,0,0)` → 0, `.6s pop`) with a wordmark SVG below whose paths light up
one by one (staggered opacity `.4 → 1`, 1.5s loop, 50ms offsets). On load the panel is
wiped away with `clip-path: inset(0 0 0 100%)` over `.5s` after a `.5s` delay while the
character exits to the left (`translate3d(-60%,0,0)`, fade). Include it only if you want
the full "official site" feel; the reference build omits it for speed.

---

## 5. Home page — section by section

Order: **Key Visual → News → About → Gameplay → Characters → Media → Footer**.

### 5.1 Key visual (`section.top-kv`) **[EXACT geometry]**

| Property | Desktop (@1920) |
|---|---|
| Section height | **1396 px** (`72.7083vw`) |
| Top padding | **824 px** (`42.9166vw`) |
| Art | full-bleed `kv.CiVddxQD.jpeg`, `object-fit:cover`, mobile swaps to `01_specialweek.DtnlpFlH.webp` |
| Art mask | `mask-image: linear-gradient(to top, transparent, transparent 6%, #000 20%, #000)` (fades the bottom into white) |
| "Play Now!" wordmark | absolutely positioned at `top:-85px`, width ≈ 420 px, `margin-left:-7px` |
| Banner offset | store row starts at `top:93px` |
| Store badges | height **66 px**, `margin:0 8px`, drop-shadow `0 5px 5px rgba(0,0,0,.25)` |
| Social plate | **466 × 66 px**, radius 8 px, white, `margin-left:60px`, padding `0 14px 0 21px` |
| TGA badge | width ≈ 190 px, `top:-203px; right:139px` |
| Scroll rail | vertical "SCROLL" right edge, `top:912px`, 60 px animated line |

Phone (@750 canvas): section **1430 px** tall, artwork pinned top, overlay panel at
`top:836px`, badges 73 px tall, socials full-width 600 px, TGA badge flows inline.

Overlay stack (centered):
1. `kv_txt_playnow.D0FaPRug.png` — **"PLAY NOW!"** display art.
2. Badge row: **Steam**, **App Store**, **Google Play**, **Google Play Games** →
   `https://store.steampowered.com/app/3224770/`,
   `https://apps.apple.com/us/app/umamusume-pretty-derby/id6480433538`,
   `https://play.google.com/store/apps/details?id=com.cygames.umamusume`,
   `https://play.google.com/store/apps/details?id=com.cygames.umamusume&hl=en_GB`.
3. **Cygames WebStore** pill → `https://webstore.cygames.com/en/umamusume_en/`.
   Two images swap on hover: `kv_cygamesid_off` (default) ⇄ `kv_cygamesid_on`.
4. Social plate: label **"Official Social Media"** + X, Facebook, YouTube, Discord:
   `https://x.com/umamusume_eng`, `https://www.facebook.com/umamusume.eng`,
   `https://www.youtube.com/@umamusume_eng`, `https://discord.gg/umamusume-eng`.
5. **THE GAME AWARDS · BEST MOBILE GAME WINNER** badge.
6. Down-arrow / scroll cue.

Interaction: every sticker scales **to .95** on hover with `--ease-pop` in, `--ease-out`
out (`transform .3s` → `transform .5s`).

### 5.2 News (`section.top-news`, pink) **[EXACT geometry]**

| Property | Value |
|---|---|
| Section offset | `margin-top: -161px` (pulls up under the KV), `padding-bottom: 97px` |
| Panel | `.top-section-box` width **1146 px**, centered |
| Panel interior | `#FFEFF7`, 4 px white border, radius 13 px, height **826 px**, padding `42px 0 28px` |
| List | grid, gap 20 px, padding `14px 40px 20px` |
| Section bg | `#f2ffea` with `news_bg.Bh8oYNXe.png` pinned bottom |
| Title plate | white, clip-path ribbon, text pink |
| "View more" pill | **393 × 55 px**, pink fill, 2 px `#E36CB9` border, italic 25 px, double-chevron at right, `margin-top:25px` |

Title plate ribbon shape (use for all sections) **[EXACT]**:

```css
.section-title{
  clip-path: polygon(0 0, var(--ribon) 50%, 0 100%, 100% 100%,
                     calc(100% - var(--ribon)) 50%, 100% 0);
  --ribon: 20px; /* 0.8333vw desktop · 4vw phone */
}
```

Content (captured 2026-11-10, newest first):

| # | Category | Published | Title | Link |
|---|---|---|---|---|
| 1 | Update | 2026/11/10 10:15 (UTC) | Issue with Racing Carnival event | `/news/100119` |
| 2 | Update | 2026/11/06 03:00 (UTC) | Emails sent regarding reimbursement for the 7th EVENT in LOS ANGELES concerts | `/news/100118` |
| 3 | Game | 2026/11/09 22:00 (UTC) | Spotlight Pretty Derby and Spotlight Support Card Scouts out now! | `/news/1165` |
| 4 | Game | 2026/11/09 22:00 (UTC) | The story event Sweet Memories Teatime is here! | `/news/1159` |
| 5 | Game | 2026/11/09 22:00 (UTC) | New title missions are here! | `/news/1168` |

Each item = white rounded row (radius 10 px) with a category chip, date, 2-line
clamped title, and (when available) a 16:9 thumbnail ≈150 px wide on the right/left.
Items 1, 2 and 5 have **no thumbnail** on the live site.
Chip colours: Update = `--color-rgb-news`, Game = `#B5D913` (dark text), Media = `#FF911C`.
The "Details" affordance is a doubled chevron (`arrow_double.nHmJyBTy.svg`), and the
item expands slightly on hover.

Full news archives follow the same row design with filter pills
(**All News / Game / Media**) and a "View more" button that appends the next batch.
`/news/` lists 10 items per page; article bodies live in `.article-box` (§6).

### 5.3 About (`section.top-about`) **[EXACT geometry]**

| Property | Value |
|---|---|
| Section height | **1200 px** (`62.5vw`) |
| Title plate | white bg, **blue** text (`--color-rgb-blue`) |
| Background | `about_bg.CQiNXnT3.jpeg`, absolute, `z-index:-1`, top-aligned |
| Movie plate | **1067 × 600 px** (16:9), centered, `position:absolute; top:50%; left:50%` |
| Play button | **107 px** blue circle, white triangle, drop-shadow |
| Hover | thumbnail `scale(1.08)` over 1 s, blue veil at `opacity:.75` |
| Entrance | starts `translate3d(-50%, calc(-50% + 100px), 0)` + `opacity:0`, settles over `.7s` with `.5s` delay |

Copy: the section is **image-led** — no paragraph text is shown; the thumbnail is the
movie poster (`about_thumbnail.DvTbfr6J.jpeg`) linking to the trailer.

### 5.4 Gameplay (`section.top-gameplay`, green) **[EXACT geometry]**

| Property | Value |
|---|---|
| Section height | **1200 px** desktop, auto on phone |
| Title plate | green bg, white text |
| Background | `gameplay_bg.Bhbdtv2B.png` |
| Carousel | Splide, 3 slides, pagination = white dots (active dot becomes a "teeth/gear" glyph via mask), arrows 46×69 px |
| Slide layout | character art (≈720 px) + 2 screenshot thumbs + one sentence |
| Entrance | active slide's art slides in from the side over `.6s` after `.2s` |

Slides **[EXACT copy]**:

1. Art `gameplay_specialweek` · shots `gameplay_image_1-1`, `1-2`
   → *"Lead your Umamusume to victory by choosing a training regimen that fits their needs!"*
2. Art `gameplay_silencesuzuka` · shots `2-1`, `2-2`
   → *"Interact with a variety of unique Umamusume at Tracen Academy! Train together, and you just might help each other reach new heights!"*
3. Art `gameplay_winningticket` · shots `3-1`, `3-2`
   → *"Up to 18 Umamusume race against each other for first place—watch them go all out as you tune in to the game's incredibly realistic live commentary."*

### 5.5 Characters (`section.top-characters`, purple) **[EXACT geometry]**

* Two huge diagonal colour bands behind the section, both
  `transform: rotate(-22.5deg) scaleX(2)`:
  * band 1 `#8C83FF`, height 1430 px, `transform-origin: top right`, `translateY(-80%)`
  * band 2 `#F1EFFF`, height 306 px, `top: 1306px`
* A `tsparticles` layer sits on top at `opacity:.2`, `mix-blend-mode:multiply`, tinted with
  `--color-characters-main` (subtle confetti/sparkle texture). Optional.
* Title plate: white with purple text.
* Horizontal carousel of character cut-outs (`.character`), each ≈**250 u** wide:
  portrait clipped to an arch (`border-radius: 120u 120u 14u 14u`), name in condensed
  bold, "VA: …" beneath. Hover lifts ~10 px.
* Arrows use the site's shared chevron and sit at `left/right: 56px`, vertically centred.
* Ends with an "Explore" pill linking to `/characters/`.

Home carousel roster (15, order as served) **[EXACT]**:

| # | Name | VA | Art (`…/files/user/character/<slug>/<file>`) |
|---|---|---|---|
| 1 | Special Week | Azumi Waki | `specialweek/specialweek_top.png` |
| 2 | Silence Suzuka | Marika Kohno | `silencesuzuka/silencesuzuka_top.png` |
| 3 | Tokai Teio | Machico | `tokaiteio/tokaiteio_top.png` |
| 4 | Maruzensky | Lynn | `maruzensky/maruzensky_top.png` |
| 5 | Fuji Kiseki | Eriko Matsui | `fujikiseki/fujikiseki_top.png` |
| 6 | Oguri Cap | Tomoyo Takayanagi | `oguricap/oguricap_top.png` |
| 7 | Gold Ship | Hitomi Ueda | `goldship/goldship_top.png` |
| 8 | Vodka | Ayaka Ohashi | `vodka/vodka_top.png` |
| 9 | Daiwa Scarlet | Chisa Kimura | `daiwascarlet/daiwascarlet_top.png` |
| 10 | Mejiro McQueen | Saori Onishi | `mejiromcqueen/mejiromcqueen_top.png` |
| 11 | Winning Ticket | Yui Watanabe | `winningticket/winningticket_top.png` |
| 12 | Rice Shower | Manaka Iwami | `riceshower/riceshower_01_list.png` (list) / `riceshower_top.png` |
| 13 | Kitasan Black | Hinaki Yano | `kitasanblack/kitasanblack_top.png` |
| 14 | Agnes Tachyon | Sumire Uesaka | `agnestachyon/agnestachyon_top.png` |
| 15 | Hokko Tarumae | Sayaka Kikuchi | `hokkotarumae/hokkotarumae_top.png` |

Base URL: `https://en-portal.g.kuroco-img.app/v=<timestamp>/files/user/character/…`
(the `v=` cache-buster is optional; strip it and the CDN still serves the file).

### 5.6 Media (`section.top-media`, blue) **[EXACT]**

* Solid `#4CAEFF` section, white ribbon title with blue text.
* One large clickable card (`media_image.bZStKUoL.png`) ≈1200 u wide, rounded 20 u,
  deep shadow, with an **Explore** pill in the bottom-right (italic condensed 24 u)
  linking to `/media/`.
* Same card pattern is used on `/media/` for anime (with a **Watch** pill) and albums
  (with a **Listen (Spotify)** link).

### 5.7 Footer **[GAP — approximated]**

The real footer is a shared Cygames component injected into `#umamusume-en-footer`.
Observed: it is white, sits at the end of the flow (`margin-top:auto`), and carries the
Cygames legal block. Reproduce with:

* logo (300 u) on the left;
* link row: News · Characters · Media · Cygames WebStore · X;
* small legal line: `© Cygames, Inc.` plus a note that assets are Cygames' property;
* all text `--color-gray-2`, hover underline, font-size 13–15 u.

---

## 6. Sub-page details

### 6.1 `/news/` **[EXACT]**
* Same ribbon title ("News", pink).
* Filter pills: **All News**, **Game**, **Media** — white pills with grey border,
  active state fills with the category colour.
* List of 10 items per page, same row component as the home page.
* "View more" appends the next 10.

### 6.2 `/news/[id]` (article) **[EXACT]**
* Breadcrumb: `Home` › `News` › title (component `BreadCrumb`).
* `.article-box` card: white, `border:1px solid #b9bed2`, width 77.08vw (≈1480 px),
  radius 11 px, padding 83 px 94 px, font-size 21 px, line-height 1.5.
* Inside, headings are black **ribbon** bars:
  `display:inline-flex; background:#4d4d4d; color:#fff; font-weight:700;
   letter-spacing:.05em; padding:6px 63px; clip-path: ribbon(...)`.
* Tables: header row `#4d4d4d` white, zebra `#ebf0f9`, 1 px dividers.
* Links: `rgb(var(--color-rgb-blue))`, underlined, hover opacity `.5`.
* Lists: `disc` / `decimal`, and variants `(a)`, `(i)`.

### 6.3 `/characters/` **[EXACT]**
* Title "Characters", purple ribbon.
* Toolbar: **Sort By** select (`Default`, `Name (A–Z)`, `Name (Z–A)`,
  `Height (Ascending)`, `Height (Descending)`) and a **Search** field.
* Grid of cards, 4 per row desktop / 2 per row phone. Each card: tall cut-out art
  (`*_list.png`), name, `VA: …`, hover shows a **View more** label.
* Roster continues into a second group (staff/instructors): Happy Meek, Bitter Glasse,
  Little Cocon, Tazuna Hayakawa, Yayoi Akikawa, Etsuko Otonashi, Aoi Kiryuin,
  Sasami Anshinzawa, Riko Kashimoto, Light Hello.

Full roster captured (name — VA — slug):

```
Special Week—Azumi Waki—specialweek                 Silence Suzuka—Marika Kohno—silencesuzuka
Tokai Teio—Machico—tokaiteio                        Maruzensky—Lynn—maruzensky
Fuji Kiseki—Eriko Matsui—fujikiseki                 Oguri Cap—Tomoyo Takayanagi—oguricap
Gold Ship—Hitomi Ueda—goldship                      Vodka—Ayaka Ohashi—vodka
Daiwa Scarlet—Chisa Kimura—daiwascarlet             Taiki Shuttle—Yuka Otsubo—taikishuttle
Grass Wonder—Rena Maeda—grasswonder                 Hishi Amazon—Yuiko Tatsumi—hishiamazon
Mejiro McQueen—Saori Onishi—mejiromcqueen           El Condor Pasa—Minami Takahashi—elcondorpasa
T.M. Opera O—Sora Tokui—tmoperao                    Narita Brian—Rika Kinugawa—naritabrian
Symboli Rudolf—Azusa Tadokoro—symbolirudolf         Air Groove—Ruriko Aoki—airgroove
Agnes Digital—Minori Suzuki—agnesdigital            Seiun Sky—Akari Kito—seiunsky
Tamamo Cross—Naomi Ohzora—tamamocross               Fine Motion—Chinami Hashimoto—finemotion
Biwa Hayahide—Yui Kondo—biwahayahide                Mayano Top Gun—Mio Hoshitani—mayanotopgun
Manhattan Cafe—Yui Ogura—manhattancafe              Mihono Bourbon—Ikumi Hasegawa—mihonobourbon
Mejiro Ryan—Afumi Hashi—mejiroryan                  Hishi Akebono—Rei Matsuzaki—hishiakebono
Yukino Bijin—Nozomi Yamamoto—yukinobijin            Rice Shower—Manaka Iwami—riceshower
Ines Fujin—Rika Nagae—inesfujin                     Agnes Tachyon—Sumire Uesaka—agnestachyon
Admire Vega—Hitomi Sasaki—admirevega                Inari One—Haruno Inoue—inarione
Winning Ticket—Yui Watanabe—winningticket           Air Shakur—Minami Tsuda—airshakur
Eishin Flash—Ayami Fujino—eishinflash               Curren Chan—Yu Sasahara—currenchan
Kawakami Princess—Karin Takahashi—kawakamiprincess  Gold City—Saki Kosaka—goldcity
Sakura Bakushin O—Sachika Misawa—sakurabakushino     Seeking the Pearl—Ayaka Fukuhara—seekingthepearl
Shinko Windy—Yuuki Takada—shinkowindy               Sweep Tosho—Shiori Sugiura—sweeptosho
Super Creek—Kana Yuuki—supercreek                   Smart Falcon—Hitomi Owada—smartfalcon
Zenno Rob Roy—Haruka Terui—zennorobroy              Tosen Jordan—Eri Suzuki—tosenjordan
Nakayama Festa—Shino Shimoji—nakayamafesta          Narita Taishin—Keiko Watanabe—naritataishin
Nishino Flower—Haruna Kawai—nishinoflower           Haru Urara—Yukina Shuto—haruurara
Bamboo Memory—Kotomi Aihara—bamboomemory            Biko Pegasus—Aimi Tanaka—bikopegasus
Marvelous Sunday—Marie Miyake—marveloussunday       Matikanefukukitaru—Hiyori Nitta—matikanefukukitaru
Mr. C.B.—Yurina Amami—mrcb                          Meisho Doto—Misaki Watada—meishodoto
Mejiro Dober—Hikari Kubota—mejirodober              Nice Nature—Kaori Maeda—nicenature
King Halo—Iori Saeki—kinghalo                       Matikanetannhauser—Hikaru Tono—matikanetannhauser
Ikuno Dictus—Masumi Tazawa—ikunodictus              Mejiro Palmer—Yuri Noguchi—mejiropalmer
Daitaku Helios—Aya Yamane—daitakuhelios             Twin Turbo—Miharu Hanai—twinturbo
Satono Diamond—Hina Tachibana—satonodiamond         Kitasan Black—Hinaki Yano—kitasanblack
Sakura Chiyono O—Ruriko Noguchi—sakurachiyonoo      Sirius Symboli—Fairouz Ai—siriussymboli
Mejiro Ardan—Saya Aizawa—mejiroardan                Yaeno Muteki—Ayumi Hinohara—yaenomuteki
Tsurumaru Tsuyoshi—Yoshino Aoyama—tsurumarutsuyoshi Mejiro Bright—Ayaka Ohnishi—mejirobright
Sakura Laurel—Mizuki Mano—sakuralaurel              Narita Top Road—Kanna Nakamura—naritatoproad
Yamanin Zephyr—Riona Imaizumi—yamaninzephyr         Symboli Kris S—Meiku Harukawa—symbolikriss
Tanino Gimlet—Misato Matsuoka—taninogimlet          Daiichi Ruby—Karin Isobe—daiichiruby
Aston Machan—Honoka Inoue—astonmachan               K.S.Miracle—Hinata Sato—ksmiracle
Copano Rickey—Konomi Inagaki—copanorickey           Hokko Tarumae—Sayaka Kikuchi—hokkotarumae
Wonder Acute—Kanoko Sudo—wonderacute                Happy Meek—Miyu Yoshizaki—happymeek
Bitter Glasse—Aino Shimada—bitterglasse             Little Cocon—Saho Shirasu—littlecocon
Tazuna Hayakawa—Yukiyo Fujii—tazunahayakawa         Yayoi Akikawa—Kaori Mizuhashi—yayoiakikawa
Etsuko Otonashi—Emiri Suyama—etsukootonashi         Aoi Kiryuin—Miho Okasaki—aoikiryuin
Sasami Anshinzawa—Kikuko Inoue—sasamianshinzawa     Riko Kashimoto—Romi Park—kashimotoriko
Light Hello—Kana Ueda—lighthello
```

Character art URL pattern:
`https://en-portal.g.kuroco-img.app/files/user/character/<slug>/<slug>_top.png` for the
home carousel and `…_list.png` for the index grid. Some slugs use an alternate filename
(`riceshower_01_list.png`, `happymeek/happymik_list.png`, `ksmiracle/k.s.miracle_top.png`),
so always verify per character.

### 6.4 `/media/` **[EXACT]**
* Two anchored tabs: **Anime** (`#anime`) and **Music** (`#music`).
* Anime cards (image + title + **Watch**) — 9 titles:
  1st Anniversary Special Animation · Umayuru: Pretty Gray (Streamed Animation) ·
  Umamusume: Cinderella Gray (Animation) · Umamusume: Pretty Derby Season 3 (TV Animation) ·
  Road to the Top (Streamed Animation) · Umayuru (Streamed Animation) · Season 2 (TV
  Animation) · Umayon (Streamed Animation) · Umamusume: Pretty Derby (TV Animation).
  The 4 newest also appear in a second "featured" row.
* Music cards (image + album title + **Listen(Spotify)**), newest first:
  *The two of us* (`cinderellagray_futari`) · *∞* (`cinderellagray_mugen`) ·
  *Umapyoi Legend (English ver.)* · *Movie "… BEGINNING OF A NEW ERA" OST* ·
  *ANIMATION DERBY Season3 vol.3* · *vol.2 "Akogare Challenge Dash!!"* · *vol.1* ·
  *Road to the Top album* · *Umayuru album* · **WINNING LIVE 06 … 01** ·
  *STARTING GATE Unit Song Collection* · *UMAYON Mini Album* ·
  *ANIMATION DERBY Season 2 vol.3 OST* · … (≈20 items, each with a Spotify album link).
* Ends with **View more** and the shared footer.

---

## 7. Motion & interaction rules

| Interaction | Spec |
|---|---|
| Sticker hover | `transform: scale(.95)`; transition `transform .3s var(--ease-pop)` on enter, `transform .5s var(--ease-out)` on leave |
| Image zoom (thumbnails) | `scale(1.08–1.1)` over 1 s `var(--ease-out)` |
| Play overlay | appears under hover, veil at `opacity:.75` in brand colour |
| Scroll reveal | sections/plates start `opacity:0; translateY(100px)`; on enter `.7s` `var(--ease-out)` |
| Slider | Splide; dots = 25 px circles at `scale(.3)`, active dot = gear/teeth mask `scale(1)`; arrows fade when disabled |
| Nav link | underline `scaleX(0→1)` from the left, 400 ms |
| Character carousel | arrows scroll ±80% of width, `behavior:smooth`; drag-to-scroll on phone |
| Loading wipe | `clip-path: inset(0 → 0 0 0 100%)` over `.5s` |
| Reduced motion | all of the above collapse to instant state |

---

## 8. Responsive summary

| Element | Desktop @1920 | Phone @750 |
|---|---|---|
| Canvas unit | 1u = 1 px | 1u = 1 px (of 750) |
| Header height | 88 | 88 |
| KV height | 1396 (824 top pad) | 1430 (overlay at 836) |
| News panel width | 1146 | 686 |
| News panel height | 826 | auto |
| View-more pill | 393×55 | 520×90 |
| About section | 1200 tall, 1067×600 movie | 920 tall, 700×376 movie |
| Gameplay | 3 columns, 1200 tall | stacked, auto height |
| Characters | 250 u cards, ~6.5 visible | 320 u cards, ~2 visible |
| Media card | 1200 wide | 670 wide |
| Section title | 760×150, ribon 20 | 600×160, ribon 32 |

---

## 9. Things that are dynamic on the real site (and how to fake them)

1. **News feed** — comes from Kuroco CMS; the home page shows the 5 newest. Hard-code the
   table in §5.2 or fetch `/news/` and parse.
2. **Character roster** — CMS-driven; sort/search is client-side.
3. **Footer** — a web component from Cygames' shared platform; approximate (§5.7).
4. **Cookie-consent button** — the site styles `[data-id=cookie_consent_cookie_btn] button`
   blue; optional.
5. **Gameplay slider + characters carousel** — Splide.js. Vanilla implementations are in
   `index.html`; Splide is only needed for touch momentum + looping.
6. **tsParticles** — decorative sparkle layer in the Characters background.

---

## 10. Asset manifest **[EXACT URLs]**

All of these were live on 2026-11-10. Hot-linking works (no referer check observed on
`parts.umamusume.com` / `umamusume.com/assets`), but for anything lasting, download and
self-host with the same paths.

### Brand & UI (`https://parts.umamusume.com/assets/images/`)
```
logo_umamusume.png
app_icon.png
badge-steam.png
badge-appstore.png
badge-googleplay.png
badge-googleplaygames.png
sns-x.svg
sns-facebook.svg
sns-youtube.svg
sns-discord.svg
```

### Home page (`https://umamusume.com/_app/immutable/assets/`)
```
kv.CiVddxQD.jpeg                     key visual (desktop, landscape)
01_specialweek.DtnlpFlH.webp         key visual (phone, portrait)
kv_txt_playnow.D0FaPRug.png          "PLAY NOW!" wordmark
kv_cygamesid_on.DSA25dCm.png         WebStore banner (hover)
kv_cygamesid_off.CGZkdrCk.png        WebStore banner (default)
kv_cygamesid.C4xTPo0s.png            WebStore banner (alt)
TGAmobile_winner.DJe1kMYp.png        The Game Awards badge
news_bg.Bh8oYNXe.png                 news section background
about_thumbnail.DvTbfr6J.jpeg        about movie poster
about_bg.CQiNXnT3.jpeg               about section background
gameplay_bg.Bhbdtv2B.png             gameplay background
gameplay_specialweek.DbgtPsGW.png    slide 1 art
gameplay_silencesuzuka.CF-9agsU.png  slide 2 art
gameplay_winningticket.6_SJzSZq.png  slide 3 art
gameplay_image_1-1.DqKsqutO.png      slide 1 shot A
gameplay_image_1-2.Bh2iV1-Q.png      slide 1 shot B
gameplay_image_2-1.CGQnQoQ9.png      slide 2 shot A
gameplay_image_2-2.DuOVG6XG.png      slide 2 shot B
gameplay_image_3-1.Dn6XnF5v.png      slide 3 shot A
gameplay_image_3-2.kL42DlwX.png      slide 3 shot B
media_image.bZStKUoL.png             media card artwork
bg.BorAeoXQ.jpeg                     page pattern background
```

Vite hashes change on redeploy. If a hash 404s, fetch `https://umamusume.com/`, grep the
`/_app/immutable/assets/` URLs, and substitute.

### Characters (`https://en-portal.g.kuroco-img.app`)
```
/files/user/character/<slug>/<slug>_top.png    portrait / carousel cut-out
/files/user/character/<slug>/<slug>_list.png   index grid art
```
Example: `/v=1744884539/files/user/character/specialweek/specialweek_top.png`

### News thumbnails
```
https://assets-webview-umamusume-en.akamaized.net/contents/assets/images/uploads/Thumbnail/<file>.png?c=<cache>
```
Example: `announce_banner_3146_L1794261600.png?c=20261028021543`.

### Media art
```
https://en-portal.g.kuroco-img.app/v=<ts>/files/user/media/anime/<file>.jpg
https://en-portal.g.kuroco-img.app/v=<ts>/files/user/media/music/<file>.jpg
```

### Original build assets worth knowing
* `teitetsu.BNI5mUfy.svg` — the site's "railway sleeper" divider glyph (used as the active
  slider dot and inside the dashed dividers).
* `decoration_base.ax2DgMiQ.svg` / `decoration_square.CPV5Y4-u.svg` — the scalloped and
  square perforated edges on the pill buttons.
* `arrow_double.nHmJyBTy.svg` — the doubled chevron.
* `icon_play.DDT9Nirq.svg` — the play triangle.

If you cannot fetch an SVG, re-create it inline exactly as the reference build does:
pill edges = two mirrored scallop masks; doubled chevron = two stroked chevrons.

---

## 11. Build recipe (fastest path to a convincing clone)

1. **Skeleton**: one `index.html`; include Roboto + Roboto Condensed; set the tokens and
   `--u` from §2–§3.
2. **Shell**: `.site-wrapper` (max 2000 px), fixed header, `main`, footer.
3. **Hero**: full-bleed `<picture>` key visual with the bottom-fade mask; absolutely
   position the "PLAY NOW!" plate, 4 store badges, WebStore pill, social plate, TGA badge.
   This single section carries ~70 % of the perceived similarity — spend the time here.
4. **Ribbon titles**: white plate + `clip-path` + coloured italic condensed text.
5. **News**: pale-pink panel, 5 rows, chips, "View more" pill.
6. **About**: 16:9 poster with a blue circular play button.
7. **Gameplay**: 3-slide carousel, art left / shots + sentence right, gear dots.
8. **Characters**: two rotated colour bands + horizontal arch-clipped cards.
9. **Media**: blue section, one big rounded card with an "Explore" pill.
10. **Polish**: hover scale-down on every pill, scroll reveals, sticky header state,
    `prefers-reduced-motion` guard, `alt` text on art, keyboard-focusable controls.

### Acceptance checklist

- [ ] At 1920 px wide, the hero is ~1396 px tall and the KV art fades to white at its base.
- [ ] All four store badges, the WebStore pill, the "Official Social Media" plate and the
      TGA badge are present and clickable.
- [ ] Section titles use the ribbon clip-path, and each section uses its own colour:
      News pink `#FF79D0`, About blue `#2A5DFA` (white plate), Gameplay green `#3CA732`,
      Characters purple `#8C83FF`, Media blue `#4CAEFF`.
- [ ] Display text is Roboto Condensed 700 italic; body text is Roboto 400 `#4d4d4d`.
- [ ] Layout scales smoothly 900 → 2000 px and freezes at 2000 px; below 900 px it
      switches to the 750 px canvas and stacks.
- [ ] Pills scale to .95 on hover; artwork zooms ~1.08 with a colour veil.
- [ ] No horizontal scrollbar; images have `alt`; controls are buttons/links with labels.
- [ ] `prefers-reduced-motion` disables reveals and carousel autoplay.

---

## 12. Provenance & honesty notes

* Copy, links, roster, news headlines and timestamps: read from the live pages on
  2026-11-10. **[EXACT]**
* Colour variables, breakpoints, clip-path, easing, section heights and paddings:
  extracted from the site's production CSS
  (`/_app/immutable/assets/0.CeerEmeO.css` and `2.BtMVfDfi.css`, snapshot
  2026-10-08 / 2026-01-01 via the Internet Archive). **[EXACT]**
* Header height, logo width, character card width, media card width, footer content:
  not present in the CSS chunks we recovered — **[RECONSTRUCTED]** to match the visual
  rhythm; tune by eye against a screenshot.
* The site is Cloudflare/bot protected: direct `curl` returns TLS errors and automated
  browsers get 403. Use the archived CSS if you need to re-verify values.
* Fonts and all artwork are © Cygames, Inc. This spec is for study/reimplementation;
  do not ship the art or branding as your own.

---

### Files in this folder
| File | Purpose |
|---|---|
| `CLONE_SPEC.md` | this document |
| `index.html` | working reference clone of the home page (single file, hot-linked assets) |
| `assets.json` | the manifest above as machine-readable JSON |
