---
name: arabic-text
description: Arabic, Persian, Urdu and Hebrew text - base direction, word and letter animation that keeps Arabic letters joined, fonts.
metadata:
  tags: arabic, rtl, persian, urdu, hebrew, typography, text-animation, captions
---

# Arabic and right-to-left text

## Set the base direction

Put `dir="rtl"` and `lang` on the element that holds right-to-left text.

Words or letters wrapped in `display: inline-block` (needed for `translate`, `scale`, `rotate`) are neutral to the bidi algorithm. Without a base direction the line defaults to LTR, so the words are placed left to right and the sentence reads backwards, even though every word looks correct. This is the usual failure of word-by-word captions and karaoke highlights.

When the language comes from props, decide the direction from the words. Count words rather than reading the first letter, because Arabic captions often start with a Latin brand name:

```tsx
const RTL = /[\u0590-\u08FF\uFB1D-\uFDFF\uFE70-\uFEFF]/;
const isRtl = (words: string[]) =>
  words.filter((w) => RTL.test(w)).length > words.length / 2;

<div dir={isRtl(words) ? 'rtl' : 'ltr'}>{/* word spans */}</div>
```

## Animate words, not letters

Arabic letters change shape depending on their neighbours. `text.split('')`, `[...text]` or `Array.from(text)` put each letter in its own box, and a letter in an `inline-block` is shaped alone, so the word falls apart into isolated letters.

Prefer word-level or line-level animation for Arabic. Split on spaces, give the container `dir="rtl"`, animate each word.

## Per-letter animation, if it is needed

Split into units that the browser can still join:

- keep harakat (vowel marks) in the same unit as their letter
- keep lam + alef (`لا`, `لأ`, `لإ`, `لآ`) as one unit, it is a ligature
- keep runs of digits and Latin as one unit, or an RTL line reverses them
- add a zero-width joiner (`\u200D`) on each side of a unit that connects to its neighbour, so each unit is drawn in its connected form

```tsx
const ZWJ = '\u200D';
const RIGHT_JOINING = /[\u0622-\u0625\u0627\u0629\u062F-\u0632\u0648\u0671-\u0673\u0675-\u0677\u0688-\u0699\u06C0\u06C3-\u06CB\u06CD\u06CF\u06D2\u06D3\u06D5]/;
const LETTER = /[\u0620-\u064A\u066E-\u06D3\u06D5\u06FA-\u06FC\u06FF]/;
const LTR_RUN = /^[0-9\u0660-\u0669\u06F0-\u06F9A-Za-z\u066B\u066C.,:%]+$/;
const MARK = /[\u064B-\u065F\u0670\u06D6-\u06ED]/;
const MARKS = /[\u064B-\u065F\u0670\u06D6-\u06ED\u200D]/g;
const first = (u: string) => u.replace(MARKS, '')[0] ?? '';
const last = (u: string) => u.replace(MARKS, '').slice(-1);
const joinsPrev = (u: string) => LETTER.test(first(u)) && first(u) !== '\u0621';
const joinsNext = (u: string) =>
  LETTER.test(last(u)) && last(u) !== '\u0621' && !RIGHT_JOINING.test(last(u));

export const splitArabicLetters = (text: string): string[] => {
  const g: string[] = [];
  for (const ch of text) {
    if (MARK.test(ch) && g.length > 0) g[g.length - 1] += ch;
    else g.push(ch);
  }
  const units: string[] = [];
  for (let i = 0; i < g.length; i++) {
    if (LTR_RUN.test(g[i])) {
      let run = g[i];
      while (g[i + 1] && LTR_RUN.test(g[i + 1])) run += g[++i];
      units.push(run);
    } else if (first(g[i]) === '\u0644' && /[\u0622\u0623\u0625\u0627]/.test(first(g[i + 1] ?? ''))) {
      units.push(g[i] + g[++i]);
    } else {
      units.push(g[i]);
    }
  }
  return units.map((u, i) => {
    const before = i > 0 && joinsNext(units[i - 1]) && joinsPrev(u) ? ZWJ : '';
    const after = i < units.length - 1 && joinsNext(u) && joinsPrev(units[i + 1]) ? ZWJ : '';
    return before + u + after;
  });
};
```

Render the units in a container with `dir="rtl"`, one `inline-block` span per unit, and animate the spans as usual. In Remotion's Chrome renders the letters join exactly as in the unsplit word.

## Fonts

Load an Arabic font explicitly, for example `@remotion/google-fonts/NotoSansArabic`, `IBMPlexSansArabic`, `Cairo` or `Tajawal`. See [google-fonts.md](google-fonts.md). A Latin-only font falls back to whatever Arabic font the render machine has.

Avoid `letterSpacing` and `textTransform` on Arabic text.

The ZWJ technique needs care outside Chrome: Safari draws a ZWJ-padded letter in a fallback font when the font has no U+200D glyph, so the same composition shown in the `<Player>` on an iPhone can mix two typefaces inside a word. Alexandria (as served by Google Fonts), IBM Plex Sans Arabic, Cairo and Tajawal have no U+200D glyph; Noto Sans Arabic and Noto Naskh Arabic do. Video renders are not affected.
