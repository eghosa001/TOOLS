package com.eghosa.tools.readaloud

import android.os.Bundle
import android.content.Intent
import android.net.Uri
import android.os.Handler
import android.os.Looper
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.math.roundToInt

private val ReadAloudLightScheme = lightColorScheme(
    primary = Color(0xFF2549CC),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFDDE6FF),
    onPrimaryContainer = Color(0xFF152D70),
    secondary = Color(0xFF51617F),
    background = Color(0xFFF7F9FD),
    surface = Color(0xFFFFFFFF),
    surfaceVariant = Color(0xFFEAF0FA),
    onSurfaceVariant = Color(0xFF45536F)
)

private val ReadAloudDarkScheme = darkColorScheme(
    primary = Color(0xFFAFC4FF),
    onPrimary = Color(0xFF0B256D),
    primaryContainer = Color(0xFF263F89),
    onPrimaryContainer = Color(0xFFDDE6FF),
    secondary = Color(0xFFACBFE0),
    background = Color(0xFF0D1424),
    surface = Color(0xFF162139),
    surfaceVariant = Color(0xFF253249),
    onSurfaceVariant = Color(0xFFC0CEE5)
)

class MainActivity : ComponentActivity() {
    private lateinit var controller: PlaybackController
    private lateinit var store: DocumentStore
    private lateinit var importer: DocumentReader
    private lateinit var advertising: ReadAloudAds
    private lateinit var billing: ReadAloudBilling

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        controller = PlaybackController.get(applicationContext)
        store = DocumentStore(this)
        importer = DocumentReader(this)
        advertising = ReadAloudAds(this)
        billing = ReadAloudBilling(this, controller)
        advertising.requestConsent()
        billing.start()
        setContent {
            MaterialTheme(colorScheme = if (isSystemInDarkTheme()) ReadAloudDarkScheme else ReadAloudLightScheme) {
                ReadAloudApp(controller, store, importer, advertising, billing)
            }
        }
    }

    override fun onStart() {
        super.onStart()
        controller.onActivityVisibility(true)
        if (::billing.isInitialized) billing.restorePurchases()
    }

    override fun onDestroy() {
        if (::billing.isInitialized) billing.close()
        super.onDestroy()
    }

    override fun onStop() {
        controller.onActivityVisibility(false)
        super.onStop()
    }
}

@Composable
private fun ReadAloudApp(controller: PlaybackController, store: DocumentStore,
                         importer: DocumentReader, advertising: ReadAloudAds,
                         billing: ReadAloudBilling) {
    val scope = rememberCoroutineScope()
    val appContext = LocalContext.current
    val mainHandler = remember { Handler(Looper.getMainLooper()) }
    var screen by remember { mutableIntStateOf(0) }
    var typedText by remember { mutableStateOf("") }
    var selectedText by remember { mutableStateOf<String?>(null) }
    var selectedTitle by remember { mutableStateOf<String?>(null) }
    var selectedId by remember { mutableStateOf<String?>(null) }
    var library by remember { mutableStateOf(store.list()) }
    var busy by remember { mutableStateOf(false) }
    var progress by remember { mutableIntStateOf(0) }
    var progressMax by remember { mutableIntStateOf(0) }
    var rate by remember { mutableFloatStateOf(1f) }
    val readerPreferences = remember { appContext.getSharedPreferences("readaloud_display", android.content.Context.MODE_PRIVATE) }
    var readingFontScale by remember {
        mutableFloatStateOf(readerPreferences.getFloat("font_scale", 1f).coerceIn(0.85f, 1.65f))
    }
    var notice by remember { mutableStateOf("Offline speech uses the voice installed on your phone.") }
    var voices by remember { mutableStateOf(emptyList<String>()) }
    var currentVoice by remember { mutableStateOf("System default") }
    val playbackStatus = controller.state.value
    val activeText = selectedText ?: typedText
    val words = remember(activeText) { TextTools.wordCount(activeText) }

    fun stop() {
        controller.pause()
        notice = "Paused. Resume at the last completed section."
    }

    fun listen() {
        if (busy) return
        controller.play(activeText, rate, selectedId)
        notice = controller.state.value.message
    }

    val picker = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) scope.launch {
            stop()
            busy = true
            notice = "Reading document…"
            try {
                val extracted = importer.extract(uri) { done, total ->
                    mainHandler.post { progress = done; progressMax = total }
                }
                val item = withContext(Dispatchers.IO) { store.save(extracted.title, extracted.text) }
                library = store.list()
                selectedText = extracted.text
                selectedTitle = extracted.title
                selectedId = item.id
                controller.reset()
                screen = 0
                notice = if (extracted.pages > 0) {
                    "Imported " + extracted.pages + " pages; OCR used on " + extracted.ocrPages + " pages."
                } else "Document imported successfully."
            } catch (e: Exception) {
                notice = e.message ?: "Unable to read this document"
            } finally { busy = false; progress = 0; progressMax = 0 }
        }
    }

    val exporter = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("audio/wav")
    ) { uri ->
        if (uri != null) scope.launch {
            stop()
            busy = true
            notice = "Generating WAV audio on this device…"
            try {
                controller.exportWav(activeText, uri, rate) { done, total ->
                    mainHandler.post { progress = done; progressMax = total }
                }
                notice = "WAV audio saved successfully."
            } catch (e: Exception) {
                notice = "Export failed: " + (e.message ?: "Audio format unavailable")
            } finally { busy = false; progress = 0; progressMax = 0 }
        }
    }

    Scaffold(
        bottomBar = {
            Column {
                if (screen == 1 && !playbackStatus.isPlaying &&
                    !playbackStatus.verifiedPremium && advertising.canRequestAds.value) {
                    ReadAloudBanner(advertising)
                }
                NavigationBar {
                val titles = listOf("Read", "Library", "Voices", "Settings")
                val symbols = listOf("▶", "▤", "♫", "⚙")
                titles.forEachIndexed { i, title ->
                    NavigationBarItem(
                        selected = screen == i,
                        onClick = { screen = i; if (i == 2) { controller.refreshVoice(); voices = controller.offlineVoices() } },
                        icon = { Text(symbols[i]) },
                        label = { Text(title) }
                    )
                }
                }
            }
        }
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            Column(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 12.dp)) {
                Text("ReadAloud", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
                Text("Read and listen, right on your phone", style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            when (screen) {
                0 -> Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(horizontal = 20.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)) {
                    Card(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            Text("Your document", fontWeight = FontWeight.SemiBold)
                            if (selectedText == null) {
                                OutlinedTextField(
                                    value = typedText,
                                    onValueChange = {
                                        typedText = it
                                        selectedId = null
                                        controller.reset()
                                    },
                                    label = { Text("Type or paste text") },
                                    placeholder = { Text("Paste an article, chapter or message here…") },
                                    minLines = 6, maxLines = 12,
                                    modifier = Modifier.fillMaxWidth()
                                )
                            } else {
                                Text(selectedTitle ?: "Document", style = MaterialTheme.typography.titleMedium)
                                Text(selectedText?.take(1500).orEmpty(), maxLines = 12, overflow = TextOverflow.Ellipsis)
                                OutlinedButton(onClick = {
                                    stop()
                                    typedText = selectedText.orEmpty()
                                    selectedText = null; selectedTitle = null; selectedId = null
                                    controller.reset()
                                }) { Text("Edit extracted text") }
                            }
                            Text(words.toString() + " words", style = MaterialTheme.typography.labelMedium)
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                OutlinedButton(onClick = {
                                    if (!busy) picker.launch(arrayOf("application/pdf",
                                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                        "text/plain", "text/markdown", "application/epub+zip"))
                                }, enabled = !busy) { Text("Import file") }
                                OutlinedButton(onClick = {
                                    if (activeText.isNotBlank()) scope.launch {
                                        try {
                                            val item = withContext(Dispatchers.IO) {
                                                store.save(selectedTitle ?: "Saved text", activeText)
                                            }
                                            library = store.list()
                                            selectedId = item.id
                                            notice = "Saved in your library"
                                        } catch (e: Exception) { notice = e.message ?: "Save failed" }
                                    }
                                }, enabled = !busy && words > 0) { Text("Save") }
                            }
                        }
                    }
                    Card(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                            Text("Playback", style = MaterialTheme.typography.titleMedium)
                            Text(if (playbackStatus.verifiedPremium) "Premium: unlimited background listening"
                            else "Free background time remaining today: " +
                                ((playbackStatus.freeBackgroundRemainingMillis + 59_999L) / 60_000L).toString() +
                                " of 30 minutes")
                            Text("Reading with ReadAloud open remains free. Only playback while the app is in the background uses this allowance.",
                                style = MaterialTheme.typography.bodySmall)
                            if (!playbackStatus.verifiedPremium &&
                                playbackStatus.freeBackgroundRemainingMillis <= 10 * 60_000L &&
                                controller.canEarnBackgroundBonus()) {
                                OutlinedButton(onClick = {
                                    controller.pause()
                                    advertising.showRewarded { controller.awardBackgroundBonus() }
                                }, enabled = !busy && advertising.rewardReady.value) {
                                    Text(if (advertising.rewardReady.value)
                                        "Watch ad for +15 background minutes" else
                                        "Optional reward video loading")
                                }
                            }
                            Text("Speed: " + ((rate * 100).roundToInt()) + "%")
                            Slider(value = rate, onValueChange = { rate = it }, valueRange = 0.5f..2.5f)
                            if (playbackStatus.total > 0) {
                                Text("Read " + playbackStatus.completed + " of " + playbackStatus.total + " sections")
                                val section = playbackStatus.currentSectionText
                                if (section.isNotBlank()) {
                                    Text("Follow along", style = MaterialTheme.typography.titleSmall)
                                    val selectedStart = playbackStatus.highlightStart.coerceIn(0, section.length)
                                    val selectedEnd = playbackStatus.highlightEnd.coerceIn(selectedStart, section.length)
                                    // Keep the spoken words inside the visible window even for long sections.
                                    val viewStart = if (selectedStart > 180) selectedStart - 160 else 0
                                    val viewEnd = minOf(section.length,
                                        maxOf(viewStart + 420, selectedEnd + 160))
                                    val excerpt = section.substring(viewStart, viewEnd)
                                    val rich = buildAnnotatedString {
                                        if (viewStart > 0) append("… ")
                                        val offset = length
                                        append(excerpt)
                                        if (selectedEnd > selectedStart) {
                                            addStyle(SpanStyle(
                                                background = MaterialTheme.colorScheme.primaryContainer,
                                                color = MaterialTheme.colorScheme.onPrimaryContainer
                                            ), offset + selectedStart - viewStart,
                                                offset + selectedEnd - viewStart)
                                        }
                                        if (viewEnd < section.length) append(" …")
                                    }
                                    Text(rich,
                                        fontSize = (18f * readingFontScale).sp,
                                        lineHeight = (27f * readingFontScale).sp,
                                        maxLines = 15, overflow = TextOverflow.Ellipsis)
                                }
                            }
                            if (progressMax > 0 && busy) Text("Processed " + progress + " of " + progressMax + " sections")
                            if (playbackStatus.total > 0) {
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    OutlinedButton(onClick = { controller.skipSection(-1) },
                                        enabled = !busy && playbackStatus.completed > 0) { Text("Previous") }
                                    OutlinedButton(onClick = { controller.skipSection(1) },
                                        enabled = !busy && playbackStatus.completed < playbackStatus.total - 1) { Text("Next") }
                                }
                            }
                            Text("Reading text size: " + (readingFontScale * 100f).roundToInt() + "%")
                            Slider(
                                value = readingFontScale,
                                onValueChange = { scale ->
                                    readingFontScale = scale
                                    readerPreferences.edit().putFloat("font_scale", scale).apply()
                                },
                                valueRange = 0.85f..1.65f
                            )
                            Text("Sleep timer", style = MaterialTheme.typography.titleSmall)
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                listOf(0, 15, 30).forEach { minutes ->
                                    OutlinedButton(onClick = { controller.setSleepTimer(minutes) }) {
                                        Text(if (minutes == 0) "Off" else "${minutes} min")
                                    }
                                }
                            }
                            if (playbackStatus.sleepTimerRemainingMillis > 0) {
                                Text("Auto-pause in " +
                                    ((playbackStatus.sleepTimerRemainingMillis + 59_999) / 60_000) +
                                    " minutes")
                            }
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Button(onClick = { if (playbackStatus.isPlaying) stop() else listen() },
                                    enabled = !busy && words > 0) {
                                    Text(if (playbackStatus.isPlaying) "Pause" else if (playbackStatus.completed > 0) "Resume" else "Listen")
                                }
                                OutlinedButton(onClick = {
                                    if (playbackStatus.isPlaying) stop()
                                    exporter.launch("readaloud-" + System.currentTimeMillis() + ".wav")
                                }, enabled = !busy && words > 0) { Text("Save WAV") }
                            }
                        }
                    }
                    if (busy) CircularProgressIndicator()
                    Notice(if (playbackStatus.isPlaying || playbackStatus.message != "Ready to listen.") playbackStatus.message else notice)
                    Spacer(Modifier.height(24.dp))
                }
                1 -> Column(Modifier.weight(1f).padding(horizontal = 20.dp)) {
                    Text("Saved on this phone", style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(12.dp))
                    if (library.isEmpty()) Text("Your saved readings will appear here.")
                    LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        items(library, key = { it.id }) { item ->
                            Card(Modifier.fillMaxWidth()) {
                                Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                    Text(item.title, fontWeight = FontWeight.SemiBold)
                                    Text(item.words.toString() + " words", style = MaterialTheme.typography.labelMedium)
                                    val position = remember(item.id) { store.progress(item.id) }
                                    if (position > 0) {
                                        Text("Saved progress: section " + (position + 1),
                                            style = MaterialTheme.typography.labelSmall,
                                            color = MaterialTheme.colorScheme.primary)
                                    }
                                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                        Button(onClick = {
                                            scope.launch {
                                                stop()
                                                try {
                                                    val text = withContext(Dispatchers.IO) { store.load(item.id) }
                                                    selectedText = text
                                                    selectedTitle = item.title
                                                    selectedId = item.id
                                                    store.setLatestId(item.id)
                                                    controller.reset()
                                                    screen = 0
                                                    notice = "Ready to read."
                                                } catch (e: Exception) { notice = e.message ?: "Unable to open" }
                                            }
                                        }) { Text("Open") }
                                        OutlinedButton(onClick = {
                                            scope.launch {
                                                try {
                                                    withContext(Dispatchers.IO) { store.remove(item.id) }
                                                    if (selectedId == item.id) {
                                                        selectedText = null; selectedId = null; selectedTitle = null
                                                        controller.reset()
                                                    }
                                                    library = store.list()
                                                } catch (error: Exception) {
                                                    notice = "Could not delete the saved reading: " +
                                                        (error.message ?: "storage error")
                                                }
                                            }
                                        }) { Text("Delete") }
                                    }
                                }
                            }
                        }
                    }
                }
                2 -> Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(horizontal = 20.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("Choose your speech engine", style = MaterialTheme.typography.titleMedium)
                    Text("ReadAloud can use your phone's system engine or an installed free, on-device neural engine. Voice models are provided by the selected engine.")
                    Text("Current engine: " + controller.selectedEngine())
                    OutlinedButton(onClick = { controller.selectEngine(null); voices = emptyList() }) {
                        Text("Use system default engine")
                    }
                    controller.installedEngines().forEach { source ->
                        OutlinedButton(onClick = { controller.selectEngine(source.packageName); voices = emptyList() },
                            modifier = Modifier.fillMaxWidth()) {
                            Text(source.label)
                        }
                    }
                    Text("Free offline neural engine options", style = MaterialTheme.typography.titleMedium)
                    Text("Kokoly (Kokoro) and HayaiTTS (Piper/Kokoro) are independent open-source TTS engines. Install one, download its model once, then select it above. No cloud subscription is needed for local generation.")
                    OutlinedButton(onClick = {
                        appContext.startActivity(Intent(Intent.ACTION_VIEW,
                            Uri.parse("https://github.com/loom7/kokoly/releases")))
                    }) { Text("Kokoly open-source releases") }
                    OutlinedButton(onClick = {
                        appContext.startActivity(Intent(Intent.ACTION_VIEW,
                            Uri.parse("https://github.com/HayaiApp/HayaiTTS/releases")))
                    }) { Text("HayaiTTS open-source releases") }
                    HorizontalDivider()
                    Text("Offline voices from selected engine", style = MaterialTheme.typography.titleMedium)
                    Text("Download and configure the voice in its engine app. Only voices reported as offline are shown.")
                    OutlinedButton(onClick = { controller.refreshVoice(); voices = controller.offlineVoices() }) { Text("Refresh voices") }
                    Text("Selected: " + playbackStatus.selectedVoice)
                    if (voices.isEmpty()) Text("No offline voice listed yet. Let the speech engine initialize and refresh.")
                    voices.forEach { voice ->
                        Card(Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(12.dp)) {
                                Text(voice, maxLines = 2)
                                OutlinedButton(onClick = {
                                    if (controller.chooseVoice(voice)) { currentVoice = voice; notice = "Voice selected." }
                                    else notice = "This voice is not available offline."
                                }) { Text("Use voice") }
                            }
                        }
                    }
                }
                else -> Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(horizontal = 20.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("Private by design", style = MaterialTheme.typography.titleLarge)
                    Text("Documents and generated WAV files are processed locally. Your installed Android speech engine determines whether a voice requires a network connection. Select an offline voice for fully offline use.")
                    HorizontalDivider()
                    Text("Background listening allowance", style = MaterialTheme.typography.titleMedium)
                    Text("Daily reward ads: " + playbackStatus.earnedRewardsToday + " of " +
                        RewardPolicy.MAX_REWARDS_PER_DAY +
                        ". Each optional ad adds 15 minutes. Ads never interrupt narration.")
                    if (!playbackStatus.verifiedPremium && controller.canEarnBackgroundBonus()) {
                        Button(onClick = {
                            if (playbackStatus.isPlaying) controller.pause()
                            advertising.showRewarded {
                                if (!controller.awardBackgroundBonus()) notice =
                                    "Today's rewarded allowance is already complete."
                            }
                        }, enabled = advertising.rewardReady.value) {
                            Text(if (advertising.rewardReady.value)
                                "Watch ad for 15 minutes" else "Rewarded ad unavailable")
                        }
                    }
                    if (advertising.privacyOptionsRequired.value) {
                        OutlinedButton(onClick = { advertising.showPrivacyOptions() }) {
                            Text("Advertising privacy choices")
                        }
                    }
                    Text("Free: 30 minutes each day while ReadAloud is in the background. Playback automatically pauses at the limit. Reading while the app is open does not use the background allowance.")
                    Text("Premium: unlimited background playback after a subscription is verified. Purchases are not available in this build; no payment will be requested.")
                    HorizontalDivider()
                    HorizontalDivider()
                    Text("ReadAloud Premium", style = MaterialTheme.typography.titleLarge)
                    Text(if (playbackStatus.verifiedPremium)
                        "Active Premium: uninterrupted background listening, without ads."
                        else "Free reading remains available. Premium unlocks unlimited background listening and removes ads.")
                    if (billing.billingAvailable.value && !playbackStatus.verifiedPremium) {
                        billing.offers.value.forEach { offer ->
                            Button(onClick = { billing.purchase(offer.basePlanId) },
                                modifier = Modifier.fillMaxWidth()) {
                                Text("Premium " + offer.label + " — " + offer.displayPrice)
                            }
                        }
                        OutlinedButton(onClick = { billing.restorePurchases() }) {
                            Text("Restore purchases")
                        }
                    } else if (!playbackStatus.verifiedPremium) {
                        Text("Premium purchase is not available until Google Play products and secure verification are configured.",
                            style = MaterialTheme.typography.bodySmall)
                    }
                    Text(billing.message.value, style = MaterialTheme.typography.bodySmall)
                    Text("Monetization", style = MaterialTheme.typography.titleMedium)
                    Text("Development uses Google's test ads. Live ads require configured AdMob IDs and privacy messaging. Premium purchases are offered only when an HTTPS verifier and active Play plans are configured; purchased access requires successful server verification.")
                    HorizontalDivider()
                    Text("Storage", style = MaterialTheme.typography.titleMedium)
                    Text("Saved documents live in this app's private storage. Export WAV files using the Android save dialog. Uninstalling the app removes its private library.")
                    Text("Support for Latin-script scanned PDFs is included. Tables, equations and heavily damaged scans may require corrections.")
                    Spacer(Modifier.height(20.dp))
                }
            }
        }
    }
}

@Composable
private fun Notice(message: String) {
    Surface(color = MaterialTheme.colorScheme.surfaceVariant, shape = MaterialTheme.shapes.medium) {
        Text(message, modifier = Modifier.fillMaxWidth().padding(12.dp),
            style = MaterialTheme.typography.bodySmall)
    }
}
