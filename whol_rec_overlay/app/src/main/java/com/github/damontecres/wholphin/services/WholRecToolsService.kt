package com.github.damontecres.wholphin.services

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import com.github.damontecres.wholphin.services.hilt.AuthOkHttpClient
import com.github.damontecres.wholphin.services.hilt.StandardOkHttpClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.jellyfin.sdk.api.client.ApiClient
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.net.URI
import java.net.URLEncoder
import javax.inject.Inject
import javax.inject.Singleton

data class WholRecTimer(
    val id: String,
    val title: String,
    val start: String,
    val end: String,
    val isWholManual: Boolean,
)

/**
 * Whol REC management operations. No secrets or NAS addresses are baked into
 * the APK; Jellyfin uses the current authenticated SDK HTTP client.
 */
@Singleton
class WholRecToolsService @Inject constructor(
    @param:ApplicationContext private val context: Context,
    @param:AuthOkHttpClient private val jellyfinClient: OkHttpClient,
    @param:StandardOkHttpClient private val webhookClient: OkHttpClient,
    private val api: ApiClient,
) {
    private val settings = context.getSharedPreferences("whol_rec_tools", Context.MODE_PRIVATE)

    fun getIptvEndpoint(): String = settings.getString("iptv_webhook", "").orEmpty()

    fun saveIptvEndpoint(value: String) {
        val url = value.trim()
        if (url.isNotEmpty()) require(validWebhookUrl(url)) { "Serve un URL HTTP/HTTPS valido" }
        settings.edit().putString("iptv_webhook", url).apply()
    }

    private fun jellyfinUrl(path: String): String {
        val url = api.baseUrl?.trimEnd('/') ?: error("Server Jellyfin non collegato")
        return "$url/$path"
    }

    private suspend fun jellyfin(path: String, method: String = "GET"): String =
        withContext(Dispatchers.IO) {
            val req = Request.Builder().url(jellyfinUrl(path))
            if (method == "POST") req.post(byteArrayOf().toRequestBody())
            else if (method == "DELETE") req.delete()
            else req.get()
            jellyfinClient.newCall(req.build()).execute().use { response ->
                if (!response.isSuccessful) {
                    throw IOException("Jellyfin HTTP ${response.code} - ${if (response.code == 401 || response.code == 403) "permessi amministratore o sessione da verificare" else "operazione rifiutata"}")
                }
                response.body?.string().orEmpty()
            }
        }

    suspend fun refreshLibraries(): String {
        jellyfin("Library/Refresh", "POST")
        return "Scansione librerie Jellyfin avviata"
    }

    suspend fun refreshEpg(): String {
        val tasks = JSONArray(jellyfin("ScheduledTasks?IsHidden=false"))
        val matching = (0 until tasks.length())
            .map { tasks.getJSONObject(it) }
            .firstOrNull { isGuideTask(it.optString("Key")) }
            ?: throw IllegalStateException("Attività RefreshGuide non trovata nel server Jellyfin")
        val id = matching.optString("Id").takeIf { it.isNotBlank() }
            ?: throw IllegalStateException("RefreshGuide senza identificativo")
        jellyfin("ScheduledTasks/Running/${URLEncoder.encode(id, "UTF-8")}", "POST")
        return "Aggiornamento guida EPG avviato su Jellyfin"
    }

    suspend fun listTimers(): List<WholRecTimer> {
        val root = JSONObject(jellyfin("LiveTv/Timers"))
        val items = root.optJSONArray("Items") ?: JSONArray()
        return (0 until items.length()).mapNotNull { index ->
            val t = items.optJSONObject(index) ?: return@mapNotNull null
            val id = t.optString("Id").takeIf { it.isNotBlank() } ?: return@mapNotNull null
            val title = t.optString("Name").ifBlank { "Registrazione" }
            WholRecTimer(
                id = id,
                title = title,
                start = t.optString("StartDate"),
                end = t.optString("EndDate"),
                isWholManual = title.startsWith("Whol REC - "),
            )
        }
    }

    suspend fun cancelManualTimer(timer: WholRecTimer): String {
        require(timer.isWholManual) { "Le registrazioni EPG si gestiscono dalla guida" }
        jellyfin("LiveTv/Timers/${URLEncoder.encode(timer.id, "UTF-8")}", "DELETE")
        return "Timer manuale interrotto: ${timer.title}"
    }

    /**
     * Calls the user's existing NAS/Home Assistant bridge. Never forward the
     * Jellyfin token to this third-party/local endpoint.
     */
    suspend fun updateIptvLists(): String = withContext(Dispatchers.IO) {
        val url = getIptvEndpoint()
        require(validWebhookUrl(url)) {
            "Configura prima l'URL del servizio di aggiornamento IPTV sul NAS/HA"
        }
        webhookClient.newCall(
            Request.Builder()
                .url(url)
                .post(byteArrayOf().toRequestBody())
                .build()
        ).execute().use { response ->
            if (!response.isSuccessful) throw IOException("Aggiornamento liste: HTTP ${response.code}")
        }
        "Richiesta aggiornamento liste IPTV inviata al NAS/HA"
    }
}

internal fun isGuideTask(key: String) = key.equals("RefreshGuide", ignoreCase = true)

internal fun validWebhookUrl(url: String): Boolean = runCatching {
    val uri = URI(url.trim())
    (uri.scheme.equals("http", true) || uri.scheme.equals("https", true)) &&
        !uri.host.isNullOrBlank() && uri.userInfo == null && uri.fragment == null
}.getOrDefault(false)
