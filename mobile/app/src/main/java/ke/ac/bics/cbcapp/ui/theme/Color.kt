package ke.ac.bics.cbcapp.ui.theme

import androidx.compose.runtime.Immutable
import androidx.compose.runtime.ReadOnlyComposable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// ---------------------------------------------------------------------------
// Raw palette
// ---------------------------------------------------------------------------

val BrandPurple = Color(0xFF362486)
val BrandPurpleLight = Color(0xFFA99BF0)

val Cream = Color(0xFFFFFDF5)
val Ink = Color(0xFF151517)

val CardLight = Color(0xFFFFFFFF)
val CardDark = Color(0xFF1C1C20)

val MutedLight = Color(0xFFEBE9E1)
val MutedDark = Color(0xFF232327)

val MutedForegroundLight = Color(0xFF6B675C)
val MutedForegroundDark = Color(0xFFA5A29A)

val BorderLight = Color(0xFFE4E0D5)
val BorderDark = Color(0xFF2E2E33)

val DestructiveLight = Color(0xFFC9282E)
val DestructiveDark = Color(0xFFFF6B6B)

// Brand "correct" green. It is a fill colour: dark text goes on top of it.
val SuccessGreen = Color(0xFF8CF45D)

// Darker green for thin strokes (rings), where the light green would vanish.
val SuccessGreenStroke = Color(0xFF3E8E2A)

val WarningLight = Color(0xFF8A5A14)
val WarningDark = Color(0xFFF2C14E)

// ---------------------------------------------------------------------------
// Colours outside the Material 3 scheme (success and warning have no slots)
// ---------------------------------------------------------------------------

@Immutable
data class CbcColors(
    val success: Color,
    val onSuccess: Color,
    val successContainer: Color,
    val onSuccessContainer: Color,
    val warning: Color,
    val onWarning: Color,
    val warningContainer: Color,
    val onWarningContainer: Color
)

val LightCbcColors = CbcColors(
    success = SuccessGreen,
    onSuccess = Color(0xFF14320A),
    successContainer = Color(0xFFEAFBDD),
    onSuccessContainer = Color(0xFF1F5A0E),
    warning = WarningLight,
    onWarning = Cream,
    warningContainer = Color(0xFFFDF0D5),
    onWarningContainer = Color(0xFF5C3A0A)
)

val DarkCbcColors = CbcColors(
    success = SuccessGreen,
    onSuccess = Color(0xFF14320A),
    successContainer = Color(0xFF23351A),
    onSuccessContainer = SuccessGreen,
    warning = WarningDark,
    onWarning = Color(0xFF2B1F00),
    warningContainer = Color(0xFF3A2E14),
    onWarningContainer = WarningDark
)

val LocalCbcColors = staticCompositionLocalOf { LightCbcColors }

val MaterialTheme.cbcColors: CbcColors
    @Composable
    @ReadOnlyComposable
    get() = LocalCbcColors.current
