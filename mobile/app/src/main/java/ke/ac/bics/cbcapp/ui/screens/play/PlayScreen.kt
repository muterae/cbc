package ke.ac.bics.cbcapp.ui.screens.play

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import ke.ac.bics.cbcapp.ui.theme.CbcappTheme
import ke.ac.bics.cbcapp.ui.theme.Spacing

@Composable
fun PlayScreen(
    onStartQuiz: () -> Unit = {}
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(Spacing.xl),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "Play",
            style = MaterialTheme.typography.displaySmall
        )
        Spacer(modifier = Modifier.height(Spacing.sm))
        Text(
            text = "Generate a quiz and see how you do.",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(Spacing.xl))
        Button(onClick = onStartQuiz) {
            Text("Start quiz")
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun PlayScreenPreview() {
    CbcappTheme {
        PlayScreen()
    }
}
