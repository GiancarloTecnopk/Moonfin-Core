package com.github.damontecres.wholphin.ui.detail.livetv

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.tv.material3.Button
import androidx.tv.material3.Text
import com.github.damontecres.wholphin.services.WholRecTimer
import com.github.damontecres.wholphin.services.WholRecToolsService
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class WholRecToolsState(
    val busy: Boolean = false,
    val status: String = "",
    val endpoint: String = "",
    val timers: List<WholRecTimer> = emptyList(),
)

@HiltViewModel
class WholRecToolsViewModel @Inject constructor(
    private val service: WholRecToolsService,
) : ViewModel() {
    private val _state = MutableStateFlow(WholRecToolsState(endpoint = service.getIptvEndpoint()))
    val state: StateFlow<WholRecToolsState> = _state

    private fun execute(action: suspend () -> String) {
        if (_state.value.busy) return
        _state.value = _state.value.copy(busy = true, status = "Operazione in corso…")
        viewModelScope.launch {
            try {
                val message = action()
                _state.value = _state.value.copy(busy = false, status = message)
            } catch (ex: CancellationException) {
                throw ex
            } catch (ex: Exception) {
                _state.value = _state.value.copy(busy = false, status = ex.message ?: "Operazione non riuscita")
            }
        }
    }

    fun refreshLibraries() = execute { service.refreshLibraries() }
    fun refreshEpg() = execute { service.refreshEpg() }
    fun updateIptvLists() = execute { service.updateIptvLists() }

    fun saveEndpoint(url: String) {
        if (_state.value.busy) return
        try {
            service.saveIptvEndpoint(url)
            _state.value = _state.value.copy(endpoint = service.getIptvEndpoint(), status = "Endpoint IPTV salvato sul dispositivo")
        } catch (ex: Exception) {
            _state.value = _state.value.copy(status = ex.message ?: "URL non valido")
        }
    }

    fun loadTimers() {
        if (_state.value.busy) return
        execute {
            val timers = service.listTimers()
            _state.value = _state.value.copy(timers = timers)
            "Timer Jellyfin rilevati: ${timers.size}"
        }
    }

    fun cancelManualTimer(timer: WholRecTimer) = execute {
        val message = service.cancelManualTimer(timer)
        _state.value = _state.value.copy(timers = service.listTimers())
        message
    }
}

/**
 * TV-friendly management panel. The existing Wholphin EPG ProgramDialog
 * continues to handle recording a program or entire series from EPG.
 */
@Composable
fun WholRecToolsDialog(
    onDismiss: () -> Unit,
    vm: WholRecToolsViewModel = hiltViewModel(),
) {
    val st by vm.state.collectAsState()
    var editingEndpoint by remember { mutableStateOf(false) }
    var url by remember(st.endpoint) { mutableStateOf(st.endpoint) }
    var confirmStop by remember { mutableStateOf<WholRecTimer?>(null) }

    Dialog(onDismissRequest = onDismiss) {
        Column(
            modifier = Modifier
                .background(Color(0xF5151D2D))
                .padding(20.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text("Wholphin REC • TV e registrazioni")
            Text("EPG: seleziona un programma nella guida per REC singolo o serie TV.")
            Button(onClick = vm::refreshEpg, enabled = !st.busy) {
                Text("Aggiorna guida EPG (Jellyfin)")
            }
            Button(onClick = vm::refreshLibraries, enabled = !st.busy) {
                Text("Aggiorna librerie Jellyfin")
            }
            Button(onClick = vm::updateIptvLists, enabled = !st.busy && st.endpoint.isNotBlank()) {
                Text("Aggiorna liste IPTV (NAS/HA)")
            }
            Button(onClick = { editingEndpoint = !editingEndpoint }) {
                Text(if (editingEndpoint) "Chiudi configurazione IPTV" else "Configura URL aggiornamento IPTV")
            }
            if (editingEndpoint) {
                Text("URL POST del servizio NAS/Home Assistant (non del file M3U).")
                BasicTextField(
                    value = url,
                    onValueChange = { url = it },
                    singleLine = true,
                    textStyle = TextStyle(color = Color.White, fontSize = 16.sp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Color(0xFF303D53))
                        .padding(12.dp),
                )
                Button(onClick = {
                    vm.saveEndpoint(url)
                    editingEndpoint = false
                }) { Text("Salva endpoint") }
            }
            Button(onClick = vm::loadTimers, enabled = !st.busy) {
                Text("Visualizza timer e registrazioni programmate")
            }
            if (st.timers.isNotEmpty()) {
                st.timers.forEach { timer ->
                    Text(timer.title + " · " + timer.start.take(16) + " / " + timer.end.take(16))
                    if (timer.isWholManual) {
                        Button(onClick = { confirmStop = timer }, enabled = !st.busy) {
                            Text("STOP REC · " + timer.title)
                        }
                    }
                }
            }
            if (st.status.isNotBlank()) {
                Text(st.status, color = if (st.status.contains("HTTP ") || st.status.contains("non ") || st.status.contains("Serve ")) Color.Yellow else Color.White)
            }
            Button(onClick = onDismiss) { Text("Chiudi") }
        }
    }

    confirmStop?.let { timer ->
        Dialog(onDismissRequest = { confirmStop = null }) {
            Column(
                modifier = Modifier.background(Color(0xFF1C2333)).padding(24.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text("Interrompere la registrazione manuale ${timer.title}?")
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Button(onClick = {
                        confirmStop = null
                        vm.cancelManualTimer(timer)
                    }) { Text("Conferma STOP REC") }
                    Button(onClick = { confirmStop = null }) { Text("Annulla") }
                }
            }
        }
    }
}
