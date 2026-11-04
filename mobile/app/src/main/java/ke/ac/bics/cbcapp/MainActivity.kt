package ke.ac.bics.cbcapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import ke.ac.bics.cbcapp.ui.navigation.AppNavHost
import ke.ac.bics.cbcapp.ui.theme.CbcappTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            CbcappTheme {
                AppNavHost()
            }
        }
    }
}
