package com.eghosa.tools.readaloud

import android.content.Context
import android.content.Intent
import android.os.SystemClock
import androidx.compose.runtime.mutableStateOf
import androidx.core.content.ContextCompat

data class PlaybackStatus(
    val isPlaying: Boolean = false,
    val completed: Int = 0,
    val total: Int = 0,
    val message: String = "Ready to listen.",
    val selectedVoice: String = "System default",
    val freeBackgroundRemainingMillis: Long = BackgroundAllowance.FREE_DAILY_MILLIS,
    val verifiedPremium: Boolean = false
)

/**
 * The playback owner deliberately outlives MainActivity. A foreground media service
 * keeps speech alive while the screen is off, and the Compose UI observes this state.
 */
class PlaybackController private constructor(private val context: Context) {
    private val settings = context.getSharedPreferences("readaloud_player", Context.MODE_PRIVATE)
    private var engine = SpeechEngine(context.applicationContext, settings.getString("engine", null))
    val state = mutableStateOf(PlaybackStatus(selectedVoice = settings.getString("voice", null) ?: "System default"))
    private var document: String? = null
    private var pieces: List<String> = emptyList()
    private var generation = 0
    private var lastRate = 1f
    private val allowance = BackgroundUsageStore(context)
    private val entitlement: PremiumEntitlement = NoBillingEntitlement
    private var activityVisible = true
    private val backgroundMeter = BackgroundTimeMeter(
        clockMillis = { SystemClock.elapsedRealtime() },
        consumeElapsed = { elapsed ->
            if (entitlement.hasVerifiedSubscription()) Long.MAX_VALUE
            else allowance.consumeElapsed(elapsed)
        },
        remainingMillis = { remainingBackgroundTime() }
    )

    private fun remainingBackgroundTime(): Long =
        if (entitlement.hasVerifiedSubscription()) Long.MAX_VALUE else allowance.remainingMillis()

    fun onActivityVisibility(visible: Boolean) {
        settleTime()
        activityVisible = visible
        val remaining = backgroundMeter.transition(state.value.isPlaying, !activityVisible)
        updateAllowance(remaining)
        enforceBackgroundLimit(remaining)
    }

    private fun updateAllowance(remaining: Long = remainingBackgroundTime()) {
        state.value = state.value.copy(
            freeBackgroundRemainingMillis = remaining,
            verifiedPremium = entitlement.hasVerifiedSubscription()
        )
    }

    private fun settleTime(): Long = backgroundMeter.tick()

    fun onServiceTick() {
        if (!state.value.isPlaying) return
        val remaining = settleTime()
        updateAllowance(remaining)
        enforceBackgroundLimit(remaining)
    }

    private fun enforceBackgroundLimit(remaining: Long) {
        if (!activityVisible && state.value.isPlaying &&
            !entitlement.hasVerifiedSubscription() && remaining <= 0L) {
            pauseForFreeLimit()
        }
    }

    private fun pauseForFreeLimit() {
        generation++
        backgroundMeter.transition(false, !activityVisible)
        engine.stop()
        state.value = state.value.copy(
            isPlaying = false,
            freeBackgroundRemainingMillis = 0L,
            message = "Today's 30-minute free background allowance is used. Open ReadAloud to continue listening."
        )
        ReadingService.instance?.refresh()
    }

    fun isReady() = engine.isReady()

    fun offlineVoices(): List<String> = engine.offlineVoices()

    fun installedEngines(): List<InstalledTtsEngine> = engine.installedEngines()

    fun selectedEngine(): String = settings.getString("engine", null) ?: "System default"

    fun selectEngine(packageName: String?) {
        pause()
        context.stopService(Intent(context, ReadingService::class.java))
        engine.shutdown()
        settings.edit().apply {
            if (packageName == null) remove("engine") else putString("engine", packageName)
            remove("voice")
        }.apply()
        engine = SpeechEngine(context.applicationContext, packageName)
        state.value = state.value.copy(selectedVoice = "System default",
            message = "Speech engine changed. Voices will load shortly.")
    }

    fun chooseVoice(name: String): Boolean {
        if (!engine.setVoice(name)) return false
        settings.edit().putString("voice", name).apply()
        state.value = state.value.copy(selectedVoice = name, message = "Offline voice selected.")
        return true
    }

    fun refreshVoice() {
        val saved = settings.getString("voice", null) ?: return
        if (engine.isReady() && state.value.selectedVoice != saved) chooseVoice(saved)
        else if (engine.isReady()) engine.setVoice(saved)
    }

    fun play(text: String, speed: Float) {
        if (text.isBlank()) {
            state.value = state.value.copy(message = "Enter or import some text.")
            return
        }
        if (!engine.isReady()) {
            state.value = state.value.copy(message = "Speech engine is initializing. Retry shortly.")
            return
        }
        val remaining = settleTime()
        updateAllowance(remaining)
        if (!activityVisible && !entitlement.hasVerifiedSubscription() && remaining <= 0L) {
            state.value = state.value.copy(message =
                "Free background time is used for today. Open ReadAloud to continue reading.")
            return
        }
        refreshVoice()
        if (document != text) {
            document = text
            pieces = TextTools.chunks(text, 900)
            state.value = state.value.copy(completed = 0, total = pieces.size)
        }
        if (pieces.isEmpty()) return
        if (state.value.completed >= pieces.size) state.value = state.value.copy(completed = 0)
        lastRate = speed
        val start = state.value.completed
        generation++
        val token = generation
        state.value = state.value.copy(isPlaying = true, total = pieces.size, message = "Reading aloud")
        backgroundMeter.transition(true, !activityVisible)
        val intent = Intent(context, ReadingService::class.java).setAction(ReadingService.ACTION_START)
        try {
            ContextCompat.startForegroundService(context, intent)
        } catch (error: Exception) {
            backgroundMeter.transition(false, !activityVisible)
            state.value = state.value.copy(isPlaying = false,
                message = "Background playback unavailable: " + (error.message ?: "service could not start"))
            return
        }
        engine.speakChunks(pieces.drop(start), speed,
            { done, _ ->
                if (token == generation) {
                    state.value = state.value.copy(completed = start + done, total = pieces.size)
                    ReadingService.instance?.refresh()
                }
            },
            { error ->
                if (token == generation) {
                    val remainingAfterSpeech = backgroundMeter.transition(false, !activityVisible)
                    state.value = state.value.copy(
                        freeBackgroundRemainingMillis = remainingAfterSpeech,
                        isPlaying = false,
                        completed = if (error == null) 0 else state.value.completed,
                        message = error ?: "Finished reading."
                    )
                    context.stopService(Intent(context, ReadingService::class.java))
                }
            })
    }

    fun resume() {
        val text = document ?: return
        if (!state.value.isPlaying) play(text, lastRate)
    }

    /** Pause without discarding the last completed speech section. */
    fun pause() {
        generation++
        val remaining = backgroundMeter.transition(false, !activityVisible)
        engine.stop()
        state.value = state.value.copy(isPlaying = false,
            freeBackgroundRemainingMillis = remaining,
            message = "Paused. Resume to continue.")
        // Keep the media notification visible so a user can resume from the lock screen.
        ReadingService.instance?.refresh()
    }

    fun reset() {
        pause()
        document = null
        pieces = emptyList()
        state.value = state.value.copy(completed = 0, total = 0, message = "Ready to listen.")
        context.stopService(Intent(context, ReadingService::class.java))
    }

    fun stop() = pause()

    suspend fun exportWav(text: String, uri: android.net.Uri, speed: Float,
                          onProgress: (Int, Int) -> Unit) {
        pause()
        context.stopService(Intent(context, ReadingService::class.java))
        engine.exportWav(text, uri, speed, onProgress)
    }

    companion object {
        @Volatile private var instance: PlaybackController? = null
        fun get(context: Context): PlaybackController =
            instance ?: synchronized(this) {
                instance ?: PlaybackController(context.applicationContext).also { instance = it }
            }
    }
}
