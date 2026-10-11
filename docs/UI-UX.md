# UI/UX Specification: KopSusRen Dashboard and Chat Simulator

Status: v0.1, direction approved by the owner ("Oat and Sage").
Applies to: M2 (dashboard) and M3 (chat simulator), and any later UI work.

Precedence: on visual and UX matters this document wins over the PRD. On business rules the PRD wins. Items marked **[OPEN]** must not be decided by an agent: stop and record them in `docs/questions.md`. Items marked **[ASSUMPTION]** are defaults the owner can change.

## 1. Principles

1. Minimalist, calm, warm. Whitespace over decoration.
2. Fast on low-end devices (old laptops, entry-level phones). Performance is a feature, not a polish step.
3. "Liquid glass" is seasoning, not the meal: translucency and a soft border on most surfaces, real blur in at most two places.
4. One primary action per page.
5. Server-rendered Jinja2 + HTMX. Hand-written CSS. No CSS framework, no JS framework.
6. The UI language is Bahasa Indonesia.

## 2. Design tokens

All colors live as CSS variables in `app/web/static/css/tokens.css`. No raw hex values anywhere else (CSS or templates). Light mode only in v1; dark mode is deferred (the variable structure must allow it later).

```css
:root {
  --bg: #F6F3EE;
  --bg-wash-sage: #E8EFE9;
  --bg-wash-latte: #F1E6DA;
  --surface: #FFFFFF;
  --glass: rgba(255, 255, 255, 0.62);
  --glass-border: rgba(255, 255, 255, 0.9);
  --hairline: #E4DED4;
  --hairline-strong: #B8AFA1;

  --text: #2B2622;
  --text-2: #6F665D;

  --primary: #4F7A64;
  --primary-hover: #446A55;
  --on-primary: #FFFFFF;
  --focus: #4F7A64;

  --tint-sage: #DDE8E0;
  --tint-sage-text: #3F5F4E;
  --tint-latte: #EFE2D3;
  --tint-latte-text: #5E4430;
  --tint-gold: #F6E7C4;
  --tint-gold-text: #6B4E12;
  --tint-danger: #F3DAD6;
  --tint-danger-text: #8A3F36;
  --tint-neutral: #ECE7DF;
  --tint-neutral-text: #5A524A;

  --danger-strong: #A8493D;
  --progress-track: #E8E2D8;

  --accent: #B08968;
  --warning: #D4A24C;
  --danger: #C26B5F;

  --sp-1: 4px;  --sp-2: 8px;  --sp-3: 12px; --sp-4: 16px;
  --sp-5: 24px; --sp-6: 32px; --sp-7: 48px;
  --r-ctl: 10px; --r-card: 16px; --r-pill: 999px;

  --fs-xs: 0.75rem;   --fs-sm: 0.8125rem; --fs-base: 0.9375rem;
  --fs-md: 1.125rem;  --fs-lg: 1.375rem;  --fs-xl: 1.75rem;
}
```

Usage rules for color:

- `--primary` is the only filled action color. Hover uses `--primary-hover`.
- `--accent`, `--warning`, `--danger` are decorative only (dots, borders, bars). Never use them as text color or as a background behind text. For text-bearing surfaces use the `--tint-*` pairs.
- Destructive buttons use `--danger-strong` fill with `--on-primary` text.
- Never use color alone to convey status: every status shows a text label.

Contrast contract (WCAG 2.x relative-luminance formula). All pairs below must be at least 4.5:1; the focus ring against `--bg` must be at least 3:1:

1. `--text` on `--bg`, `--text` on `--surface`
2. `--text-2` on `--bg`, `--text-2` on `--surface`
3. `--on-primary` on `--primary`, `--on-primary` on `--primary-hover`
4. `--on-primary` on `--danger-strong`
5. `--tint-sage-text` on `--tint-sage`
6. `--tint-latte-text` on `--tint-latte`
7. `--tint-gold-text` on `--tint-gold`
8. `--tint-danger-text` on `--tint-danger`
9. `--tint-neutral-text` on `--tint-neutral`
10. `--focus` on `--bg` (non-text, 3:1)

The values above are the owner-approved intent and the ratios were estimated by hand. The agent must compute the ratios with a script (see section 12). If a pair fails, do not silently change a token: report the failing pair and propose the smallest lightness change in `docs/questions.md`.

## 3. Typography

- Font stack: `system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif`. No web fonts, no `@font-face`, no font downloads.
- Weights: 400 and 500 only. Never 600, 700, `bold`, or `bolder`.
- Base size `--fs-base` (15px), line-height 1.5 for body and 1.25 for headings.
- Scale: `--fs-xs` captions/pill text, `--fs-sm` labels and helper text, `--fs-base` body and buttons, `--fs-md` card titles, `--fs-lg` page titles (h1), `--fs-xl` metric numbers.
- Money, quantities, and counts use `font-variant-numeric: tabular-nums`.
- Sentence case everywhere. No ALL CAPS, no Title Case.

## 4. Spacing, radius, layout

- Spacing only from the `--sp-*` scale. Radius only from `--r-*`.
- Mobile first. Breakpoints: 640px and 900px. Content max width 1080px. Page padding 16px (mobile) and 24px (desktop).
- Shell at 900px and up: left sidebar 220px (solid `--surface`, no blur) plus content area.
- Shell below 900px: sticky top bar (`.glass-bar`) with the navigation inside a `<details>` element (no JavaScript).
- Use CSS grid and flexbox only. Use `minmax(0, 1fr)` for grid columns that contain tables or long text.
- Touch targets at least 44px high on mobile.

## 5. Background and glass

Static page background (no animation, no `background-attachment: fixed`):

```css
body {
  background:
    radial-gradient(900px 500px at 8% -8%, var(--bg-wash-sage), transparent 60%),
    radial-gradient(800px 480px at 100% 0%, var(--bg-wash-latte), transparent 55%),
    var(--bg);
  background-repeat: no-repeat;
  color: var(--text);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif;
  font-size: var(--fs-base);
  line-height: 1.5;
}
```

Cards (no blur):

```css
.card {
  background: var(--glass);
  border: 1px solid var(--glass-border);
  outline: 0.5px solid var(--hairline);
  outline-offset: -1px;
  border-radius: var(--r-card);
  padding: var(--sp-4) 20px;
}
```

Real blur is allowed on exactly two selectors: `.glass-bar` (mobile top bar) and `.modal` (the dialog panel). Never on cards, tables, rows, or sidebars. At most two elements with `backdrop-filter` may exist in the DOM at the same time.

```css
.glass-bar, .modal { background: var(--glass); border: 1px solid var(--glass-border); }
@supports (backdrop-filter: blur(1px)) {
  .glass-bar, .modal { backdrop-filter: blur(10px); }
}
@media (prefers-reduced-transparency: reduce) {
  .card, .glass-bar, .modal { background: var(--surface); backdrop-filter: none; }
}
```

Blur radius is at most 10px and is never animated. Shadows: none, except one soft shadow on the modal (`0 8px 24px rgba(43, 38, 34, 0.12)`) and the focus ring. No stacked shadows, no glow, no neon, no gradients other than the body background above.

## 6. Components

Class names are part of the contract (tests rely on them).

- **Button** `.btn`: secondary by default (transparent, 1px `--hairline-strong` border, `--text`). Variants `.btn-primary` (fill `--primary`), `.btn-danger` (fill `--danger-strong`), `.btn-ghost` (no border). Min height 40px (44px on mobile), horizontal padding 16px, radius `--r-ctl`, font 15px/500. Hover: primary goes to `--primary-hover`, secondary gets `--tint-neutral` background. Avoid disabled buttons; keep them enabled and respond with a clear message. If a button truly must be disabled, show the reason next to it.
- **One `.btn-primary` per page.** A confirmation dialog may contain one `.btn-danger` plus one secondary button.
- **Pill** `.pill` with variants `.pill-sage`, `.pill-latte`, `.pill-gold`, `.pill-danger`, `.pill-neutral` (the matching `--tint-*` pair). Radius `--r-pill`, padding 4px 12px, `--fs-xs`.
- **Card** `.card` (section 5). **Metric card** `.metric`: label in `--fs-sm`/`--text-2`, value in `--fs-xl`/500 with tabular numbers.
- **Table** `.table`: hairline row dividers, no zebra stripes, no heavy borders. Under 640px each row becomes a stacked block using `data-label` attributes (CSS only). Wide tables scroll inside their own `overflow-x: auto` wrapper, never the page body.
- **Form**: label above the control, control height 40px, 1px `--hairline-strong` border, radius `--r-ctl`, background `--surface`. Focus: `outline: 2px solid var(--focus); outline-offset: 2px`. Helper text in `--text-2`; error text in `--tint-danger-text` with the message next to the field. Server-side validation returns the form with messages (HTMX swap).
- **Progress bar** `.progress`: 8px track `--progress-track`, fill `--primary`, with `role="progressbar"` and `aria-valuenow/min/max`.
- **Flash message** `.flash` (+ `-sage`, `-gold`, `-danger`): inline banner at the top of the content area, server-rendered, `aria-live="polite"`. No floating toasts.
- **Modal**: native `<dialog class="modal">`; `::backdrop` is `rgba(43, 38, 34, 0.35)` with no blur. Used for destructive confirmations only (cancel session, cancel order).
- **Empty state**: one-line title, one-line explanation, at most one primary button.
- **Loading**: HTMX adds `.htmx-request`; reduce the target's opacity to 0.6 and show the text "Memuat…". No spinners, no skeleton shimmer.
- **Icons**: none by default. If needed, inline SVG with `aria-hidden="true"`, at most 8 distinct icons, each at most 600 bytes. No icon fonts, no emoji.
- **Motion**: only `opacity` and `transform`, at most 150ms, and disabled under `prefers-reduced-motion: reduce`.

## 7. Pages

Every page: one `<h1>`, `<html lang="id">`, a skip link to main content, and at most one `.btn-primary`.

1. **Masuk (login)**: centered card, username and password, primary "Masuk". Generic error "Nama pengguna atau kata sandi salah." Login rate-limit message "Terlalu banyak percobaan. Coba lagi nanti."
2. **Ringkasan (overview)**: three `.metric` cards (Order masuk, Pendapatan, Kuota terjual "x dari y"); a current-session card (title, closing time, status pill, `.progress`, per-product quota rows, buttons "Lihat order" primary and "Tutup PO" secondary); the five latest orders. If no session is open: empty state "Belum ada PO yang dibuka" with primary "Buat sesi PO".
3. **Produk**: table (Nama, Harga, Status, Ubah). Primary "Tambah produk". Form page for create/edit.
4. **Sesi PO**: list (Judul, Status, Buka, Tutup, Terjual/Kuota), primary "Buat sesi". Detail page: info block, product-and-quota table, and state-dependent actions: SCHEDULED shows "Buka sekarang" (secondary) and "Batalkan sesi" (danger, confirm dialog); OPEN shows "Tutup sekarang" and "Batalkan sesi"; CLOSED shows "Ekspor CSV" (secondary).
5. **Order**: filter bar (Sesi, Status) above the table (Waktu, Pelanggan, Item, Total, Status, Aksi). Status changes use a select plus confirmation. "Ekspor CSV" is secondary. Zero primary buttons is allowed.
6. **Pelanggan**: list with order counts; detail page with order history.
7. **Log**: two stacked sections, "Log audit" and "Percakapan terbaru". Phone numbers masked.
8. **Simulator chat** (dev only): chat bubbles (customer right with `--tint-sage`, bot left with `--glass`), identity switch (Pelanggan/Owner) with fake numbers, message box with primary "Kirim". The route returns 404 unless `SIMULATOR_ENABLED=1` (default off).

## 8. Copy and formatting

- Bahasa Indonesia, sentence case, active voice, verb-first button labels ("Buat sesi", "Tutup PO", "Ekspor CSV").
- No exclamation marks in system copy. No filler words such as "berhasil" in toasts: say "Sesi dibuka".
- Errors say what happened and what to do, in one sentence. Never show raw exception text or stack traces.
- Money: `Rp 25.000` (dot as thousands separator, no decimals). Dates: `17 Okt 2026, 17.00 WIB` (Asia/Jakarta).
- Phone numbers: show the first 4 and last 3 digits (`0812****345`). Full numbers only where the owner explicitly opens a customer detail page.

Status labels:

| Internal value | Label | Pill |
|---|---|---|
| Session DRAFT | Draf | neutral |
| Session SCHEDULED | Terjadwal | gold |
| Session OPEN | Dibuka | sage |
| Session CLOSED | Ditutup | neutral |
| Session CANCELLED | Dibatalkan | danger |
| Order DRAFT | Draf | neutral |
| Order CONFIRMED | Terkonfirmasi | sage |
| Order PAID | Dibayar | latte |
| Order FULFILLED | Selesai | sage |
| Order CANCELLED | Dibatalkan | danger |

## 9. Accessibility

- Text contrast per section 2. Visible focus ring on every interactive element.
- Full keyboard operation. Semantic HTML (`nav`, `main`, `table`, `button`, `label`). Every form control has a label.
- Support `prefers-reduced-motion` and `prefers-reduced-transparency`.
- Status is never conveyed by color alone.
- `aria-live="polite"` on flash messages.

## 10. Performance budget [ASSUMPTION]

- CSS: at most 24 KB uncompressed in total. JS: at most 70 KB uncompressed in total. HTML per page: at most 60 KB.
- No external requests of any kind (fonts, CDNs, analytics). Everything is served from `/static`.
- HTMX is vendored (self-hosted) at a pinned version that the agent verifies from the official source. Record the version and SHA-256 in `docs/decisions.md`.
- No images except one inline SVG logo of at most 2 KB.
- Static files are served with `ETag` and `Cache-Control`.
- No client-side charting library; use CSS bars.
- The agent must measure and report the actual sizes in the M2 report.

## 11. Forbidden

- CSS or JS frameworks (Tailwind, Bootstrap, React, Vue, Alpine, jQuery), icon fonts, web fonts, CDN links, `@import`.
- `backdrop-filter` outside `.glass-bar` and `.modal`; blur on cards, rows, or sidebars; animated blur.
- Gradients other than the body background; animated backgrounds; video.
- `box-shadow` other than the modal shadow and the focus ring.
- `font-weight` 600 or higher; ALL CAPS styling.
- Raw hex colors outside `tokens.css`.
- More than one `.btn-primary` per page; floating toasts; spinners; skeleton shimmer.
- Emoji in the UI.
- Improvising visual changes. Any deviation from this document must be listed in the task report and approved by the owner.

## 12. Conformance tests (part of M2)

Create `tests/web/test_ui_contract.py` and `scripts/check_contrast.py` (Python standard library only). Test names carry the IDs below.

- **UI-1** Compute WCAG contrast for every pair in section 2 by parsing `tokens.css`; fail below the thresholds.
- **UI-2** `tokens.css` defines every token listed in section 2; no other CSS file or template contains a raw hex color.
- **UI-3** `backdrop-filter` appears only inside `@supports` blocks for `.glass-bar` and `.modal`; blur value at most 10px.
- **UI-4** No `@import`, no `@font-face`, no `http://` or `https://` URLs in CSS, JS (apart from comments), or templates.
- **UI-5** Total CSS and JS sizes are within the budgets in section 10.
- **UI-6** Each page, rendered through the test client with fake data, has `<html lang="id">`, exactly one `<h1>`, at most one `.btn-primary`, and every `<img>` has an `alt`.
- **UI-7** No `font-weight` of 600 or higher or `bold`/`bolder`; gradients appear only in the `body` rule.
- **UI-8** The simulator route returns 404 when `SIMULATOR_ENABLED` is unset.

## 13. Definition of done for UI work

- `make test` and `make lint` pass, including UI-1 to UI-8.
- Measured CSS, JS, and HTML sizes reported against the budget.
- If a headless browser is available, screenshots at 360px and 1280px width using fake data only, saved to `docs/screens/`. Otherwise report the screenshots as UNVERIFIED.
- A list of deviations from this document (must be empty or owner-approved).
- No real phone numbers or customer data in screenshots, fixtures, or logs.

## 14. Open items

- Logo and brand name treatment: **[OPEN]**.
- Dark mode: deferred past v1.
- Bot persona and tone (PRD Q8) only affects simulator copy, not this specification.
