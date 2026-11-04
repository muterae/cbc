# 0002 — Android application ID `ke.ac.bics.cbcapp`

## Context

The project was generated from the Android Studio template, which assigns the placeholder
package `com.example.cbc_app`. That identifier appears in four places that must agree:

1. `namespace` in `mobile/app/build.gradle.kts` — where the generated `R` class lives
2. `applicationId` — the identity Android and Google Play use to install and update the app
3. the Kotlin package declaration and imports
4. the source directory path

## Options considered

| Option | Notes |
|---|---|
| Keep `com.example.cbc_app` | Zero work now; rejected by Google Play, and the underscore is unconventional |
| Rename to `ke.ac.bics.cbcapp` | Matches the course (BICS), reverses the domain-style convention correctly, no underscore |

## Decision

`ke.ac.bics.cbcapp`.

`com.example.*` is reserved by Google and blocked from publication. Renaming while the app
had four Kotlin files is a mechanical change; renaming after adding a database, a signing
key, deep links, or a server that trusts a token audience would touch all of them.

## Consequences

- Source files now live under `app/src/main/java/ke/ac/bics/cbcapp/`.
- Builds and unit tests were re-run after the move to confirm nothing referenced the old
  package.
- The launcher label (`cbc-app`) and default icon are still template values; they are
  cosmetic and will be updated during UI polish, not as part of the package rename.
