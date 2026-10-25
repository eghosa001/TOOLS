package com.eghosa.tools.readaloud

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class BackgroundAllowanceTest {
    @Test fun backgroundTimeStopsAtThirtyMinutes() {
        val maximum = BackgroundAllowance.FREE_DAILY_MILLIS
        assertEquals(0L, BackgroundAllowance.remaining(maximum))
        assertEquals(maximum, BackgroundAllowance.consume(maximum - 2000L, 9000L))
        assertEquals(0L, BackgroundAllowance.remaining(maximum + 3000L))
    }

    @Test fun premiumPlanDoesNotConsumeFreeAllowance() {
        assertEquals(5000L, BackgroundAllowance.consume(5000L, 7000000L, verifiedPremium = true))
        assertEquals(Long.MAX_VALUE, BackgroundAllowance.remaining(5000L, verifiedPremium = true))
    }

    @Test fun onlyActiveBackgroundIntervalsCount() {
        var clock = 0L
        var usage = 0L
        val meter = BackgroundTimeMeter(
            clockMillis = { clock },
            consumeElapsed = { elapsed ->
                usage = BackgroundAllowance.consume(usage, elapsed)
                BackgroundAllowance.remaining(usage)
            },
            remainingMillis = { BackgroundAllowance.remaining(usage) }
        )
        meter.transition(isPlaying = true, inBackground = false)
        clock = 40_000L
        meter.tick()
        assertEquals(0L, usage)

        meter.transition(isPlaying = true, inBackground = true)
        clock = 100_000L
        meter.tick()
        assertEquals(60_000L, usage)

        meter.transition(isPlaying = false, inBackground = true)
        clock = 180_000L
        meter.tick()
        assertEquals(60_000L, usage)

        meter.transition(isPlaying = true, inBackground = true)
        clock = 2_000_000L
        assertEquals(0L, meter.tick())
        assertEquals(BackgroundAllowance.FREE_DAILY_MILLIS, usage)
        assertTrue(meter.tick() <= 0L)
    }

    @Test fun repeatedPauseResumeDoesNotAccrueForegroundTime() {
        var now = 0L
        var used = 0L
        val meter = BackgroundTimeMeter(
            { now },
            { elapsed ->
                used = BackgroundAllowance.consume(used, elapsed)
                BackgroundAllowance.remaining(used)
            },
            { BackgroundAllowance.remaining(used) }
        )
        repeat(100) {
            meter.transition(true, false)
            now += 5000L
            meter.transition(true, true)
            now += 1000L
            meter.transition(false, true)
            now += 10000L
        }
        assertEquals(100_000L, used)
    }

    @Test fun exactQuotaBoundaryAndOverrunAreClamped() {
        val max = BackgroundAllowance.FREE_DAILY_MILLIS
        assertEquals(max, BackgroundAllowance.consume(0L, max))
        assertEquals(max, BackgroundAllowance.consume(max - 1, 5000L))
        assertEquals(0L, BackgroundAllowance.remaining(max))
        assertEquals(0L, BackgroundAllowance.remaining(Long.MAX_VALUE))
        assertEquals(max, BackgroundAllowance.remaining(-123L))
    }

    @Test fun negativeAndDuplicateTicksCannotIncreaseAllowance() {
        var now = 1000L
        var spent = 0L
        val meter = BackgroundTimeMeter(
            { now },
            { elapsed ->
                spent = BackgroundAllowance.consume(spent, elapsed)
                BackgroundAllowance.remaining(spent)
            },
            { BackgroundAllowance.remaining(spent) }
        )
        meter.transition(true, true)
        now = 7000L
        meter.tick()
        meter.tick()
        assertEquals(6000L, spent)
        now = 3000L
        meter.tick()
        assertEquals(6000L, spent)
    }
}
