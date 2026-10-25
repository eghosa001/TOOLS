package com.eghosa.tools.readaloud

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
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

/** User-initiated foreground playback with lock screen and notification controls. */
class ReadingService : Service() {
    private lateinit var mediaSession: MediaSession

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
        return START_NOT_STICKY
    }

    fun refresh() {
        if (!::mediaSession.isInitialized) return
        val state = controller().state.value
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
        // Android 13 requires runtime notification permission for explicit updates.
        // The foreground media service itself still works without the grant.
        if (Build.VERSION.SDK_INT < 33 ||
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED) {
            getSystemService(NotificationManager::class.java).notify(NOTIFICATION_ID, notification())
        }
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
            .setContentText("${state.completed} of ${state.total} sections • Reading locally")
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
