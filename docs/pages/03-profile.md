# Profile

Summary card followed by grouped menu lists.

| File | Role |
|---|---|
| `ProfileScreen.kt` | Header, groups, footer |
| `ProfileUiState.kt` | Name, student ID, grade, streak, XP + fake state |
| `components/ProfileHeaderCard.kt` | Avatar initial, details, stat chips |
| `components/SettingsRow.kt` | `SettingsItem`, group card, divider rows |

**Groups:** Account (Edit profile, Log out), Preferences (Daily goal, Notifications,
Appearance), Support (Help & support, About).

**Rules:** dividers between rows; the destructive row uses the error colour, has no chevron
and sits after a divider. Footer shows `Version 1.0`.

**Now:** every row is a placeholder except the visual destructive styling; `onAction` reports
the row label so wiring can be added later. Appearance stays a placeholder until settings
persistence exists.
