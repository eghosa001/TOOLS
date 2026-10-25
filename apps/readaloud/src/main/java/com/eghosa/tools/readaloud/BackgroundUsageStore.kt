package com.eghosa.tools.readaloud

import android.content.Context
import java.time.LocalDate

/** Device-local quota. Server-authoritative usage requires a signed-in backend. */
class BackgroundUsageStore(context: Context) {
    private val prefs = context.getSharedPreferences("readaloud_background_allowance", Context.MODE_PRIVATE)

    private fun today(): String = LocalDate.now().toString()

    @Synchronized
    private fun usedForToday(): Long {
        val date = today()
        if (prefs.getString("date", null) != date) {
            prefs.edit().putString("date", date).putLong("used_ms", 0L).commit()
            return 0L
        }
        return prefs.getLong("used_ms", 0L).coerceAtLeast(0L)
    }

    @Synchronized
    fun remainingMillis(): Long = BackgroundAllowance.remaining(usedForToday())

    @Synchronized
    fun consumeElapsed(millis: Long): Long {
        val newUsed = BackgroundAllowance.consume(usedForToday(), millis)
        // Commit, not apply: quota must survive abrupt process termination.
        check(prefs.edit().putLong("used_ms", newUsed).commit()) {
            "Unable to persist background reading allowance"
        }
        return BackgroundAllowance.remaining(newUsed)
    }
}

/** Never unlock paid benefits from user-editable preferences or a raw purchase callback. */
interface PremiumEntitlement {
    fun hasVerifiedSubscription(): Boolean
}

/**
 * Subscription entitlement stays locked until an authenticated Play purchase
 * verification backend is connected. This prevents accidental paid unlocks.
 */
object NoBillingEntitlement : PremiumEntitlement {
    override fun hasVerifiedSubscription() = false
}
