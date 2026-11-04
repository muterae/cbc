package ke.ac.bics.cbcapp.ui.screens.profile

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import ke.ac.bics.cbcapp.ui.theme.CbcappTheme

@Composable
fun ProfileScreen() {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(text = "Profile", style = MaterialTheme.typography.displaySmall)
    }
}

@Preview(showBackground = true)
@Composable
private fun ProfileScreenPreview() {
    CbcappTheme {
        ProfileScreen()
    }
}
