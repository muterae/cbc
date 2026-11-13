package ke.ac.bics.cbcapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import ke.ac.bics.cbcapp.data.session.SessionManager
import ke.ac.bics.cbcapp.ui.navigation.AppNavHost
import ke.ac.bics.cbcapp.ui.theme.CbcappTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        SessionManager.init(applicationContext)
        enableEdgeToEdge()
        setContent {
            CbcappTheme {
                AppNavHost()
            }
        }
    }
}
