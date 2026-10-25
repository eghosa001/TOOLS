package com.eghosa.tools.readaloud

import org.xmlpull.v1.XmlPullParser
import org.xmlpull.v1.XmlPullParserFactory
import java.io.File
import java.io.InputStream
import java.nio.file.Paths
import java.util.zip.ZipFile

/**
 * EPUB 2/3 DRM-free reading-order parser.
 * Follows package spine rather than ZIP insertion / filename ordering.
 */
object EpubReader {
    const val MAX_TEXT_LENGTH = 25_000_000
    private const val MAX_CHAPTERS = 5000
    private const val MAX_CHAPTER_BYTES = 16L * 1024 * 1024
    private const val MAX_PACKAGE_BYTES = 2L * 1024 * 1024
    private const val MAX_ZIP_ITEMS = 10_000

    private fun limited(input: InputStream, maxBytes: Long): InputStream =
        object : java.io.FilterInputStream(input) {
            private var remaining = maxBytes
            override fun read(): Int {
                if (remaining <= 0L) {
                    if (super.read() == -1) return -1
                    throw IllegalArgumentException("EPUB entry too large")
                }
                val v = super.read()
                if (v >= 0) remaining--
                return v
            }
            override fun read(bytes: ByteArray, offset: Int, length: Int): Int {
                if (length == 0) return 0
                if (remaining <= 0L) {
                    if (super.read() == -1) return -1
                    throw IllegalArgumentException("EPUB entry too large")
                }
                val result = super.read(bytes, offset, minOf(length.toLong(), remaining).toInt())
                if (result > 0) remaining -= result
                return result
            }
        }

    private fun parser(input: InputStream): XmlPullParser =
        XmlPullParserFactory.newInstance().apply { isNamespaceAware = true }.newPullParser().apply {
            setInput(input, "UTF-8")
            // EPUB XHTML often contains a few HTML named entities.
            for ((name, text) in mapOf("nbsp" to " ", "mdash" to "—", "ndash" to "–",
                "ldquo" to "“", "rdquo" to "”", "lsquo" to "‘", "rsquo" to "’")) {
                defineEntityReplacementText(name, text)
            }
        }

    private fun rootfile(zip: ZipFile): String {
        val entry = zip.getEntry("META-INF/container.xml")
            ?: error("Invalid EPUB: missing container.xml")
        limited(zip.getInputStream(entry), MAX_PACKAGE_BYTES).use { input ->
            val xml = parser(input)
            while (xml.eventType != XmlPullParser.END_DOCUMENT) {
                if (xml.eventType == XmlPullParser.START_TAG && xml.name == "rootfile") {
                    return xml.getAttributeValue(null, "full-path")
                        ?.takeIf { it.isNotBlank() } ?: error("EPUB package path missing")
                }
                xml.next()
            }
        }
        error("Invalid EPUB: no package manifest")
    }

    private fun chapterPath(opfPath: String, href: String): String {
        val decoded = java.net.URLDecoder.decode(href.substringBefore('#').replace("+", "%2B"), "UTF-8")
        val base = Paths.get(opfPath).parent ?: Paths.get("")
        val file = base.resolve(decoded).normalize().toString().replace('\\', '/')
        require(!file.startsWith("/") && !file.startsWith("../") && file != "..") {
            "Unsafe EPUB chapter path"
        }
        return file
    }

    private fun chapter(input: InputStream): String {
        val xml = parser(input)
        val out = StringBuilder()
        var inBody = false
        var depth = 0
        var excludedDepth = 0
        while (xml.eventType != XmlPullParser.END_DOCUMENT) {
            val name = xml.name?.lowercase()
            when (xml.eventType) {
                XmlPullParser.START_TAG -> {
                    if (name == "body") { inBody = true; depth = 1 }
                    else if (inBody) {
                        depth++
                        if (excludedDepth == 0 && name in setOf("script","style","svg","nav"))
                            excludedDepth = depth
                        if (excludedDepth == 0 && name in setOf("br","p","div","h1","h2","h3","h4","h5","h6","li"))
                            out.append('\n')
                    }
                }
                XmlPullParser.TEXT -> if (inBody && excludedDepth == 0) {
                    out.append(xml.text ?: "")
                    require(out.length < MAX_TEXT_LENGTH) { "EPUB chapter exceeds supported text size" }
                }
                XmlPullParser.END_TAG -> if (inBody) {
                    if (excludedDepth == depth) excludedDepth = 0
                    if (name == "body") inBody = false
                    depth--
                }
            }
            xml.next()
        }
        return out.toString().replace(Regex("[ \\t]+"), " ").trim()
    }

    fun extract(file: File): String = ZipFile(file).use { zip ->
        require(zip.size() <= MAX_ZIP_ITEMS) { "EPUB contains too many files" }
        val opfPath = rootfile(zip)
        require(!opfPath.startsWith("/") && !opfPath.startsWith("../") &&
            !opfPath.contains("/../")) { "Unsafe EPUB package path" }
        val opfEntry = zip.getEntry(opfPath) ?: error("Invalid EPUB: OPF package missing")
        val resources = mutableMapOf<String, String>()
        val spine = mutableListOf<String>()
        limited(zip.getInputStream(opfEntry), MAX_PACKAGE_BYTES).use { input ->
            val xml = parser(input)
            while (xml.eventType != XmlPullParser.END_DOCUMENT) {
                if (xml.eventType == XmlPullParser.START_TAG) {
                    when (xml.name) {
                        "item" -> {
                            val id = xml.getAttributeValue(null,"id")
                            val href = xml.getAttributeValue(null,"href")
                            val media = xml.getAttributeValue(null,"media-type")
                            if (!id.isNullOrBlank() && !href.isNullOrBlank() &&
                                media in setOf("application/xhtml+xml","text/html"))
                                resources[id] = href
                        }
                        "itemref" -> {
                            val id = xml.getAttributeValue(null, "idref")
                            if (!id.isNullOrBlank() &&
                                xml.getAttributeValue(null, "linear") != "no") spine.add(id)
                        }
                    }
                }
                xml.next()
            }
        }
        require(spine.isNotEmpty() && spine.size <= MAX_CHAPTERS) {
            "EPUB has an invalid number of readable chapters"
        }
        val out = StringBuilder()
        for (id in spine) {
            val href = resources[id] ?: continue
            val path = chapterPath(opfPath, href)
            val entry = zip.getEntry(path) ?: continue
            require(entry.size <= MAX_CHAPTER_BYTES || entry.size == -1L) {
                "EPUB chapter is too large"
            }
            limited(zip.getInputStream(entry), MAX_CHAPTER_BYTES).use { stream ->
                val text = chapter(stream)
                if (text.isNotBlank()) {
                    require(out.length + text.length < MAX_TEXT_LENGTH) { "EPUB text exceeds supported size" }
                    out.append(text).append("\n\n")
                }
            }
        }
        out.toString().trim().ifBlank {
            error("EPUB contains no readable chapter text. Encrypted EPUBs are not supported.")
        }
    }
}
