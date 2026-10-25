package com.eghosa.tools.readaloud

import android.net.Uri
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader
import com.tom_roush.pdfbox.pdmodel.PDDocument
import com.tom_roush.pdfbox.pdmodel.PDPage
import com.tom_roush.pdfbox.pdmodel.PDPageContentStream
import com.tom_roush.pdfbox.pdmodel.common.PDRectangle
import com.tom_roush.pdfbox.pdmodel.graphics.image.LosslessFactory
import com.tom_roush.pdfbox.pdmodel.font.PDType1Font
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

@RunWith(AndroidJUnit4::class)
class ReaderFlowInstrumentedTest {
    private val context get() = ApplicationProvider.getApplicationContext<android.content.Context>()

    @Test fun epubSpineOrderAndHiddenMarkup() = runBlocking {
        val file = File(context.cacheDir, "reader-book.epub")
        ZipOutputStream(file.outputStream()).use { zip ->
            fun add(path: String, content: String) {
                zip.putNextEntry(ZipEntry(path))
                zip.write(content.toByteArray(Charsets.UTF_8))
                zip.closeEntry()
            }
            add("META-INF/container.xml", """<?xml version="1.0"?>
                <container><rootfiles><rootfile full-path="OEBPS/content.opf"/></rootfiles></container>""")
            add("OEBPS/content.opf", """<?xml version="1.0"?>
                <package><manifest>
                <item id="a" href="chap-one.xhtml" media-type="application/xhtml+xml"/>
                <item id="b" href="chap-two.xhtml" media-type="application/xhtml+xml"/>
                </manifest><spine><itemref idref="b"/><itemref idref="a"/></spine></package>""")
            add("OEBPS/chap-one.xhtml", """<?xml version="1.0"?>
                <html><body><p>Second chapter.</p></body></html>""")
            add("OEBPS/chap-two.xhtml", """<?xml version="1.0"?>
                <html><body><nav>Do not speak the menu</nav><h1>First chapter.</h1></body></html>""")
        }
        try {
            val extracted = DocumentReader(context).extract(Uri.fromFile(file)) { _, _ -> }
            assertTrue(extracted.text.contains("First chapter."))
            assertTrue(extracted.text.indexOf("First chapter.") < extracted.text.indexOf("Second chapter."))
            assertFalse(extracted.text.contains("Do not speak"))
        } finally { file.delete() }
    }

    @Test fun corruptedEpubIsRejectedWithoutSavingToLibrary() = runBlocking {
        val file = File(context.cacheDir, "reader-bad.epub")
        ZipOutputStream(file.outputStream()).use { zip ->
            zip.putNextEntry(ZipEntry("junk.txt"))
            zip.write("not an epub".toByteArray())
            zip.closeEntry()
        }
        try {
            var rejected = false
            try {
                DocumentReader(context).extract(Uri.fromFile(file)) { _, _ -> }
            } catch (failure: Exception) {
                rejected = true
            }
            assertTrue("Missing EPUB container must fail", rejected)
        } finally { file.delete() }
    }

    @Test fun textImportAndLibraryRoundTrip() = runBlocking {
        val input = File(context.cacheDir, "reader-test.txt")
        input.writeText((1..4000).joinToString(" ") { "word$it" })
        try {
            val imported = DocumentReader(context).extract(Uri.fromFile(input)) { _, _ -> }
            assertEquals(4000, TextTools.wordCount(imported.text))
            val library = DocumentStore(context)
            val saved = library.save("Long text test", imported.text)
            assertEquals(imported.text, library.load(saved.id))
            assertEquals(0, library.progress(saved.id))
            library.setProgress(saved.id, 13)
            assertEquals(13, DocumentStore(context).progress(saved.id))
            library.setProgress(saved.id, -200)
            assertEquals(0, library.progress(saved.id))
            library.setProgress(saved.id, 5)
            assertTrue(library.list().any { it.id == saved.id })
            library.remove(saved.id)
            assertFalse(library.list().any { it.id == saved.id })
            assertEquals(0, library.progress(saved.id))
        } finally { input.delete() }
    }

    @Test fun utf16TextImportsWithNoBomCharacters() = runBlocking {
        val input = File(context.cacheDir, "reader-test-utf16.txt")
        input.outputStream().use {
            it.write(byteArrayOf(0xFF.toByte(), 0xFE.toByte()))
            it.write("A readable Unicode file — café".toByteArray(Charsets.UTF_16LE))
        }
        try {
            val imported = DocumentReader(context).extract(Uri.fromFile(input)) { _, _ -> }
            assertEquals("A readable Unicode file — café", imported.text)
        } finally { input.delete() }
    }

    @Test fun docxImportReadsParagraphs() = runBlocking {
        val input = File(context.cacheDir, "reader-test.docx")
        ZipOutputStream(input.outputStream()).use { zip ->
            zip.putNextEntry(ZipEntry("word/document.xml"))
            zip.write("""<?xml version="1.0" encoding="UTF-8"?>
                <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                <w:body><w:p><w:r><w:t>First paragraph.</w:t></w:r></w:p>
                <w:p><w:r><w:t>Second paragraph.</w:t></w:r></w:p></w:body>
                </w:document>""".trimIndent().toByteArray())
            zip.closeEntry()
        }
        try {
            val imported = DocumentReader(context).extract(Uri.fromFile(input)) { _, _ -> }
            assertTrue(imported.text.contains("First paragraph."))
            assertTrue(imported.text.contains("Second paragraph."))
        } finally { input.delete() }
    }

    @Test fun scannedPdfUsesOfflineOcr() = runBlocking {
        PDFBoxResourceLoader.init(context)
        val input = File(context.cacheDir, "reader-scanned-test.pdf")
        val bitmap = Bitmap.createBitmap(1000, 400, Bitmap.Config.ARGB_8888)
        Canvas(bitmap).apply {
            drawColor(Color.WHITE)
            drawText("Scanning text clearly", 35f, 210f,
                Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    color = Color.BLACK
                    textSize = 68f
                    isFakeBoldText = true
                })
        }
        try {
            PDDocument().use { pdf ->
                val page = PDPage(PDRectangle(1000f, 400f))
                pdf.addPage(page)
                val image = LosslessFactory.createFromImage(pdf, bitmap)
                PDPageContentStream(pdf, page).use { it.drawImage(image, 0f, 0f, 1000f, 400f) }
                pdf.save(input)
            }
            val result = DocumentReader(context).extract(Uri.fromFile(input)) { _, _ -> }
            assertEquals(1, result.pages)
            assertEquals(1, result.ocrPages)
            assertTrue(result.text.contains("Scanning", ignoreCase = true))
        } finally {
            input.delete()
            bitmap.recycle()
        }
    }

    @Test fun manyPagePdfIsExtractedWithoutFullPageRasterization() = runBlocking {
        PDFBoxResourceLoader.init(context)
        val input = File(context.cacheDir, "reader-250-pages.pdf")
        PDDocument().use { pdf ->
            repeat(250) { index ->
                val page = PDPage()
                pdf.addPage(page)
                PDPageContentStream(pdf, page).use { canvas ->
                    canvas.beginText()
                    canvas.setFont(PDType1Font.HELVETICA, 12f)
                    canvas.newLineAtOffset(50f, 680f)
                    canvas.showText("Searchable page number ${index + 1} of two hundred fifty pages.")
                    canvas.endText()
                }
            }
            pdf.save(input)
        }
        try {
            var lastProgress = 0
            val result = DocumentReader(context).extract(Uri.fromFile(input)) { done, _ ->
                lastProgress = done
            }
            assertEquals(250, result.pages)
            assertEquals(250, lastProgress)
            assertTrue(result.text.contains("Searchable page number 1"))
            assertTrue(result.text.contains("Searchable page number 250"))
        } finally { input.delete() }
    }

    @Test fun searchablePdfTextIsExtracted() = runBlocking {
        PDFBoxResourceLoader.init(context)
        val input = File(context.cacheDir, "reader-test.pdf")
        PDDocument().use { pdf ->
            val page = PDPage()
            pdf.addPage(page)
            PDPageContentStream(pdf, page).use { canvas ->
                canvas.beginText()
                canvas.setFont(PDType1Font.HELVETICA, 12f)
                canvas.newLineAtOffset(60f, 700f)
                canvas.showText("ReadAloud searchable PDF imported correctly end to end.")
                canvas.endText()
            }
            pdf.save(input)
        }
        try {
            val document = DocumentReader(context).extract(Uri.fromFile(input)) { _, _ -> }
            assertEquals(1, document.pages)
            assertEquals(0, document.ocrPages)
            assertTrue(document.text.contains("ReadAloud searchable PDF"))
        } finally { input.delete() }
    }
}
