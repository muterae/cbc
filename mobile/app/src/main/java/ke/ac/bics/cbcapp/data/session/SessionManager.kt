package ke.ac.bics.cbcapp.data.session

import android.content.Context
import android.content.SharedPreferences
import ke.ac.bics.cbcapp.data.api.StudentProfileDto

object SessionManager {
    private const val PREFS_NAME = "cbc_session"
    private const val KEY_STUDENT_ID = "student_id"
    private const val KEY_STUDENT_NAME = "student_name"

    private var prefs: SharedPreferences? = null

    var profile: StudentProfileDto? = null
        private set
    var studentId: String? = null
        private set
    var studentName: String? = null
        private set

    fun init(context: Context) {
        if (prefs != null) return
        val store = context.applicationContext.getSharedPreferences(
            PREFS_NAME,
            Context.MODE_PRIVATE
        )
        prefs = store
        studentId = store.getString(KEY_STUDENT_ID, null)
        studentName = store.getString(KEY_STUDENT_NAME, null)
    }

    fun save(profile: StudentProfileDto) {
        this.profile = profile
        studentId = profile.studentId
        studentName = profile.name
        prefs?.edit()
            ?.putString(KEY_STUDENT_ID, profile.studentId)
            ?.putString(KEY_STUDENT_NAME, profile.name)
            ?.apply()
    }

    fun clear() {
        profile = null
        studentId = null
        studentName = null
        prefs?.edit()?.clear()?.apply()
    }
}
