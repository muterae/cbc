package ke.ac.bics.cbcapp.ui.theme

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Shapes
import androidx.compose.ui.unit.dp

/**
 * The app uses a single rounding radius so every surface, button and input
 * reads as part of the same family.
 */
val AppRadius = 30.dp

val AppShapes = Shapes(
    extraSmall = RoundedCornerShape(AppRadius),
    small = RoundedCornerShape(AppRadius),
    medium = RoundedCornerShape(AppRadius),
    large = RoundedCornerShape(AppRadius),
    extraLarge = RoundedCornerShape(AppRadius)
)
