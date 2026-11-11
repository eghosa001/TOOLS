package com.eghosa.tools.readaloud

import android.annotation.SuppressLint
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.media.MediaMetadata
import android.media.session.MediaSession
import android.media.session.PlaybackState
import android.os.IBinder
import android.os.Handler
import android.os.Looper

/** User-initiated foreground playback with lock screen and notification controls. */
class ReadingService : Service() {
    private lateinit var mediaSession: MediaSession
    private val handler = Handler(Looper.getMainLooper())
    private val playbackQuotaTicker: Runnable = object : Runnable {
        override fun run() {
            controller().onServiceTick()
            if (controller().state.value.isPlaying) {
                handler.postDelayed(this, 1000L)
            }
        }
    }
    private val releaseWhenPaused = Runnable {
        if (!controller().state.value.isPlaying) stopSelf()
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
        getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "Reading aloud", NotificationManager.IMPORTANCE_LOW)
        )
        mediaSession = MediaSession(this, "ReadAloud").apply {
            setCallback(object : MediaSession.Callback() {
                override fun onPause() = controller().pause()
                override fun onStop() = controller().reset()
                override fun onPlay() = resume()
            })
            isActive = true
        }
    }

    private fun controller() = PlaybackController.get(applicationContext)

    private fun resume() {
        // The Activity supplies the text; a notification must never restart an
        // arbitrary document from an untrusted Intent.
        controller().resume()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_PAUSE -> { controller().pause(); return START_NOT_STICKY }
            ACTION_STOP -> { controller().reset(); return START_NOT_STICKY }
            ACTION_RESUME -> { resume(); return START_NOT_STICKY }
        }
        if (!controller().state.value.isPlaying) { stopSelf(); return START_NOT_STICKY }
        refresh()
        startForeground(NOTIFICATION_ID, notification())
        handler.removeCallbacks(playbackQuotaTicker)
        handler.postDelayed(playbackQuotaTicker, 1000L)
        return START_NOT_STICKY
    }

    // MediaSession/MediaStyle notifications are exempt from POST_NOTIFICATIONS.
    // See Android notification-permission docs, Media sessions exemption.
    @SuppressLint("MissingPermission", "NotificationPermission")
    fun refresh() {
        if (!::mediaSession.isInitialized) return
        val state = controller().state.value
        handler.removeCallbacks(releaseWhenPaused)
        if (!state.isPlaying) handler.postDelayed(releaseWhenPaused, 10 * 60 * 1000L)
        val value = if (state.isPlaying) PlaybackState.STATE_PLAYING else PlaybackState.STATE_PAUSED
        mediaSession.setPlaybackState(
            PlaybackState.Builder().setState(value, state.completed.toLong(), 1f)
                .setActions(PlaybackState.ACTION_PLAY or PlaybackState.ACTION_PAUSE or PlaybackState.ACTION_STOP)
                .build()
        )
        mediaSession.setMetadata(MediaMetadata.Builder()
            .putString(MediaMetadata.METADATA_KEY_TITLE, "ReadAloud")
            .putString(MediaMetadata.METADATA_KEY_ARTIST, "Offline document narration")
            .build())
        getSystemService(NotificationManager::class.java).notify(NOTIFICATION_ID, notification())
    }

    private fun intent(action: String, id: Int): PendingIntent =
        PendingIntent.getService(this, id,
            Intent(this, ReadingService::class.java).setAction(action),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

    private fun notification(): Notification {
        val state = controller().state.value
        val open = PendingIntent.getActivity(this, 0,
            Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val control = if (state.isPlaying) Notification.Action.Builder(
            android.R.drawable.ic_media_pause, "Pause", intent(ACTION_PAUSE, 1)).build()
        else Notification.Action.Builder(
            android.R.drawable.ic_media_play, "Resume", intent(ACTION_RESUME, 2)).build()
        val stop = Notification.Action.Builder(
            android.R.drawable.ic_menu_close_clear_cancel, "Stop", intent(ACTION_STOP, 3)).build()
        return Notification.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setContentTitle("ReadAloud")
            .setContentText(if (state.verifiedPremium) "Premium • Background reading"
                else "${state.completed}/${state.total} sections • " +
                "${(state.freeBackgroundRemainingMillis + 59_999L) / 60_000L}m background left")
            .setContentIntent(open)
            .setOnlyAlertOnce(true)
            .setVisibility(Notification.VISIBILITY_PUBLIC)
            .setOngoing(state.isPlaying)
            .addAction(control)
            .addAction(stop)
            .setStyle(Notification.MediaStyle().setMediaSession(mediaSession.sessionToken)
                .setShowActionsInCompactView(0, 1))
            .build()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        handler.removeCallbacks(releaseWhenPaused)
        handler.removeCallbacks(playbackQuotaTicker)
        if (instance === this) instance = null
        mediaSession.isActive = false
        mediaSession.release()
        super.onDestroy()
    }

    companion object {
        const val ACTION_START = "com.eghosa.tools.readaloud.START"
        const val ACTION_PAUSE = "com.eghosa.tools.readaloud.PAUSE"
        const val ACTION_RESUME = "com.eghosa.tools.readaloud.RESUME"
        const val ACTION_STOP = "com.eghosa.tools.readaloud.STOP"
        private const val CHANNEL_ID = "readaloud_playback"
        private const val NOTIFICATION_ID = 4201
        @Volatile var instance: ReadingService? = null
            private set
    }
}
