package ke.ac.bics.cbcapp.ui.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import ke.ac.bics.cbcapp.data.session.SessionManager
import ke.ac.bics.cbcapp.ui.screens.auth.AuthScreen
import ke.ac.bics.cbcapp.ui.screens.home.HomeScreen
import ke.ac.bics.cbcapp.ui.screens.home.sampleHomeState
import ke.ac.bics.cbcapp.ui.screens.home.toHomeUiState
import ke.ac.bics.cbcapp.ui.screens.placement.PlacementScreen
import ke.ac.bics.cbcapp.ui.screens.play.PlayScreen
import ke.ac.bics.cbcapp.ui.screens.profile.ProfileScreen
import ke.ac.bics.cbcapp.ui.screens.profile.sampleProfileState
import ke.ac.bics.cbcapp.ui.screens.profile.toProfileUiState
import ke.ac.bics.cbcapp.ui.screens.quiz.QuizScreen
import ke.ac.bics.cbcapp.ui.theme.CbcappTheme

@Composable
fun AppNavHost() {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination = navBackStackEntry?.destination
    val currentRoute = currentDestination?.route
    val showBottomBar = mainTabs.any { it.route == currentRoute }

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar {
                    mainTabs.forEach { screen ->
                        NavigationBarItem(
                            icon = { Icon(screen.icon, contentDescription = screen.title) },
                            label = { Text(screen.title) },
                            selected = currentDestination?.hierarchy?.any { it.route == screen.route } == true,
                            onClick = {
                                navController.navigate(screen.route) {
                                    popUpTo(Screen.Home.route) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            }
                        )
                    }
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = Screen.Auth.route,
            modifier = Modifier.padding(innerPadding)
        ) {
            composable(Screen.Auth.route) {
                AuthScreen(
                    onLoggedIn = { profile ->
                        val destination = if (profile.placementCompleted) {
                            Screen.Home
                        } else {
                            Screen.Placement
                        }
                        navController.navigate(destination.route) {
                            popUpTo(Screen.Auth.route) { inclusive = true }
                            launchSingleTop = true
                        }
                    }
                )
            }
            composable(Screen.Placement.route) {
                PlacementScreen(
                    onDone = {
                        navController.navigate(Screen.Home.route) {
                            popUpTo(Screen.Placement.route) { inclusive = true }
                            launchSingleTop = true
                        }
                    }
                )
            }
            composable(Screen.Home.route) {
                HomeScreen(
                    state = SessionManager.profile?.toHomeUiState() ?: sampleHomeState(),
                    onSubjectClick = { navController.navigate(Screen.Quiz.route) }
                )
            }
            composable(Screen.Play.route) {
                PlayScreen(
                    onStartQuiz = { navController.navigate(Screen.Quiz.route) }
                )
            }
            composable(Screen.Profile.route) {
                ProfileScreen(
                    state = SessionManager.profile?.toProfileUiState() ?: sampleProfileState(),
                    onAction = { action ->
                        if (action == "Log out") {
                            SessionManager.clear()
                            navController.navigate(Screen.Auth.route) {
                                popUpTo(Screen.Home.route) { inclusive = true }
                                launchSingleTop = true
                            }
                        }
                    }
                )
            }
            composable(Screen.Quiz.route) {
                QuizScreen(
                    onExit = {
                        navController.navigate(Screen.Home.route) {
                            popUpTo(Screen.Home.route) { inclusive = false }
                            launchSingleTop = true
                        }
                    }
                )
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
fun AppNavHostPreview() {
    CbcappTheme {
        AppNavHost()
    }
}
