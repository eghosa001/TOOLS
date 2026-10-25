package com.eghosa.tools.readaloud

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.UUID

data class StoredDocument(val id: String, val title: String, val words: Int, val timestamp: Long)

class DocumentStore(context: Context) {
    private val base = File(context.filesDir, "documents").also { it.mkdirs() }
    private val prefs = context.getSharedPreferences("readaloud_library", Context.MODE_PRIVATE)

    @Synchronized
    fun list(): List<StoredDocument> {
        val raw = prefs.getString("index", "[]") ?: "[]"
        val items = JSONArray(raw)
        return (0 until items.length()).mapNotNull { index ->
            runCatching {
                val obj = items.getJSONObject(index)
                val id = obj.getString("id")
                if (!File(base, "$id.txt").isFile) return@runCatching null
                StoredDocument(id, obj.getString("title"), obj.getInt("words"), obj.getLong("timestamp"))
            }.getOrNull()
        }.filterNotNull().sortedByDescending { it.timestamp }
    }

    @Synchronized
    fun save(title: String, text: String): StoredDocument {
        require(text.isNotBlank()) { "No extractable text found" }
        val id = UUID.randomUUID().toString()
        val file = File(base, "$id.txt")
        file.writeText(text, Charsets.UTF_8)
        val item = StoredDocument(id, title.take(150).ifBlank { "Untitled" }, TextTools.wordCount(text), System.currentTimeMillis())
        val all = list().toMutableList().also { it.add(0, item) }
        saveIndex(all)
        prefs.edit().putString("last_id", item.id).apply()
        return item
    }

    fun load(id: String): String {
        require(Regex("[a-fA-F0-9-]{36}").matches(id))
        return File(base, "$id.txt").readText(Charsets.UTF_8)
    }

    @Synchronized
    fun remove(id: String) {
        require(Regex("[a-fA-F0-9-]{36}").matches(id))
        File(base, "$id.txt").delete()
        saveIndex(list().filter { it.id != id })
        val editor = prefs.edit().remove("position_" + id)
        if (prefs.getString("last_id", "") == id) editor.remove("last_id")
        editor.apply()
    }

    /** Store an approximate speech-section bookmark for saved documents. */
    @Synchronized
    fun progress(id: String): Int {
        require(Regex("[a-fA-F0-9-]{36}").matches(id))
        return prefs.getInt("position_" + id, 0).coerceAtLeast(0)
    }

    @Synchronized
    fun setProgress(id: String, section: Int) {
        require(Regex("[a-fA-F0-9-]{36}").matches(id))
        prefs.edit().putInt("position_" + id, section.coerceAtLeast(0)).apply()
    }

    fun latestId(): String? = prefs.getString("last_id", null)
    fun setLatestId(id: String) { prefs.edit().putString("last_id", id).apply() }

    private fun saveIndex(items: List<StoredDocument>) {
        val arr = JSONArray()
        items.forEach {
            arr.put(JSONObject().put("id", it.id).put("title", it.title)
                .put("words", it.words).put("timestamp", it.timestamp))
        }
        check(prefs.edit().putString("index", arr.toString()).commit()) { "Could not save library index" }
    }
}
