package com.eghosa.tools.readaloud

import android.content.Context
import android.content.Intent
import androidx.compose.runtime.mutableStateOf
import androidx.core.content.ContextCompat

data class PlaybackStatus(
    val isPlaying: Boolean = false,
    val completed: Int = 0,
    val total: Int = 0,
    val message: String = "Ready to listen.",
    val selectedVoice: String = "System default"
)

/**
 * The playback owner deliberately outlives MainActivity. A foreground media service
 * keeps speech alive while the screen is off, and the Compose UI observes this state.
 */
class PlaybackController private constructor(private val context: Context) {
    private val engine = SpeechEngine(context.applicationContext)
    private val settings = context.getSharedPreferences("readaloud_player", Context.MODE_PRIVATE)
    val state = mutableStateOf(PlaybackStatus(selectedVoice = settings.getString("voice", null) ?: "System default"))
    private var document: String? = null
    private var pieces: List<String> = emptyList()
    private var generation = 0

    fun isReady() = engine.isReady()

    fun offlineVoices(): List<String> = engine.offlineVoices()

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
        refreshVoice()
        if (document != text) {
            document = text
            pieces = TextTools.chunks(text, 900)
            state.value = state.value.copy(completed = 0, total = pieces.size)
        }
        if (pieces.isEmpty()) return
        if (state.value.completed >= pieces.size) state.value = state.value.copy(completed = 0)
        val start = state.value.completed
        generation++
        val token = generation
        state.value = state.value.copy(isPlaying = true, total = pieces.size, message = "Reading aloud")
        val intent = Intent(context, ReadingService::class.java).setAction(ReadingService.ACTION_START)
        try {
            ContextCompat.startForegroundService(context, intent)
        } catch (error: Exception) {
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
                    state.value = state.value.copy(
                        isPlaying = false,
                        completed = if (error == null) 0 else state.value.completed,
                        message = error ?: "Finished reading."
                    )
                    context.stopService(Intent(context, ReadingService::class.java))
                }
            })
    }

    /** Pause without discarding the last completed speech section. */
    fun pause() {
        generation++
        engine.stop()
        state.value = state.value.copy(isPlaying = false, message = "Paused. Resume to continue.")
        context.stopService(Intent(context, ReadingService::class.java))
    }

    fun reset() {
        pause()
        document = null
        pieces = emptyList()
        state.value = state.value.copy(completed = 0, total = 0, message = "Ready to listen.")
    }

    fun stop() = pause()

    suspend fun exportWav(text: String, uri: android.net.Uri, speed: Float,
                          onProgress: (Int, Int) -> Unit) {
        pause()
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
