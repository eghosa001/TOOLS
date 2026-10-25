package com.eghosa.tools.readaloud

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import android.os.ParcelFileDescriptor
import android.provider.OpenableColumns
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader
import com.tom_roush.pdfbox.io.MemoryUsageSetting
import com.tom_roush.pdfbox.pdmodel.PDDocument
import com.tom_roush.pdfbox.text.PDFTextStripper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.withContext
import org.xmlpull.v1.XmlPullParser
import org.xmlpull.v1.XmlPullParserFactory
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.InputStream
import java.util.zip.ZipInputStream

data class ExtractedDocument(val title: String, val text: String, val pages: Int, val ocrPages: Int)

class DocumentReader(private val context: Context) {
    fun displayName(uri: Uri): String {
        val fromProvider = runCatching {
            context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use {
                if (it.moveToFirst()) it.getString(0) else null
            }
        }.getOrNull()
        return fromProvider ?: uri.lastPathSegment ?: "Imported document"
    }

    suspend fun extract(uri: Uri, onProgress: (Int, Int) -> Unit): ExtractedDocument =
        withContext(Dispatchers.IO) {
            val title = displayName(uri)
            val ext = title.substringAfterLast('.', "").lowercase()
            val mime = context.contentResolver.getType(uri)
            when {
                ext == "pdf" || mime == "application/pdf" ->
                    readPdf(uri, title, onProgress)
                ext == "docx" || mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" ->
                    ExtractedDocument(title, readDocx(uri), 0, 0)
                ext in setOf("txt", "md") || mime in setOf("text/plain", "text/markdown") ->
                    ExtractedDocument(title, readText(uri), 0, 0)
                ext == "epub" || mime == "application/epub+zip" ->
                    ExtractedDocument(title, readEpub(uri), 0, 0)
                else -> throw IllegalArgumentException("Supported files: PDF, EPUB, DOCX, TXT and MD")
            }
        }

    private fun readEpub(uri: Uri): String {
        val temp = File.createTempFile("readaloud-book-", ".epub", context.cacheDir)
        try {
            context.contentResolver.openInputStream(uri)?.use { stream ->
                temp.outputStream().use { target ->
                    val buffer = ByteArray(64 * 1024)
                    var bytes = 0L
                    while (true) {
                        kotlinx.coroutines.currentCoroutineContext().ensureActive()
                        val count = stream.read(buffer)
                        if (count < 0) break
                        bytes += count
                        require(bytes <= 250L * 1024L * 1024L) { "EPUB exceeds 250 MB import limit" }
                        target.write(buffer, 0, count)
                    }
                }
            } ?: error("Unable to open EPUB")
            return EpubReader.extract(temp)
        } finally { temp.delete() }
    }

    /** Supports common UTF-8/UTF-16 text exports without accidentally speaking BOMs or NULs. */
    private fun readText(uri: Uri): String {
        val source = context.contentResolver.openInputStream(uri)
            ?: throw IllegalArgumentException("Unable to open document")
        return java.io.PushbackInputStream(source, 3).use { input ->
            val bom = ByteArray(3)
            var count = 0
            // Content-provider streams may return fewer bytes than requested.
            while (count < bom.size) {
                val read = input.read(bom, count, bom.size - count)
                if (read < 0) break
                if (read == 0) continue
                count += read
            }
            val (charset, skip) = when {
                count >= 2 && bom[0] == 0xFF.toByte() && bom[1] == 0xFE.toByte() ->
                    Charsets.UTF_16LE to 2
                count >= 2 && bom[0] == 0xFE.toByte() && bom[1] == 0xFF.toByte() ->
                    Charsets.UTF_16BE to 2
                count >= 3 && bom[0] == 0xEF.toByte() &&
                    bom[1] == 0xBB.toByte() && bom[2] == 0xBF.toByte() ->
                    Charsets.UTF_8 to 3
                else -> Charsets.UTF_8 to 0
            }
            if (count > skip) input.unread(bom, skip, count - skip)
            input.bufferedReader(charset).use { reader ->
                val chars = CharArray(8192)
                val out = StringBuilder()
                while (true) {
                    val n = reader.read(chars)
                    if (n < 0) break
                    require(out.length + n <= 20_000_000) { "Text exceeds supported size" }
                    out.append(chars, 0, n)
                }
                out.toString()
            }
        }
    }

    private fun readDocx(uri: Uri): String {
        val stream = context.contentResolver.openInputStream(uri) ?: error("Unable to open Word document")
        stream.use { source ->
            ZipInputStream(source).use { zip ->
                var entries = 0
                while (true) {
                    val entry = zip.nextEntry ?: break
                    if (++entries > 20000) error("Word document has too many entries")
                    if (entry.name != "word/document.xml") continue
                    val buffer = ByteArrayOutputStream()
                    val bytes = ByteArray(8192)
                    while (true) {
                        val n = zip.read(bytes)
                        if (n < 0) break
                        if (buffer.size() + n > 50_000_000) error("Word text exceeds supported size")
                        buffer.write(bytes, 0, n)
                    }
                    return parseDocxXml(ByteArrayInputStream(buffer.toByteArray()))
                }
            }
        }
        error("This DOCX has no readable document body")
    }

    private fun parseDocxXml(input: InputStream): String {
        val parser = XmlPullParserFactory.newInstance().apply { isNamespaceAware = true }.newPullParser()
        parser.setInput(input, "UTF-8")
        val text = StringBuilder()
        val ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        var event = parser.eventType
        while (event != XmlPullParser.END_DOCUMENT) {
            if (event == XmlPullParser.START_TAG && parser.namespace == ns) {
                when (parser.name) {
                    "t" -> text.append(parser.nextText())
                    "tab" -> text.append(' ')
                    "br" -> text.append('\n')
                }
            } else if (event == XmlPullParser.END_TAG && parser.namespace == ns && parser.name == "p") {
                text.append("\n")
            }
            event = parser.next()
        }
        return text.toString().trim()
    }

    private suspend fun readPdf(uri: Uri, title: String, onProgress: (Int, Int) -> Unit): ExtractedDocument {
        val temp = File.createTempFile("import-", ".pdf", context.cacheDir)
        try {
            context.contentResolver.openInputStream(uri)?.use { input ->
                temp.outputStream().use { output ->
                    val buffer = ByteArray(64 * 1024)
                    var copied = 0L
                    while (true) {
                        kotlinx.coroutines.currentCoroutineContext().ensureActive()
                        val count = input.read(buffer)
                        if (count < 0) break
                        copied += count
                        require(copied <= 250L * 1024L * 1024L) {
                            "PDF exceeds the 250 MB device import limit"
                        }
                        output.write(buffer, 0, count)
                    }
                }
            } ?: error("Unable to open PDF")
            PDFBoxResourceLoader.init(context.applicationContext)
            val output = StringBuilder()
            var ocrCount = 0
            var count = 0
            PDDocument.load(temp, MemoryUsageSetting.setupTempFileOnly()).use { pdf ->
                count = pdf.numberOfPages
                if (count == 0) error("This PDF has no pages")
                val stripped = PDFTextStripper()
                val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
                var renderer: PdfRenderer? = null
                var descriptor: ParcelFileDescriptor? = null
                try {
                    for (i in 0 until count) {
                        kotlinx.coroutines.currentCoroutineContext().ensureActive()
                        stripped.startPage = i + 1
                        stripped.endPage = i + 1
                        var pageText = stripped.getText(pdf).trim()
                        if (pageText.length < 30) {
                            if (renderer == null) {
                                descriptor = ParcelFileDescriptor.open(temp, ParcelFileDescriptor.MODE_READ_ONLY)
                                renderer = PdfRenderer(descriptor!!)
                            }
                            if (i < renderer.pageCount) {
                                renderer.openPage(i).use { page ->
                                    val scale = minOf(1.8f, 1400f / maxOf(1, page.width), 1800f / maxOf(1, page.height))
                                    val width = maxOf(1, (page.width * scale).toInt())
                                    val height = maxOf(1, (page.height * scale).toInt())
                                    val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
                                    try {
                                        bitmap.eraseColor(Color.WHITE)
                                        page.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                                        val recognized = recognizer.process(InputImage.fromBitmap(bitmap, 0)).await().text.trim()
                                        if (recognized.length > pageText.length) {
                                            pageText = recognized
                                            ocrCount++
                                        }
                                    } finally { bitmap.recycle() }
                                }
                            }
                        }
                        if (pageText.isNotBlank()) output.append(pageText).append("\n\n")
                        onProgress(i + 1, count)
                        if (output.length > 35_000_000) error("Extracted text exceeds supported size")
                    }
                } finally {
                    renderer?.close()
                    descriptor?.close()
                    recognizer.close()
                }
            }
            if (output.isBlank()) error("No readable text detected. Try a clearer scan or an unlocked PDF.")
            return ExtractedDocument(title, output.toString().trim(), count, ocrCount)
        } finally { temp.delete() }
    }
}
