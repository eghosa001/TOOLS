package com.eghosa.tools.readaloud

import android.net.Uri
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader
import com.tom_roush.pdfbox.pdmodel.PDDocument
import com.tom_roush.pdfbox.pdmodel.PDPage
import com.tom_roush.pdfbox.pdmodel.PDPageContentStream
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

    @Test fun textImportAndLibraryRoundTrip() = runBlocking {
        val input = File(context.cacheDir, "reader-test.txt")
        input.writeText((1..4000).joinToString(" ") { "word$it" })
        try {
            val imported = DocumentReader(context).extract(Uri.fromFile(input)) { _, _ -> }
            assertEquals(4000, TextTools.wordCount(imported.text))
            val library = DocumentStore(context)
            val saved = library.save("Long text test", imported.text)
            assertEquals(imported.text, library.load(saved.id))
            assertTrue(library.list().any { it.id == saved.id })
            library.remove(saved.id)
            assertFalse(library.list().any { it.id == saved.id })
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
