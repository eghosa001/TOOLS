package com.eghosa.tools.readaloud

/** Ads are optional; each video adds time only if the Google rewarded callback fires. */
object RewardPolicy {
    const val MAX_REWARDS_PER_DAY = 3
    const val BONUS_MILLIS = 15L * 60L * 1000L

    fun dailyLimit(rewards: Int): Long =
        BackgroundAllowance.FREE_DAILY_MILLIS +
            rewards.coerceIn(0, MAX_REWARDS_PER_DAY) * BONUS_MILLIS
}
