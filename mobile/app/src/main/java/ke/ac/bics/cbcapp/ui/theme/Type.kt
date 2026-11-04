package ke.ac.bics.cbcapp.ui.theme

import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import ke.ac.bics.cbcapp.R

val AbeeZee = FontFamily(
    Font(R.font.abeezee_regular, FontWeight.Normal, FontStyle.Normal),
    Font(R.font.abeezee_italic, FontWeight.Normal, FontStyle.Italic)
)

/**
 * ABeeZee ships a single weight (400) plus italic, so every style uses
 * [FontWeight.Normal]. Hierarchy comes from size and colour, not weight.
 *
 * Scale: H1 56, H2 35, H3 27, body 18, label 16, caption 14, overline 12.
 */
val AbeeZeeTypography = androidx.compose.material3.Typography(
    displayLarge = TextStyle(
        fontFamily = AbeeZee,
        fontWeight = FontWeight.Normal,
        fontSize = 56.sp,
        lineHeight = 64.sp,
        letterSpacing = (-1.5).sp
    ),
    displayMedium = TextStyle(
        fontFamily = AbeeZee,
        fontWeight = FontWeight.Normal,
        fontSize = 44.sp,
        lineHeight = 52.sp,
        letterSpacing = (-1.0).sp
    ),
    displaySmall = TextStyle(
        fontFamily = AbeeZee,
        fontWeight = FontWeight.Normal,
        fontSize = 35.sp,
        lineHeight = 44.sp,
        letterSpacing = (-0.5).sp
    ),
    headlineLarge = TextStyle(
        fontFamily = AbeeZee,
        fontWeight = FontWeight.Normal,
        fontSize = 32.sp,
        lineHeight = 40.sp,
        letterSpacing = (-0.4).sp
    ),
    headlineMedium = TextStyle(
        fontFamily = AbeeZee,
        fontWeight = FontWeight.Normal,
        fontSize = 27.sp,
        lineHeight = 36.sp,
        letterSpacing = (-0.25).sp
    ),
    headlineSmall = TextStyle(
        fontFamily = AbeeZee,
        fontWeight = FontWeight.Normal,
        fontSize = 24.sp,
        lineHeight = 32.sp
    ),
    titleLarge = TextStyle(
        fontFamily = AbeeZee,
        fontWeight = FontWeight.Normal,
        fontSize = 22.sp,
        lineHeight = 28.sp
    ),
    titleMedium = TextStyle(
        fontFamily = AbeeZee,
        fontWeight = FontWeight.Normal,
        fontSize = 18.sp,
        lineHeight = 26.sp
    ),
    titleSmall = TextStyle(
        fontFamily = AbeeZee,
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 24.sp
    ),
    bodyLarge = TextStyle(
        fontFamily = AbeeZee,
        fontWeight = FontWeight.Normal,
        fontSize = 18.sp,
        lineHeight = 28.sp,
        letterSpacing = 0.15.sp
    ),
    bodyMedium = TextStyle(
        fontFamily = AbeeZee,
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.15.sp
    ),
    bodySmall = TextStyle(
        fontFamily = AbeeZee,
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.25.sp
    ),
    labelLarge = TextStyle(
        fontFamily = AbeeZee,
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.2.sp
    ),
    labelMedium = TextStyle(
        fontFamily = AbeeZee,
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.3.sp
    ),
    labelSmall = TextStyle(
        fontFamily = AbeeZee,
        fontWeight = FontWeight.Normal,
        fontSize = 12.sp,
        lineHeight = 16.sp,
        letterSpacing = 1.5.sp
    )
)
