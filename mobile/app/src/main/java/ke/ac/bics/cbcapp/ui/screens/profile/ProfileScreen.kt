package ke.ac.bics.cbcapp.ui.screens.profile

import android.content.res.Configuration
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.HelpOutline
import androidx.compose.material.icons.automirrored.rounded.Logout
import androidx.compose.material.icons.rounded.DarkMode
import androidx.compose.material.icons.rounded.Edit
import androidx.compose.material.icons.rounded.Flag
import androidx.compose.material.icons.rounded.Info
import androidx.compose.material.icons.rounded.Notifications
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import ke.ac.bics.cbcapp.ui.screens.profile.components.ProfileHeaderCard
import ke.ac.bics.cbcapp.ui.screens.profile.components.SettingsGroupCard
import ke.ac.bics.cbcapp.ui.screens.profile.components.SettingsItem
import ke.ac.bics.cbcapp.ui.theme.CbcappTheme
import ke.ac.bics.cbcapp.ui.theme.Spacing

@Composable
fun ProfileScreen(
    state: ProfileUiState = sampleProfileState(),
    onAction: (String) -> Unit = {}
) {
    val accountItems = listOf(
        SettingsItem(icon = Icons.Rounded.Edit, label = "Edit profile"),
    )
    val preferenceItems = listOf(
        SettingsItem(icon = Icons.Rounded.Flag, label = "Daily goal"),
        SettingsItem(icon = Icons.Rounded.Notifications, label = "Notifications"),
        SettingsItem(icon = Icons.Rounded.DarkMode, label = "Appearance")
    )
    val supportItems = listOf(
        SettingsItem(icon = Icons.AutoMirrored.Rounded.HelpOutline, label = "Help & support"),
        SettingsItem(icon = Icons.Rounded.Info, label = "About")
    )
    val destructiveItems = listOf(
        SettingsItem(icon = Icons.AutoMirrored.Rounded.Logout, label = "Log out", destructive = true)
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .verticalScroll(rememberScrollState())
            .padding(Spacing.lg),
        verticalArrangement = Arrangement.spacedBy(Spacing.lg)

    ) {
        Text(
            text = "Profile",
            style = MaterialTheme.typography.displaySmall
        )
        ProfileHeaderCard(state = state)
        SettingsGroupCard(items = accountItems, onItemClick = { onAction(it.label) })
        SettingsGroupCard(items = preferenceItems, onItemClick = { onAction(it.label) })
        SettingsGroupCard(items = supportItems, onItemClick = { onAction(it.label) })
        SettingsGroupCard(items = destructiveItems, onItemClick = { onAction(it.label) })
        Text(
            text = "Version 1.0",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth()
        )
    }
}

@Composable
private fun GroupLabel(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.labelSmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        modifier = Modifier.padding(start = Spacing.xs, top = Spacing.sm)
    )
}


@Preview(showBackground = true)
@Composable
private fun ProfileScreenPreview() {
    CbcappTheme {
        ProfileScreen()
    }
}

@Preview(showBackground = true, uiMode = Configuration.UI_MODE_NIGHT_YES)
@Composable
private fun ProfileScreenDarkPreview() {
    CbcappTheme {
        ProfileScreen()
    }
}
