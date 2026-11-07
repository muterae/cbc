package ke.ac.bics.cbcapp.ui.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.ui.graphics.vector.ImageVector

sealed class Screen(val route: String, val title: String, val icon: ImageVector) {
    data object Home : Screen("home", "Home", Icons.Default.Home)
    data object Play : Screen("play", "Play", Icons.Filled.PlayArrow)
    data object Profile : Screen("profile", "Profile", Icons.Default.Person)
    data object Quiz : Screen("quiz", "Quiz", Icons.Filled.PlayArrow)
}

val mainTabs = listOf(Screen.Home, Screen.Play, Screen.Profile)
