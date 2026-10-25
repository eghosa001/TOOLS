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
            prefs.edit().putString("date", date).putLong("used_ms", 0L)
                .putInt("rewarded_count", 0).commit()
            return 0L
        }
        return prefs.getLong("used_ms", 0L).coerceAtLeast(0L)
    }

    @Synchronized
    fun remainingMillis(): Long =
        (RewardPolicy.dailyLimit(prefs.getInt("rewarded_count", 0)) - usedForToday())
            .coerceAtLeast(0L)

    @Synchronized
    fun rewardsToday(): Int {
        usedForToday()
        return prefs.getInt("rewarded_count", 0).coerceIn(0, RewardPolicy.MAX_REWARDS_PER_DAY)
    }

    @Synchronized
    fun awardBackgroundBonus(): Boolean {
        usedForToday()
        val current = rewardsToday()
        if (current >= RewardPolicy.MAX_REWARDS_PER_DAY) return false
        return prefs.edit().putInt("rewarded_count", current + 1).commit()
    }

    @Synchronized
    fun consumeElapsed(millis: Long): Long {
        val cap = RewardPolicy.dailyLimit(rewardsToday())
        val current = usedForToday()
        val newUsed = (current + millis.coerceAtLeast(0L).coerceAtMost(cap - current))
            .coerceIn(0L, cap)
        // Asynchronous persistence avoids a blocking disk fsync every playback second.
        // Android flushes pending SharedPreferences writes at lifecycle boundaries.
        prefs.edit().putLong("used_ms", newUsed).apply()
        return (cap - newUsed).coerceAtLeast(0L)
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

/** In-memory, short-lived access. Never read paid status from local user preferences. */
object VerifiedPlayEntitlement : PremiumEntitlement {
    @Volatile private var validUntilElapsedMs: Long = 0L
    override fun hasVerifiedSubscription(): Boolean =
        android.os.SystemClock.elapsedRealtime() < validUntilElapsedMs

    fun setVerifiedFor(seconds: Long) {
        validUntilElapsedMs = android.os.SystemClock.elapsedRealtime() +
            seconds.coerceIn(0L, 6L * 60L * 60L) * 1000L
    }

    fun revoke() { validUntilElapsedMs = 0L }
}
