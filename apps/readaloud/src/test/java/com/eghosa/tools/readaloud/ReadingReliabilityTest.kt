package com.eghosa.tools.readaloud

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Assert.assertThrows
import org.junit.Test
import java.io.ByteArrayOutputStream
import java.io.File

class ReadingReliabilityTest {
    @Test fun longDocumentsSplitWithoutDroppingWords() {
        val text = (1..4000).joinToString(" ") { "paragraph$it" }
        val chunks = TextTools.chunks(text, 900)
        assertTrue(chunks.size > 20)
        assertTrue(chunks.all { it.isNotBlank() && it.length <= 900 })
        assertEquals(text, chunks.joinToString(" "))
        assertEquals(4000, TextTools.wordCount(text))
    }

    @Test fun extremelyLongWordDoesNotExceedAndroidLimit() {
        val text = "a".repeat(5000)
        val parts = TextTools.chunks(text, 900)
        assertEquals(text, parts.joinToString(""))
        assertTrue(parts.all { it.length <= 900 })
    }

    @Test fun emptyTextProducesNoSpeechChunks() {
        assertTrue(TextTools.chunks("  \n  \t").isEmpty())
        assertEquals(0, TextTools.wordCount(" \n "))
    }

    @Test fun wavExportJoinsPcmSamplesInOrder() {
        val first = wav(16000, byteArrayOf(1, 0, 2, 0))
        val second = wav(16000, byteArrayOf(3, 0, 4, 0))
        try {
            val dest = ByteArrayOutputStream()
            WavMerger.merge(listOf(first, second), dest)
            val result = dest.toByteArray()
            assertEquals(52, result.size)
            assertEquals("RIFF", String(result, 0, 4))
            assertEquals("WAVE", String(result, 8, 4))
            assertEquals(8, result[40].toInt())
            assertEquals(listOf(1, 0, 2, 0, 3, 0, 4, 0),
                result.takeLast(8).map { it.toInt() })
        } finally { first.delete(); second.delete() }
    }

    @Test fun wavExportRejectsMismatchedSampleRates() {
        val first = wav(16000, byteArrayOf(1, 0))
        val second = wav(22050, byteArrayOf(2, 0))
        try {
            assertThrows(IllegalArgumentException::class.java) {
                WavMerger.merge(listOf(first, second), ByteArrayOutputStream())
            }
        } finally { first.delete(); second.delete() }
    }

    private fun wav(rate: Int, pcm: ByteArray): File {
        val data = ByteArrayOutputStream()
        fun ascii(v: String) = data.write(v.toByteArray(Charsets.US_ASCII))
        fun le32(v: Int) { repeat(4) { i -> data.write((v ushr (i * 8)) and 255) } }
        fun le16(v: Int) { repeat(2) { i -> data.write((v ushr (i * 8)) and 255) } }
        ascii("RIFF"); le32(36 + pcm.size); ascii("WAVEfmt ")
        le32(16); le16(1); le16(1); le32(rate); le32(rate * 2); le16(2); le16(16)
        ascii("data"); le32(pcm.size); data.write(pcm)
        return File.createTempFile("readaloud-", ".wav").apply { writeBytes(data.toByteArray()) }
    }
}
