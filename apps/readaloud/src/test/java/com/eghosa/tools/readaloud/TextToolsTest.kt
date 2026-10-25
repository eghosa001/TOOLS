package com.eghosa.tools.readaloud

import org.junit.Assert.*
import org.junit.Test

class TextToolsTest {
    @Test fun countWords() {
        assertEquals(0, TextTools.wordCount(" \n  "))
        assertEquals(4, TextTools.wordCount("Hello,    world!\nNew line"))
    }

    @Test fun chunksNeverExceedEngineLimit() {
        val text = (1..4000).joinToString(" ") { "word-$it" }
        val chunks = TextTools.chunks(text, 150)
        assertTrue(chunks.size > 200)
        assertTrue(chunks.all { it.length <= 150 })
        assertEquals(text, chunks.joinToString(" "))
    }

    @Test fun hugeTokenSplitsWithoutCrash() {
        val chunks = TextTools.chunks("x".repeat(600), 100)
        assertEquals(6, chunks.size)
        assertTrue(chunks.all { it.length == 100 })
    }

    @Test(expected = IllegalArgumentException::class)
    fun rejectsTooSmallChunkLimit() { TextTools.chunks("test", 4) }
}
