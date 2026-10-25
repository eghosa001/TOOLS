package com.eghosa.tools.readaloud

import android.os.Bundle
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
import androidx.compose.foundation.layout.weight
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
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.math.roundToInt

class MainActivity : ComponentActivity() {
    private lateinit var engine: SpeechEngine
    private lateinit var store: DocumentStore
    private lateinit var importer: DocumentReader

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        engine = SpeechEngine(this)
        store = DocumentStore(this)
        importer = DocumentReader(this)
        setContent {
            MaterialTheme(colorScheme = if (isSystemInDarkTheme()) darkColorScheme() else lightColorScheme()) {
                ReadAloudApp(engine, store, importer)
            }
        }
    }

    override fun onDestroy() {
        engine.shutdown()
        super.onDestroy()
    }
}

@Composable
private fun ReadAloudApp(engine: SpeechEngine, store: DocumentStore, importer: DocumentReader) {
    val scope = rememberCoroutineScope()
    val mainHandler = remember { Handler(Looper.getMainLooper()) }
    var screen by remember { mutableIntStateOf(0) }
    var typedText by remember { mutableStateOf("") }
    var selectedText by remember { mutableStateOf<String?>(null) }
    var selectedTitle by remember { mutableStateOf<String?>(null) }
    var selectedId by remember { mutableStateOf<String?>(null) }
    var library by remember { mutableStateOf(store.list()) }
    var busy by remember { mutableStateOf(false) }
    var speaking by remember { mutableStateOf(false) }
    var progress by remember { mutableIntStateOf(0) }
    var progressMax by remember { mutableIntStateOf(0) }
    var rate by remember { mutableFloatStateOf(1f) }
    var notice by remember { mutableStateOf("Offline speech uses the voice installed on your phone.") }
    var voices by remember { mutableStateOf(emptyList<String>()) }
    var currentVoice by remember { mutableStateOf("System default") }
    var completedChunks by remember { mutableIntStateOf(0) }
    var lastText by remember { mutableStateOf("") }
    val activeText = selectedText ?: typedText
    val words = remember(activeText) { TextTools.wordCount(activeText) }

    fun stop() {
        engine.stop()
        speaking = false
        notice = "Stopped. Tap Listen to resume from the last completed section."
    }

    fun listen() {
        if (busy) return
        if (activeText.isBlank()) { notice = "Enter text or import a document first."; return }
        if (!engine.isReady()) { notice = "Speech engine is preparing. Check Android speech settings if this continues."; return }
        if (lastText != activeText) { completedChunks = 0; lastText = activeText }
        val pieces = TextTools.chunks(activeText, 900)
        val offset = completedChunks.coerceIn(0, pieces.size)
        if (offset >= pieces.size) completedChunks = 0
        val start = completedChunks
        val remaining = pieces.drop(start).joinToString(" ")
        speaking = true
        notice = "Reading aloud…"
        engine.speak(remaining, rate, { done, max ->
            completedChunks = minOf(pieces.size, start + done)
            progress = completedChunks
            progressMax = maxOf(pieces.size, start + max)
        }, { error ->
            speaking = false
            notice = error ?: "Finished reading."
            if (error == null) completedChunks = 0
        })
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
                completedChunks = 0
                lastText = ""
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
                engine.exportWav(activeText, uri, rate) { done, total ->
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
            NavigationBar {
                val titles = listOf("Read", "Library", "Voices", "Settings")
                val symbols = listOf("▶", "▤", "♫", "⚙")
                titles.forEachIndexed { i, title ->
                    NavigationBarItem(
                        selected = screen == i,
                        onClick = { screen = i; if (i == 2) voices = engine.offlineVoices() },
                        icon = { Text(symbols[i]) },
                        label = { Text(title) }
                    )
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
                                    onValueChange = { typedText = it; completedChunks = 0 },
                                    label = { Text("Type or paste text") },
                                    placeholder = { Text("Paste an article, chapter or message here…") },
                                    minLines = 6, maxLines = 12,
                                    modifier = Modifier.fillMaxWidth()
                                )
                            } else {
                                Text(selectedTitle ?: "Document", style = MaterialTheme.typography.titleMedium)
                                Text(selectedText?.take(1500).orEmpty(), maxLines = 12, overflow = TextOverflow.Ellipsis)
                                OutlinedButton(onClick = {
                                    stop(); selectedText = null; selectedTitle = null; selectedId = null
                                    completedChunks = 0; lastText = ""
                                }) { Text("Switch to text editor") }
                            }
                            Text(words.toString() + " words", style = MaterialTheme.typography.labelMedium)
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                OutlinedButton(onClick = {
                                    if (!busy) picker.launch(arrayOf("application/pdf",
                                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                        "text/plain", "text/markdown"))
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
                            Text("Speed: " + ((rate * 100).roundToInt()) + "%")
                            Slider(value = rate, onValueChange = { rate = it }, valueRange = 0.6f..1.7f)
                            if (progressMax > 0) Text("Processed " + progress + " of " + progressMax + " sections")
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Button(onClick = { if (speaking) stop() else listen() },
                                    enabled = !busy && words > 0) {
                                    Text(if (speaking) "Stop" else if (completedChunks > 0) "Resume" else "Listen")
                                }
                                OutlinedButton(onClick = {
                                    if (speaking) stop()
                                    exporter.launch("readaloud-" + System.currentTimeMillis() + ".wav")
                                }, enabled = !busy && words > 0) { Text("Save WAV") }
                            }
                        }
                    }
                    if (busy) CircularProgressIndicator()
                    Notice(notice)
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
                                                    lastText = ""
                                                    completedChunks = 0
                                                    screen = 0
                                                    notice = "Ready to read."
                                                } catch (e: Exception) { notice = e.message ?: "Unable to open" }
                                            }
                                        }) { Text("Open") }
                                        OutlinedButton(onClick = {
                                            scope.launch {
                                                withContext(Dispatchers.IO) { store.remove(item.id) }
                                                if (selectedId == item.id) {
                                                    selectedText = null; selectedId = null; selectedTitle = null
                                                }
                                                library = store.list()
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
                    Text("Offline voices installed on your device", style = MaterialTheme.typography.titleMedium)
                    Text("Voice quality depends on your Android speech engine. Download additional offline voices in your phone's text-to-speech settings.")
                    OutlinedButton(onClick = { voices = engine.offlineVoices() }) { Text("Refresh voices") }
                    Text("Selected: " + currentVoice)
                    if (voices.isEmpty()) Text("No offline voice listed yet. Let the speech engine initialize and refresh.")
                    voices.forEach { voice ->
                        Card(Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(12.dp)) {
                                Text(voice, maxLines = 2)
                                OutlinedButton(onClick = {
                                    if (engine.setVoice(voice)) { currentVoice = voice; notice = "Voice selected." }
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
                    Text("Current build", style = MaterialTheme.typography.titleMedium)
                    Text("This build has no advertisements, purchases, subscription collection or word limits. Monetization and downloadable neural models require a separate validated integration before Play Store release.")
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
