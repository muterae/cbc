package ke.ac.bics.cbcapp.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.graphics.Color

private val LightColorScheme = lightColorScheme(
    primary = BrandPurple,
    onPrimary = Cream,
    primaryContainer = Color(0xFFE2DDF8),
    onPrimaryContainer = Color(0xFF1B1233),

    secondary = MutedForegroundLight,
    onSecondary = Cream,
    secondaryContainer = MutedLight,
    onSecondaryContainer = Ink,

    tertiary = WarningLight,
    onTertiary = Cream,
    tertiaryContainer = Color(0xFFFDF0D5),
    onTertiaryContainer = Color(0xFF5C3A0A),

    background = Cream,
    onBackground = Ink,

    surface = CardLight,
    onSurface = Ink,
    surfaceVariant = MutedLight,
    onSurfaceVariant = MutedForegroundLight,
    surfaceTint = BrandPurple,
    surfaceContainerLowest = CardLight,
    surfaceContainerLow = CardLight,
    surfaceContainer = CardLight,
    surfaceContainerHigh = MutedLight,
    surfaceContainerHighest = MutedLight,

    outline = BorderLight,
    outlineVariant = Color(0xFFEFEDE5),

    error = DestructiveLight,
    onError = Cream,
    errorContainer = Color(0xFFFBE9E9),
    onErrorContainer = Color(0xFF5A1418)
)

private val DarkColorScheme = darkColorScheme(
    primary = BrandPurple,
    onPrimary = Cream,
    primaryContainer = Color(0xFF2A1C6B),
    onPrimaryContainer = Color(0xFFE2DDF8),

    secondary = MutedForegroundDark,
    onSecondary = Ink,
    secondaryContainer = MutedDark,
    onSecondaryContainer = Cream,

    tertiary = WarningDark,
    onTertiary = Color(0xFF2B1F00),
    tertiaryContainer = Color(0xFF3A2E14),
    onTertiaryContainer = WarningDark,

    background = Ink,
    onBackground = Cream,

    surface = CardDark,
    onSurface = Cream,
    surfaceVariant = MutedDark,
    onSurfaceVariant = MutedForegroundDark,
    surfaceTint = BrandPurple,
    surfaceContainerLowest = CardDark,
    surfaceContainerLow = CardDark,
    surfaceContainer = CardDark,
    surfaceContainerHigh = MutedDark,
    surfaceContainerHighest = MutedDark,

    outline = BorderDark,
    outlineVariant = Color(0xFF26262A),

    error = DestructiveDark,
    onError = Color(0xFF2B0A0B),
    errorContainer = Color(0xFF3A1D1F),
    onErrorContainer = Color(0xFFFFD9D9)
)

@Composable
fun CbcappTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
    val cbcColors = if (darkTheme) DarkCbcColors else LightCbcColors

    CompositionLocalProvider(LocalCbcColors provides cbcColors) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography = AbeeZeeTypography,
            shapes = AppShapes,
            content = content
        )
    }
}
