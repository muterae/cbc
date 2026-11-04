# Home (landing)

First screen after login. Order: greeting → today's progress → subjects → leaderboard.

| File | Role |
|---|---|
| `HomeScreen.kt` | LazyColumn layout, ring section |
| `HomeUiState.kt` | `SubjectProgress`, `LeaderboardEntry`, fake `sampleHomeState()` |
| `components/ProgressRing.kt` | Canvas ring |
| `components/SubjectCard.kt` | Primary card with icon, title, description |
| `components/LeaderboardCard.kt` | Ranked list, current user highlighted |

**Rings:** one per subject. One answered question = 20% of the 5-question daily goal.
Progress is capped at 100% and shows a check instead of a percentage.
Ring colours: Math purple, English green, Science amber.

**Data:** all values come from `HomeUiState`; the screen is stateless and has a fake state
until the server is connected. Subject taps currently do nothing.

**Copy:** subject cards use the primary colour with cream text; the leaderboard sits on the
surface colour.
