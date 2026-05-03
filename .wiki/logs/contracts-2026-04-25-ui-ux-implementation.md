---
title: Contracts 2026 04 25 Ui Ux Implementation
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

# CONTRACTS: cekwajar.id UI/UX Deep Implementation

## Execution Order
Serial (must run in sequence):
1. Contract 1 (Foundation: Font + Colors + globals.css)
2. Contract 2 (shadcn/ui Core Components)
3. Contract 3 (Fix Bilingual Pollution + Accessible PercentileBar)
4. Contract 4 (Empty State + Form Micro-interactions)
5. Contract 5 (FreemiumGate Rework)
6. Contract 6 (Footer + Landing Page Polish)

Final gate: Run `ls -la components/ui/` and `cat app/globals.css` to verify all files exist

---

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Font loading fails with next/font | L | M | Fallback to Google Fonts CDN link tag |
| Tailwind v4 CSS vars syntax conflict | L | H | Use @theme inline syntax per existing pattern |
| shadcn components conflict with existing Badge | M | M | Extend existing Badge, don't replace |
| Bilingual fix removes legitimate Chinese | H | M | Verify Chinese chars are 逃/性/样本/七 vs actual content |
| FreemiumGate animation causes layout shift | M | L | Test with content below gate |

---

## CONTRACT #1: Foundation — Plus Jakarta Sans + Semantic Colors + globals.css Cleanup

### WHAT:
Implement foundation layer: add Plus Jakarta Sans font via next/font/google, add semantic CSS custom properties for verdict colors (wajar=emerald, perhatian=amber, critical=red), surface colors, and globals.css polish (custom scrollbar, selection color, focus-visible styles).

### FILES:
READ:
- /home/newadmin/cekwajar.id/app/layout.tsx
- /home/newadmin/cekwajar.id/app/globals.css

WRITE:
- /home/newadmin/cekwajar.id/app/layout.tsx (update font import)
- /home/newadmin/cekwajar.id/app/globals.css (complete rewrite with semantic tokens)

### DONE_WHEN:
- [ ] Plus Jakarta Sans loaded via next/font/google in layout.tsx
- [ ] CSS variables: --color-wajar, --color-perhatian, --color-critical with semantic meaning
- [ ] Surface colors: --surface-background, --surface-card, --surface-border
- [ ] Custom scrollbar styled (webkit-scrollbar)
- [ ] ::selection color matches brand
- [ ] :focus-visible uses ring style instead of outline
- [ ] globals.css contains @import "tailwindcss" and @theme inline blocks

PROOF_FORMAT:
```bash
cat /home/newadmin/cekwajar.id/app/layout.tsx | grep -i "Jakarta"
cat /home/newadmin/cekwajar.id/app/globals.css | grep -E "(wajar|perhatian|critical|surface)"
```

### BLOCKER_IF:
- next/font/google fails to import Plus Jakarta Sans (use fallback to CDN link tag)
- Tailwind v4 @theme inline syntax not recognized (verify @import "tailwindcss" is present)

DEPENDS_ON: none

---

## CONTRACT #2: shadcn/ui Core Components

### WHAT:
Add missing shadcn/ui components to components/ui/: Card, Button, Input, Label, Select, Skeleton, Toast, Sheet. Each component must follow shadcn/ui patterns with proper TypeScript types and variants.

### FILES:
READ:
- /home/newadmin/cekwajar.id/components/ui/badge.tsx (existing pattern to follow)
- /home/newadmin/cekwajar.id/components/ui/badge.tsx

WRITE (create each):
- /home/newadmin/cekwajar.id/components/ui/card.tsx (Card, CardHeader, CardContent, CardFooter, CardTitle, CardDescription)
- /home/newadmin/cekwajar.id/components/ui/button.tsx (Button with variants: default, secondary, outline, ghost, destructive, link)
- /home/newadmin/cekwajar.id/components/ui/input.tsx (Input with proper focus styles)
- /home/newadmin/cekwajar.id/components/ui/label.tsx (Label with htmlFor association)
- /home/newadmin/cekwajar.id/components/ui/select.tsx (Select trigger + content pattern)
- /home/newadmin/cekwajar.id/components/ui/skeleton.tsx (Skeleton with pulse animation)
- /home/newadmin/cekwajar.id/components/ui/toast.tsx (Toast component with toaster setup)
- /home/newadmin/cekwajar.id/components/ui/sheet.tsx (Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter, SheetClose)

### DONE_WHEN:
- [ ] All 8 component files exist in components/ui/
- [ ] Each has proper TypeScript interfaces extending HTML element types
- [ ] Button has 6 variants: default, secondary, outline, ghost, destructive, link
- [ ] Card has: Card, CardHeader, CardContent, CardFooter, CardTitle, CardDescription
- [ ] Input has focus-visible ring styling
- [ ] Skeleton has pulse animation
- [ ] Toast uses Sonner-style toaster pattern

PROOF_FORMAT:
```bash
ls -la /home/newadmin/cekwajar.id/components/ui/
wc -l /home/newadmin/cekwajar.id/components/ui/*.tsx
```

### BLOCKER_IF:
- Component files fail to compile due to TypeScript errors
- Missing dependency (ensure lucide-react is imported for icons)

DEPENDS_ON: 1 (needs globals.css ready for CSS variables)

---

## CONTRACT #3: Fix Bilingual Pollution + Accessible PercentileBar

### WHAT:
Remove Chinese characters from kabur and gaji pages. Add proper ARIA attributes to PercentileBar for accessibility (role="meter", aria-valuenow, aria-label).

### FILES:
READ:
- /home/newadmin/cekwajar.id/app/(wajar)/kabur/page.tsx
- /home/newadmin/cekwajar.id/app/(wajar)/gaji/page.tsx

WRITE:
- /home/newadmin/cekwajar.id/app/(wajar)/kabur/page.tsx (remove Chinese chars)
- /home/newadmin/cekwajar.id/app/(wajar)/gaji/page.tsx (remove Chinese chars, update PercentileBar accessibility)

### DONE_WHEN:
- [ ] kabur page has NO Chinese characters: 逃, 走, 可, 性, 尽, 飞, 七
- [ ] gaji page has NO Chinese characters: 样, 本, 资, 库
- [ ] PercentileBar has role="meter" attribute
- [ ] PercentileBar has aria-valuenow={user} attribute
- [ ] PercentileBar has aria-label describing what the meter shows
- [ ] Both pages still function correctly after edits

PROOF_FORMAT:
```bash
grep -E "(逃|走|可|性|尽|飞|七|样|本|资|库)" /home/newadmin/cekwajar.id/app/\(wajar\)/kabur/page.tsx
grep -E "(逃|走|可|性|尽|飞|七|样|本|资|库)" /home/newadmin/cekwajar.id/app/\(wajar\)/gaji/page.tsx
grep "role=\"meter\"" /home/newadmin/cekwajar.id/app/\(wajar\)/gaji/page.tsx
grep "aria-valuenow" /home/newadmin/cekwajar.id/app/\(wajar\)/gaji/page.tsx
```

### BLOCKER_IF:
- Chinese characters found (grep returns non-empty)
- Page fails to render after edits
- PercentileBar accessibility breaks the component

DEPENDS_ON: 2 (components needed for form elements)

---

## CONTRACT #4: Empty State Component + Form Micro-interactions

### WHAT:
Create a reusable EmptyState component with icon, message, and CTA button. Add form micro-interactions: focus ring transitions, valid check icons (using lucide-react CheckCircle2/XCircle), error shake animations using CSS keyframes.

### FILES:
READ:
- /home/newadmin/cekwajar.id/components/ui/card.tsx (from contract 2)
- /home/newadmin/cekwajar.id/components/ui/button.tsx (from contract 2)

WRITE:
- /home/newadmin/cekwajar.id/components/ui/empty-state.tsx (new EmptyState component)
- /home/newadmin/cekwajar.id/app/globals.css (add shake animation keyframes)

MODIFY:
- /home/newadmin/cekwajar.id/app/(wajar)/gaji/page.tsx (add form validation visual feedback)
- /home/newadmin/cekwajar.id/app/(wajar)/kabur/page.tsx (add form validation visual feedback)

### DONE_WHEN:
- [ ] EmptyState component exists at components/ui/empty-state.tsx
- [ ] EmptyState accepts: icon (LucideIcon), title, description, cta (optional button props)
- [ ] globals.css contains @keyframes shake animation
- [ ] Form inputs show green border on valid state (border-green-500)
- [ ] Form inputs show red border + shake animation on error (border-red-500 + animate-shake)
- [ ] Submit button shows spinner while loading (using lucide-react Loader2 with animate-spin)

PROOF_FORMAT:
```bash
cat /home/newadmin/cekwajar.id/components/ui/empty-state.tsx | head -30
grep -E "(shake|@keyframes)" /home/newadmin/cekwajar.id/app/globals.css
grep -E "(border-green|border-red|animate-shake)" /home/newadmin/cekwajar.id/app/\(wajar\)/gaji/page.tsx
```

### BLOCKER_IF:
- EmptyState component fails to render
- CSS animation causes performance issues
- Form validation logic breaks existing functionality

DEPENDS_ON: 2 (needs UI components)

---

## CONTRACT #5: FreemiumGate Rework

### WHAT:
Replace blur overlay with gradient fade from transparent to white. Add upgrade card at bottom of gated content. Add smooth slide-up animation on mount. Improve visual hierarchy with better typography and spacing.

### FILES:
READ:
- /home/newadmin/cekwajar.id/components/FreemiumGate.tsx

WRITE:
- /home/newadmin/cekwajar.id/components/FreemiumGate.tsx (complete rework)

### DONE_WHEN:
- [ ] No blur backdrop-filter CSS property
- [ ] Uses gradient mask: linear-gradient(to bottom, transparent 0%, white 40%)
- [ ] Upgrade card positioned at bottom with shadow-xl
- [ ] animate-slide-up class on upgrade card (fade + translateY)
- [ ] Uses Card component from components/ui/card.tsx
- [ ] Uses Button component from components/ui/button.tsx
- [ ] Shows pricing: "Mulai dari Rp 29.000/bulan"
- [ ] Close/Back button returns to previous page

PROOF_FORMAT:
```bash
grep -E "(blur|gradient|mask)" /home/newadmin/cekwajar.id/components/FreemiumGate.tsx
grep "animate-slide-up" /home/newadmin/cekwajar.id/components/FreemiumGate.tsx
grep "Card\|Button" /home/newadmin/cekwajar.id/components/FreemiumGate.tsx
```

### BLOCKER_IF:
- Gradient fade doesn't cover content properly on different screen sizes
- Upgrade card overlaps important content
- Animation causes jank on mobile

DEPENDS_ON: 2 (needs Card and Button components)

---

## CONTRACT #6: Footer with Trust Signals + Landing Page Polish

### WHAT:
Create a comprehensive Footer with: logo, tagline, navigation links, social links (Twitter/X, LinkedIn, GitHub using lucide-react icons), security badge (SSL, data protection). Landing page: add hover states with scale+shadow on tool cards, staggered entrance animation on tool cards, improved pricing cards with hover lift effect.

### FILES:
READ:
- /home/newadmin/cekwajar.id/app/page.tsx

WRITE:
- /home/newadmin/cekwajar.id/components/ui/footer.tsx (new Footer component)
- /home/newadmin/cekwajar.id/app/page.tsx (update landing page with animations)

MODIFY:
- /home/newadmin/cekwajar.id/app/layout.tsx (add Footer to layout)

### DONE_WHEN:
- [ ] Footer component exists at components/ui/footer.tsx
- [ ] Footer contains: Logo "cekwajar.id", tagline in Indonesian
- [ ] Footer links: Tentang, Privasi, Kontak, Syarat & Ketentuan
- [ ] Social icons: Twitter, Linkedin, Github (from lucide-react)
- [ ] Security badges: Shield + Lock icons with "Data Aman" text
- [ ] Tool cards have hover:scale-105 + hover:shadow-xl transitions
- [ ] Tool cards have staggered animation-delay on load
- [ ] Pricing cards have hover:-translate-y-1 effect
- [ ] Popular badge on Pro plan has subtle pulse animation

PROOF_FORMAT:
```bash
cat /home/newadmin/cekwajar.id/components/ui/footer.tsx | head -50
grep -E "(scale|shadow|delay|animate)" /home/newadmin/cekwajar.id/app/page.tsx | head -20
```

### BLOCKER_IF:
- Footer breaks responsive layout on mobile
- Animation causes layout shift on page load
- Social icons are not properly sized

DEPENDS_ON: 2 (needs Button component for Footer CTA)

---

## Final Verification Commands

After ALL contracts complete, run:

```bash
# Verify all UI components exist
ls -la /home/newadmin/cekwajar.id/components/ui/

# Verify globals.css has semantic tokens
cat /home/newadmin/cekwajar.id/app/globals.css

# Verify no Chinese characters remain
grep -rE "(逃|走|可|性|尽|飞|七|样|本|资|库)" /home/newadmin/cekwajar.id/app/\(wajar\)/

# Verify PercentileBar accessibility
grep -E "(role=|aria-)" /home/newadmin/cekwajar.id/app/\(wajar\)/gaji/page.tsx

# Run lint check
cd /home/newadmin/cekwajar.id && npm run lint
```

---

END OF CONTRACTS
