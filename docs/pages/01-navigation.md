# Navigation

Single activity, Compose Navigation, bottom bar with three tabs.

| File | Role |
|---|---|
| `MainActivity.kt` | Applies the theme, hosts `AppNavHost` |
| `ui/navigation/Routes.kt` | `Screen` routes + `mainTabs` list |
| `ui/navigation/AppNavHost.kt` | Scaffold, bottom bar, `NavHost` |
| `ui/screens/*` | One package per screen |

Adding a tab: add an entry to `mainTabs` and a `composable` in `AppNavHost`.

Tab switches use `popUpTo(start)` + `saveState`/`restoreState`, so each tab keeps its scroll
position. The login screen will sit outside this tab graph.
