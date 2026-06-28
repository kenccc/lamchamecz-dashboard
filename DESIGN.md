# Làm Cha Mẹ CZ — Monochrome Chic

A boutique, editorial dashboard for a children's parenting/education brand. The
identity is **"Monochrome Chic"**: timeless urban energy meets high-end editorial
minimalism — calm authority, architectural precision, restrained confidence. Built
on a left-sidebar app shell with industrial-glass surfaces over a parchment canvas.

## 1. Visual Theme & Atmosphere

Minimalism crossed with **Industrial Glassmorphism**. Heavy whitespace, a strictly
curated low-chroma palette, smoked-glass surfaces (sharp backdrop blur + desaturated
white) that read as polished concrete rather than soft amber. Depth comes from thin
borders and tonal layering, not bright color or heavy shadow.

Mood: sophisticated, composed, editorial.

## 2. Color

Parchment canvas, white / industrial-glass surfaces, one low-chroma ink primary, and
a strictly monochrome treatment of everything decorative.

- **Page:** `--bg #f1f0ea` (Parchment). Bone `--bg-deep #e8e7e1` for lifts.
- **Surfaces:** white `--surface #ffffff`; industrial glass `--glass-surface
  rgba(255,255,255,.6)` / `--glass-surface-strong rgba(255,255,255,.78)` with backdrop
  blur for elevated/sticky elements (sidebar, cards, hero, auth).
- **Primary:** Shadow Grey `--accent #2d232e`. Deep hover → near-black `--accent-deep
  #161015`. Faint ink wash `--accent-soft rgba(45,35,46,.06)`. Drives nav-active,
  primary buttons, calendar events, progress bars, focus rings.
- **Text:** `--text #2d232e` (Shadow Grey), muted `--text-muted #474448` (Gunmetal),
  soft `--text-soft #8a868c` (Taupe).
- **Borders:** Taupe ink at low opacity — `--border (.10)`, `--border-strong (.20)`,
  `--border-warm (.32)`. These define structure in lieu of shadows.
- **Decorative palette is monochrome.** The `--brand-*` tokens and every `.stat-card--*`
  variant resolve to a tonal ink/bone ramp — never categorical color. The UI does not
  go rainbow.
- **Semantic stays real (muted):** success `#4a6b4f`, warning `#8a6a3b`, danger/error
  `#962d2d`, each with a soft tint. Used for flashes, form errors, and calendar
  day-offs only.

## 3. Typography

Editorial serif display over a clean sans body.

- **Display / headings:** `Playfair Display` (high-contrast serif). Weights 600–800,
  tight tracking. Used for h1–h5, page titles, card headers, stat/metric values.
- **Body / UI / labels:** `Inter`. Weights 400–700. Labels and utility text are
  UPPERCASE with wide letter-spacing for an architectural counterpoint to the serif.
- Both load from Google Fonts in `main.css`.

Scale: 13 / 15 / 18 / 20 / 24 / 32 / 48 / 64.

## 4. Component Stylings

**App shell**
- Fixed left sidebar (`--sidebar-w 256px`), industrial glass (translucent white +
  strong blur), thin right border. Logo on top, icon nav, user + language + logout in
  the footer. Active link = solid `--accent` (Shadow Grey) pill, white text.
- Main content scrolls right of the sidebar; centered to `--max-width 1280px`, generous
  `--gutter 40px` desktop margins.
- Collapses to a top bar + dropdown under 900px (`data-nav-toggle` / `data-nav-menu` /
  `.is-open`).

**Page header** (`.page-head`)
- Lives in the content area (not a global app bar): uppercase breadcrumb, Playfair
  title, sub-line, and right-aligned primary action. The list/form pages lead with it.

**Buttons**
- Rounded `--radius-md (8px)`, weight 700, slight tracking.
- Primary: solid `--accent` fill, white text. Hover → `--accent-deep` (near-black).
- Secondary: white fill, ink border. Ghost: transparent. Auth CTA is uppercase + tracked.

**Cards**
- Industrial glass: `--glass-surface` + backdrop blur, 1px ink border, radius
  `--radius-xl (16px)`. Hover lifts opacity toward `--glass-surface-strong`.
- **Stat cards:** ink icon chip + big Playfair value + uppercase label + a short ink
  underline bar. Monochrome — the color variants are tonal, not categorical.
- **Summary bento** (`.summary-card`): metric + uppercase label with an icon chip to
  the right. **Quick stats** (`.qstat`): label / Playfair value rows + thin progress bars.
- **Tiles:** quick-action shortcuts — icon chip + serif label, lift on hover.

**Hero** (`.hero`)
- Dashboard lead: glass banner with a pill welcome badge, large Playfair headline (with
  an italic second line), Inter lede, and the grayscale logo at right.

**Tables**
- White surface, uppercase tracked headers on bone, 1px row dividers, ink hover wash.
- Identity cells (`.id-cell`) pair an initials avatar with name + sub. Status as chips.

**Calendar (Google Calendar style)**
- Real month grid: Monday-first localized weekday header + week rows.
- Lesson days = faint ink-wash cell + a solid Shadow-Grey event chip. Days off =
  `--danger-soft` cell with a struck red number (semantic red kept). Today = solid ink
  number badge. Out-of-month days dimmed. Built server-side in
  `core/services.build_calendar_months()`.

**Inputs**
- White fill, ink border, radius `--radius-md`. Focus: `--accent` border + accent ring.

## 5. Layout Principles

- App shell: `grid-template-columns: var(--sidebar-w) 1fr`.
- Dashboard / statistics split into a main column + 340px rail (`.grid-dash`).
- 8px spacing rhythm; generous 40px desktop margins, 24px gutters.
- Left-aligned, grid-forced, editorial compositions — avoid centered content.

## 6. Depth & Elevation

Industrial glass + tonal layering. Thin ink borders over soft cool shadows
(`0 4px 20px -2px rgba(45,35,46,.07)`). Higher elevation = more opaque glass fill, not a
bigger shadow. Backdrop blur on sidebar, cards, hero, and the auth card (with a faint
atmospheric ink wash behind it). 8px rounding softens the industrial palette.

## 7. Do's and Don'ts

**Do**
- Keep the page parchment and surfaces white/glass; let ink borders carry structure.
- Use Playfair for any display moment; Inter (often uppercase + tracked) everywhere else.
- Keep one low-chroma ink primary; keep decorative elements monochrome.
- Round to 8px; lean on borders and blur over heavy shadows.

**Don't**
- Reintroduce the kid-blue / rainbow palette, Fredoka/Nunito, bubbly radii, or colored
  glow shadows (the previous "Playful Kids" system — removed).
- Paint the UI with categorical color, or grey out the *semantic* states (error stays red).
- Use sharp corners or hard drop shadows.

## 8. Responsive Behavior

- Sidebar → top bar + dropdown under 900px.
- Dashboard / statistics rail stacks under the main column under 1100px.
- Hero stacks vertically under 860px. Calendar day cells shrink; event chips stay legible.

## 9. Token Source

All values live in `static/core/css/tokens.css`; components read tokens, so re-theming is
a token edit. Class names are kept (`.glass-card`, `.glass-nav__link`, etc.) for stability.
Boutique structural patterns (page-head, hero, schedule list, progress stats, summary
bento, identity cells) live in `static/core/css/components/boutique.css`.

## 10. Agent Prompt Guide

Bias: parchment page, white / industrial-glass cards with thin ink borders and backdrop
blur, Shadow-Grey ink primary, monochrome decorative treatment, Playfair Display headings
+ Inter (uppercase tracked) labels, 8px rounding, left sidebar shell, editorial page
headers, Google-Calendar-style month grids.

Reject: kid-blue/rainbow accents, Fredoka/Nunito, pill-bubbly radii, colored glow shadows,
categorical color on surfaces, fully-greyed semantic states.
