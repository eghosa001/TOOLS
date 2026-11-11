package com.eghosa.tools.readaloud

import android.content.Context
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import java.io.File
import java.util.Locale
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicInteger
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

data class InstalledTtsEngine(val label: String, val packageName: String)

class SpeechEngine(private val context: Context, private val requestedEngine: String? = null) {
    private val handler = Handler(Looper.getMainLooper())
    private val callbacks = ConcurrentHashMap<String, (Boolean) -> Unit>()
    private val rangeCallbacks = ConcurrentHashMap<String, (Int, Int) -> Unit>()
    private val session = AtomicInteger()
    @Volatile private var ready = false
    private var speech: TextToSpeech? = null

    init {
        val onInitialized = TextToSpeech.OnInitListener { result ->
            ready = result == TextToSpeech.SUCCESS
            if (ready) speech?.language = Locale.getDefault()
        }
        speech = if (requestedEngine.isNullOrBlank()) TextToSpeech(context.applicationContext, onInitialized)
                 else TextToSpeech(context.applicationContext, onInitialized, requestedEngine)
        speech?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) = Unit
            override fun onDone(utteranceId: String?) {
                utteranceId?.let { rangeCallbacks.remove(it); callbacks.remove(it)?.invoke(true) }
            }
            override fun onRangeStart(utteranceId: String?, start: Int, end: Int, frame: Int) {
                utteranceId?.let { rangeCallbacks[it]?.invoke(start, end) }
            }
            @Deprecated("Java override")
            override fun onError(utteranceId: String?) {
                utteranceId?.let { rangeCallbacks.remove(it); callbacks.remove(it)?.invoke(false) }
            }
            override fun onError(utteranceId: String?, errorCode: Int) = onError(utteranceId)
        })
    }

    fun isReady(): Boolean = ready
    fun installedEngines(): List<InstalledTtsEngine> = speech?.engines.orEmpty()
        .map { InstalledTtsEngine(it.label ?: it.name, it.name) }
        .sortedBy { it.label.lowercase() }
    fun offlineVoices(): List<String> =
        if (!ready) emptyList() else speech?.voices.orEmpty()
            .filter { !it.isNetworkConnectionRequired }
            .map { it.name }.sorted()

    fun voiceDescription(name: String): String {
        val voice = speech?.voices?.firstOrNull { it.name == name } ?: return "Offline voice"
        return voice.locale.getDisplayName(Locale.getDefault()) +
            if (voice.quality >= android.speech.tts.Voice.QUALITY_HIGH)
                " · Higher quality" else " · Offline"
    }

    fun setVoice(name: String): Boolean {
        if (!ready) return false
        val voice = speech?.voices?.firstOrNull { it.name == name && !it.isNetworkConnectionRequired } ?: return false
        return speech?.setVoice(voice) == TextToSpeech.SUCCESS
    }

    fun stop() {
        session.incrementAndGet()
        speech?.stop()
        callbacks.clear()
        rangeCallbacks.clear()
    }

    fun speak(text: String, speed: Float, onProgress: (Int, Int) -> Unit, onFinished: (String?) -> Unit) =
        speakChunks(TextTools.chunks(text, 900), speed, onProgress, onFinished)

    /** Preserve exact segment boundaries across pause/resume; do not re-chunk suffixes. */
    fun speakChunks(chunks: List<String>, speed: Float,
                    onProgress: (Int, Int) -> Unit, onFinished: (String?) -> Unit,
                    onRange: (Int, Int, Int) -> Unit = { _, _, _ -> }) {
        if (!ready) { onFinished("Speech engine is not ready. Check Android text-to-speech settings."); return }
        stop()
        speech?.setSpeechRate(speed)
        if (chunks.isEmpty()) { onFinished("Enter some text first."); return }
        val token = session.get()
        fun next(index: Int) {
            if (session.get() != token) return
            if (index == chunks.size) { onFinished(null); return }
            val id = UUID.randomUUID().toString()
            rangeCallbacks[id] = { begin, end ->
                handler.post {
                    if (session.get() == token) onRange(index, begin, end)
                }
            }
            callbacks[id] = { success ->
                handler.post {
                    if (session.get() != token) return@post
                    if (success) { onProgress(index + 1, chunks.size); next(index + 1) }
                    else onFinished("Speech synthesis failed for this voice.")
                }
            }
            if (speech?.speak(chunks[index], TextToSpeech.QUEUE_FLUSH, Bundle(), id) != TextToSpeech.SUCCESS) {
                callbacks.remove(id)
                rangeCallbacks.remove(id)
                onFinished("The selected voice could not speak.")
            }
        }
        next(0)
    }

    suspend fun exportWav(text: String, uri: Uri, speed: Float, onProgress: (Int, Int) -> Unit) {
        require(ready) { "Speech engine is not ready" }
        stop()
        val parts = TextTools.chunks(text, 1800)
        require(parts.isNotEmpty()) { "No text to export" }
        val directory = File(context.cacheDir, "wav-" + UUID.randomUUID()).also { it.mkdirs() }
        try {
            speech?.setSpeechRate(speed)
            val files = mutableListOf<File>()
            for ((index, chunk) in parts.withIndex()) {
                val file = File(directory, "part-" + index + ".wav")
                withTimeout(90_000L) { synthesize(chunk, file) }
                files.add(file)
                onProgress(index + 1, parts.size)
            }
            withContext(Dispatchers.IO) {
                context.contentResolver.openOutputStream(uri, "w")?.use { output ->
                    WavMerger.merge(files, output)
                } ?: error("Could not open the selected destination")
            }
        } finally { directory.deleteRecursively() }
    }

    private suspend fun synthesize(text: String, destination: File): Unit =
        suspendCancellableCoroutine { continuation ->
            val id = UUID.randomUUID().toString()
            callbacks[id] = { ok ->
                if (continuation.isActive) {
                    if (ok && destination.length() > 44) continuation.resume(Unit)
                    else continuation.resumeWithException(IllegalStateException("Selected TTS voice could not export audio"))
                }
            }
            continuation.invokeOnCancellation { callbacks.remove(id); speech?.stop() }
            handler.post {
                if (!continuation.isActive) return@post
                if (speech?.synthesizeToFile(text, Bundle(), destination, id) != TextToSpeech.SUCCESS) {
                    callbacks.remove(id)
                    if (continuation.isActive) continuation.resumeWithException(IllegalStateException("Unable to start audio export"))
                }
            }
        }

    fun shutdown() { stop(); speech?.shutdown(); speech = null; ready = false }
}
