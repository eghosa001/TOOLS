package com.eghosa.tools.readaloud

import java.io.DataOutputStream
import java.io.File
import java.io.OutputStream
import java.io.RandomAccessFile

/** Joins standard uncompressed WAV segments without loading audio into memory. */
object WavMerger {
    private data class Header(val format: Int, val channels: Int, val rate: Int,
        val byteRate: Int, val blockAlign: Int, val bits: Int, val offset: Long, val length: Long)

    private fun RandomAccessFile.le16(): Int {
        val a = readUnsignedByte(); val b = readUnsignedByte()
        return a or (b shl 8)
    }
    private fun RandomAccessFile.le32(): Long {
        val a = le16(); val b = le16()
        return (a.toLong() or (b.toLong() shl 16)) and 0xffffffffL
    }

    private fun inspect(file: File): Header = RandomAccessFile(file, "r").use { input ->
        require(file.length() >= 44 && input.readASCII(4) == "RIFF") { "Voice did not return RIFF WAV audio" }
        input.le32()
        require(input.readASCII(4) == "WAVE") { "Audio is not WAV" }
        var fmt: IntArray? = null
        var offset = -1L
        var length = -1L
        while (input.filePointer + 8 <= input.length()) {
            val id = input.readASCII(4)
            val size = input.le32()
            val start = input.filePointer
            require(size >= 0 && start + size <= input.length()) { "Invalid WAV chunk size" }
            when (id) {
                "fmt " -> {
                    require(size >= 16) { "Unsupported WAV format chunk" }
                    fmt = intArrayOf(input.le16(), input.le16(), input.le32().toInt(),
                        input.le32().toInt(), input.le16(), input.le16())
                }
                "data" -> { offset = start; length = size; break }
            }
            input.seek(start + size + (size % 2))
        }
        val f = fmt ?: error("Missing WAV format")
        require(offset >= 0 && length >= 0) { "Missing WAV audio data" }
        require(f[0] == 1) { "Only PCM WAV export is supported for this voice" }
        Header(f[0], f[1], f[2], f[3], f[4], f[5], offset, length)
    }

    private fun RandomAccessFile.readASCII(size: Int): String {
        val arr = ByteArray(size); readFully(arr); return String(arr, Charsets.US_ASCII)
    }
    private fun DataOutputStream.ascii(value: String) { write(value.toByteArray(Charsets.US_ASCII)) }
    private fun DataOutputStream.le16(v: Int) { writeByte(v and 255); writeByte(v shr 8 and 255) }
    private fun DataOutputStream.le32(v: Long) {
        writeByte((v and 255).toInt()); writeByte((v shr 8 and 255).toInt())
        writeByte((v shr 16 and 255).toInt()); writeByte((v shr 24 and 255).toInt())
    }

    fun merge(files: List<File>, output: OutputStream) {
        require(files.isNotEmpty())
        val headers = files.map { inspect(it) }
        val first = headers.first()
        require(headers.all { it.format == first.format && it.channels == first.channels &&
            it.rate == first.rate && it.bits == first.bits && it.blockAlign == first.blockAlign }) {
            "Speech engine changed its audio format between segments"
        }
        val length = headers.sumOf { it.length }
        require(length < 0xfffffff0L) { "WAV exceeds the 4GB file format limit" }
        val out = DataOutputStream(output)
        out.ascii("RIFF"); out.le32(36 + length)
        out.ascii("WAVEfmt "); out.le32(16)
        out.le16(1); out.le16(first.channels); out.le32(first.rate.toLong())
        out.le32(first.byteRate.toLong()); out.le16(first.blockAlign); out.le16(first.bits)
        out.ascii("data"); out.le32(length)
        val buffer = ByteArray(64 * 1024)
        files.zip(headers).forEach { (file, header) ->
            RandomAccessFile(file, "r").use { input ->
                input.seek(header.offset)
                var remaining = header.length
                while (remaining > 0) {
                    val bytes = minOf(buffer.size.toLong(), remaining).toInt()
                    input.readFully(buffer, 0, bytes)
                    out.write(buffer, 0, bytes)
                    remaining -= bytes
                }
            }
        }
        out.flush()
    }
}
