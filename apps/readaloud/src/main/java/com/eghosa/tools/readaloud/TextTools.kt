package com.eghosa.tools.readaloud

object TextTools {
    fun wordCount(text: String): Int {
        var words = 0
        var inside = false
        for (c in text) {
            if (c.isWhitespace()) inside = false
            else if (!inside) { words++; inside = true }
        }
        return words
    }

    /** Android TTS engines have input length limits. Segments end at word boundaries. */
    fun chunks(text: String, maxLength: Int = 2200): List<String> {
        require(maxLength >= 16)
        val result = mutableListOf<String>()
        val current = StringBuilder()
        for (match in Regex("\\S+").findAll(text)) {
            var word = match.value
            while (word.length > maxLength) {
                if (current.isNotEmpty()) { result.add(current.toString()); current.clear() }
                result.add(word.substring(0, maxLength))
                word = word.substring(maxLength)
            }
            if (word.isEmpty()) continue
            if (current.isNotEmpty() && current.length + 1 + word.length > maxLength) {
                result.add(current.toString()); current.clear()
            }
            if (current.isNotEmpty()) current.append(' ')
            current.append(word)
        }
        if (current.isNotEmpty()) result.add(current.toString())
        return result
    }
}
