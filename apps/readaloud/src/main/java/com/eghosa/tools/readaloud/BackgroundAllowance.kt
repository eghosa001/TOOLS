package com.eghosa.tools.readaloud

import kotlin.math.max
import kotlin.math.min

/** A deliberately small, deterministic policy that is unit-testable without Android. */
object BackgroundAllowance {
    const val FREE_DAILY_MILLIS: Long = 30L * 60L * 1000L

    fun remaining(consumedMillis: Long, verifiedPremium: Boolean = false): Long =
        if (verifiedPremium) Long.MAX_VALUE
        else (FREE_DAILY_MILLIS - consumedMillis.coerceAtLeast(0L)).coerceAtLeast(0L)

    fun consume(consumedMillis: Long, elapsedMillis: Long, verifiedPremium: Boolean = false): Long {
        if (verifiedPremium) return max(0L, consumedMillis)
        val spent = min(elapsedMillis.coerceAtLeast(0L), remaining(consumedMillis))
        return consumedMillis.coerceAtLeast(0L) + spent
    }
}

/**
 * Uses elapsed realtime to meter actual background playback, not the wall clock.
 * Every state transition settles the previous interval before changing its mode.
 */
class BackgroundTimeMeter(
    private val clockMillis: () -> Long,
    private val consumeElapsed: (Long) -> Long,
    private val remainingMillis: () -> Long
) {
    private var last = clockMillis()
    private var playing = false
    private var background = false

    fun transition(isPlaying: Boolean, inBackground: Boolean): Long {
        settle()
        playing = isPlaying
        background = inBackground
        return remainingMillis()
    }

    fun tick(): Long {
        settle()
        return remainingMillis()
    }

    private fun settle() {
        val now = clockMillis()
        if (playing && background && now > last) consumeElapsed(now - last)
        last = now
    }
}
