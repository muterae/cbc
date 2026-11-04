# 0003 — Semantic design tokens instead of ad-hoc colours

## Context

The app started with the Android Studio theme template: purple Material colours, Roboto, and
`dynamicColor = true`. The product needs a fixed brand palette (primary `#362486`, cream
background `#FFFDF5`, muted surface `#EBE9E1`, destructive `#C9282E`, ink `#151517`) and a
single typeface (ABeeZee) with a fixed scale.

Two constraints shaped the implementation:

1. Material 3 has no `success` role. Correct/incorrect feedback is core to a quiz app, so a
   colour outside the scheme is unavoidable.
2. ABeeZee ships one weight (400). Any style requesting Medium/Bold would be synthesised by
   the platform and look inconsistent.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| Inline hex values in each screen | Fastest | Drift, no dark mode, impossible to restyle |
| Only `lightColorScheme` / `darkColorScheme` | Standard, zero extra APIs | No slot for success/warning; screens would hardcode green |
| **Material scheme + `CbcColors` composition local** | Correct/incorrect colours are first-class and themeable | One small custom API to learn |

## Decision

- Map the palette onto `lightColorScheme` / `darkColorScheme`, with dark mode using the same
  brand purple and a lighter destructive red for legibility.
- Expose success and warning through an immutable `CbcColors` class provided by
  `LocalCbcColors`, read as `MaterialTheme.cbcColors`.
- Disable dynamic colour so the brand is not overridden on Android 12+.
- Use one corner radius, 30dp, for every shape.
- Bundle ABeeZee in `res/font` (downloaded fonts depend on Play Services and can fail offline)
  and keep every style at weight 400.

## Consequences

- Screens only reference semantic roles (`colorScheme.primary`, `cbcColors.success`), so a
  redesign touches `ui/theme/` only.
- Quiz feedback is guaranteed to be accessible: `success` is a fill with `onSuccess` on top,
  and correct/incorrect must also be paired with an icon.
- Every text style uses ABeeZee, so no screen can accidentally fall back to Roboto — all 15
  Material slots are defined in `Type.kt`.
- Adding a `bold` label later means adding a second font family, not just a weight.
