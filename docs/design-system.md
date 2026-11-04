# Design system

Implemented in `mobile/app/src/main/java/ke/ac/bics/cbcapp/ui/theme/`.

Dynamic colour is **off**: the app always uses the CBC palette, even on Android 12+.

## Colour

### Base palette

| Token | Light | Dark | Used for |
|---|---|---|---|
| `background` | `#FFFDF5` | `#151517` | Page background |
| `foreground` / `onBackground` | `#151517` | `#FFFDF5` | Body text, icons (the inverse of the background) |
| `surface` / card | `#FFFFFF` | `#1C1C20` | Cards, sheets, dialogs |
| `muted` / `surfaceVariant` | `#EBE9E1` | `#232327` | Chips, inactive tabs, skeletons |
| `mutedForeground` | `#6B675C` | `#A5A29A` | Captions, secondary text |
| `border` / `outline` | `#E4E0D5` | `#2E2E33` | Dividers, input outlines |
| `primary` | `#362486` | `#362486` | Brand fill, buttons |
| `onPrimary` | `#FFFDF5` | `#FFFDF5` | Text on primary |
| `destructive` / `error` | `#C9282E` | `#FF6B6B` | Errors, delete, wrong answers |
| `errorContainer` | `#FBE9E9` | `#3A1D1F` | Wrong-answer background |
| `success` | `#8CF45D` | `#8CF45D` | Correct answers |
| `successContainer` | `#EAFBDD` | `#23351A` | Correct-answer background |
| `warning` | `#8A5A14` | `#F2C14E` | Hints, streaks, timers |
| `warningContainer` | `#FDF0D5` | `#3A2E14` | Hint card |

### Success and warning are not Material slots

Material 3 has no `success` or `warning` role, so they are exposed through a separate
`CbcColors` object provided by `LocalCbcColors`:

```kotlin
MaterialTheme.cbcColors.success
MaterialTheme.cbcColors.onSuccess
MaterialTheme.cbcColors.successContainer
MaterialTheme.cbcColors.onSuccessContainer
MaterialTheme.cbcColors.warning
MaterialTheme.cbcColors.onWarning
MaterialTheme.cbcColors.warningContainer
MaterialTheme.cbcColors.onWarningContainer
```

`success` (`#8CF45D`) is a **fill** colour; put `onSuccess` (`#14320A`) on top of it.
For a correct-answer row, use `successContainer` as the row background and `onSuccessContainer`
for the text, with a check icon — never colour alone.

### Contrast rules

| Pair | Ratio | Verdict |
|---|---|---|
| Primary on light background | 11.8:1 | Pass |
| Primary on dark background | 1.5:1 | **Do not use as text on dark** |
| Destructive on light background | 5.4:1 | Pass |
| Destructive on dark background | 3.4:1 | Large text only — dark mode uses `#FF6B6B` |
| `success` as fill with `onSuccess` text | ~9:1 | Pass |

**Rings:** strokes use mode-specific colours — Math `#362486` / `#A99BF0`, English `#3E8E2A`
/ `#8CF45D`, Science `#8A5A14` / `#F2C14E` (light / dark). The thin stroke needs a darker
green than the `success` fill.

## Typography

ABeeZee, bundled in `res/font/` with its OFL licence at `docs/licenses/abeezee-OFL.txt`.
ABeeZee has only Regular 400 and Italic, so every style is `FontWeight.Normal`; hierarchy
comes from size and colour.

| Style | Material slot | Size | Line height | Use |
|---|---|---|---|---|
| H1 | `displayLarge` | 56sp | 64sp | Onboarding hero only |
| H1 (compact) | `displayMedium` | 44sp | 52sp | Hero on small screens |
| H2 | `displaySmall` | 35sp | 44sp | Screen titles |
| H3 | `headlineMedium` | 27sp | 36sp | Section headers |
| Title | `titleLarge` | 22sp | 28sp | App-bar titles |
| Body | `bodyLarge` | 18sp | 28sp | All prose |
| Body small | `bodyMedium` | 16sp | 24sp | Dense lists |
| Caption | `bodySmall` | 14sp | 20sp | Helper text |
| Label | `labelLarge` | 16sp | 24sp | Buttons, tabs |
| Overline | `labelSmall` | 12sp | 16sp | Badges (1.5sp tracking) |

Sizes are `sp`, never `px`, so they follow the user's font-size preference. Use `titleLarge`
for app bars — 27sp does not fit the standard bar height.

## Shape

One radius everywhere: **30dp** (`AppRadius`). Cards, buttons, inputs, chips and sheets all
share it, so the app reads as a single family. Chips and buttons therefore render as pills.

## Spacing

| Token | Value |
|---|---|
| `Spacing.xs` | 4dp |
| `Spacing.sm` | 8dp |
| `Spacing.md` | 12dp |
| `Spacing.lg` | 16dp (default gutter) |
| `Spacing.xl` | 24dp |
| `Spacing.xxl` | 32dp |
| `Spacing.xxxl` | 48dp |

## Usage

```kotlin
CbcappTheme {
    Surface(color = MaterialTheme.colorScheme.background) {
        Text("Generate a quiz", style = MaterialTheme.typography.displaySmall)
    }
}
```

## Still open

- Launcher icon and app label are still template values.
- Motion timings, component specs (quiz option states, button variants, progress bar) and
  illustration style are not defined yet.
