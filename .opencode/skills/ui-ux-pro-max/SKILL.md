---
name: ui-ux-pro-max
description: "UI/UX design intelligence for web and mobile. Includes 50+ styles, 161 color palettes, 57 font pairings, 99 UX guidelines, and 25 chart types across 10 stacks (React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui, and HTML/CSS). Use when designing UI, building landing pages, dashboards, or reviewing UX."
---

# UI/UX Pro Max - Design Intelligence

Comprehensive design guide for web and mobile applications. Contains 50+ styles, 161 color palettes, 57 font pairings, 99 UX guidelines, and 25 chart types across 10 technology stacks.

## When to Apply

Use this skill when the task involves: UI structure, visual design decisions, interaction patterns, or user experience quality control.

### Must Use
- Designing new pages (Landing Page, Dashboard, Admin, SaaS, Mobile App)
- Creating or refactoring UI components (buttons, modals, forms, tables, charts)
- Choosing color schemes, typography systems, spacing standards, or layout systems
- Reviewing UI code for UX, accessibility, or visual consistency
- Implementing navigation, animations, or responsive behavior

### Skip
- Pure backend logic, API/database design only
- Performance optimization unrelated to UI
- Infrastructure/DevOps work
- Non-visual scripts or automation

## Priority Rule Categories

### 1. Accessibility (CRITICAL)
- **Color contrast**: Minimum 4.5:1 ratio for normal text (3:1 for large text)
- **Focus states**: Visible focus rings (2-4px) on interactive elements
- **Alt text**: Descriptive alt text for meaningful images
- **Aria labels**: aria-label for icon-only buttons
- **Keyboard nav**: Tab order matches visual order
- **Skip links**: Skip to main content for keyboard users
- **Heading hierarchy**: Sequential h1->h6, no level skip
- **Reduced motion**: Respect prefers-reduced-motion
- **Screen readers**: Logical reading order with accessibilityLabel

### 2. Touch & Interaction (CRITICAL)
- **Touch target**: Min 44x44pt (iOS) / 48x48dp (Android)
- **Touch spacing**: Minimum 8px gap between touch targets
- **Hover independence**: Don't rely on hover alone for primary interactions
- **Loading feedback**: Disable button during async; show spinner
- **Error feedback**: Clear error messages near the problem field
- **Standard gestures**: Use platform standard gestures consistently
- **Press feedback**: Visual ripple/highlight on press
- **Safe areas**: Keep targets away from notch, Dynamic Island, gesture bar

### 3. Performance (HIGH)
- **Image optimization**: WebP/AVIF, responsive images (srcset/sizes), lazy load
- **Image dimensions**: Declare width/height or aspect-ratio to prevent CLS
- **Font loading**: Use font-display: swap/optional
- **Lazy loading**: Lazy load non-hero components
- **Bundle splitting**: Split code by route/feature
- **Virtualize lists**: Virtualize lists with 50+ items
- **Input latency**: Keep under ~100ms for taps/scrolls

### 4. Style Selection (HIGH)
- **Style match**: Match style to product type
- **Consistency**: Same style across all pages
- **SVG icons**: Use SVG (Heroicons, Lucide), not emojis
- **Color palette**: Choose from product/industry
- **Dark mode**: Design light/dark variants together
- **Icon consistency**: One icon set across the product
- **Primary action**: One primary CTA per screen

### 5. Layout & Responsive (HIGH)
- **Viewport**: width=device-width, initial-scale=1 (never disable zoom)
- **Mobile-first**: Design mobile-first, scale up
- **Breakpoints**: Systematic breakpoints (375 / 768 / 1024 / 1440)
- **Font size**: Minimum 16px body text on mobile
- **Line length**: 35-60 chars mobile, 60-75 desktop
- **No horizontal scroll**: Content must fit viewport
- **Spacing**: 4pt/8dp incremental spacing system
- **z-index**: Define layered scale (0/10/20/40/100/1000)

### 6. Typography & Color (MEDIUM)
- **Line height**: 1.5-1.75 for body text
- **Font pairing**: Match heading/body font personalities
- **Font scale**: Consistent type scale (12/14/16/18/24/32)
- **Contrast**: Darker text on light backgrounds
- **Color semantics**: Define semantic color tokens, never raw hex
- **Dark mode**: Desaturated/lighter tonal variants, not inverted
- **Number tabular**: Use tabular figures for data columns

### 7. Animation (MEDIUM)
- **Duration**: 150-300ms for micro-interactions
- **Performance**: Use transform/opacity only, never width/height/top/left
- **Loading states**: Skeleton/progress for >300ms loads
- **Easing**: ease-out for entering, ease-in for exiting
- **Motion meaning**: Every animation expresses cause-effect
- **Spring physics**: Prefer spring-based curves for natural feel
- **Exit faster than enter**: ~60-70% of enter duration
- **Interruptible**: User tap cancels in-progress animation

### 8. Forms & Feedback (MEDIUM)
- **Input labels**: Visible label per input (not placeholder-only)
- **Error placement**: Error below the related field
- **Submit feedback**: Loading then success/error on submit
- **Empty states**: Helpful message + action when no content
- **Toast dismiss**: Auto-dismiss in 3-5s
- **Inline validation**: Validate on blur, not keystroke
- **Password toggle**: Show/hide toggle for password fields
- **Multi-step progress**: Step indicator with back navigation

### 9. Navigation (HIGH)
- **Bottom nav**: Max 5 items with labels + icons
- **Back behavior**: Predictable and consistent; preserve scroll/state
- **Deep linking**: All key screens reachable via deep link
- **Nav state**: Current location visually highlighted
- **Modal escape**: Clear close/dismiss affordance
- **State preservation**: Back restores scroll position and input state

### 10. Charts & Data (LOW)
- **Chart type**: Match to data type (trend=line, comparison=bar, proportion=pie)
- **Accessible colors**: Avoid red/green only pairs
- **Data table**: Provide table alternative for a11y
- **Legend**: Always show legend near chart
- **Tooltip**: On hover (web) or tap (mobile)
- **Responsive**: Charts reflow/simplify on small screens
- **Empty state**: Meaningful message when no data

## How to Use

1. Analyze user requirements (product type, audience, style keywords, stack)
2. Generate design system: recommend style, colors, typography based on product type
3. Search for specific details (UX rules, color palettes, font pairings)
4. Apply platform-specific best practices for the target stack
5. Run pre-delivery checklist: accessibility, dark mode, touch targets, safe areas

## Pre-Delivery Checklist
- [ ] No emojis as icons (use SVG/vector)
- [ ] All icons from consistent family
- [ ] Pressed states don't shift layout
- [ ] Touch targets >=44x44pt
- [ ] Micro-interactions 150-300ms
- [ ] Primary text contrast >=4.5:1 (both modes)
- [ ] Safe areas respected for fixed elements
- [ ] Verified on small/large phone + tablet
- [ ] 4/8dp spacing rhythm maintained
- [ ] Reduced motion supported
- [ ] Screen reader labels on all meaningful elements

## References
- Color palettes, font pairings, and style guides in references/
- Framework-specific best practices in references/
