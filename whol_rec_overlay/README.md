# Whol REC — esperimento Android TV / Fire TV

## Stato
Ramo di integrazione isolato dalla Moonfin REC 3.1.1. Questo ramo contiene
un **overlay Kotlin** per Wholphin, un applicatore riproducibile e la pipeline
di build. Il codice Wholphin originale viene recuperato dal commit bloccato
`572090863cb7d775cb42818fec632e32fb297dc9` (sviluppo Jellyfin 12).

## REC v0.1 (test)
- Pulsante REC nell'OSD durante la riproduzione di un canale TV
- Scelta durata 30/60/120/180 minuti anche senza guida EPG
- Registrazione creata nel DVR Jellyfin via `/LiveTv/Timers`
- STOP REC con conferma; cancella solo i timer manuali Whol REC
- Pallino rosso REC quando il timer manuale risulta attivo
- Registrazione indipendente dalla riproduzione TV; chiudere il player non ferma il DVR
- Conserva le registrazioni EPG già presenti in Wholphin
- Evita il crash nel DVR per programmi mancanti (`programInfo == null`)
- Identità separata `com.github.damontecres.wholphin.wholrec.debug` per affiancare Wholphin e Moonfin REC

## Wholphin REC — integrazione EPG e NAS (prossima build)

- **Registrazioni da EPG:** conserviamo `ProgramDialog` Wholphin,
  già dotato di REC programma singolo / serie e annullamento timer.
- **REC manuale senza EPG:** pulsante OSD con durata e STOP confermato.
- **Timer DVR:** nuovo pannello con elenco timer Jellyfin, date e
  cancellazione protetta dei soli timer manuali Whol REC.
- **Aggiorna EPG:** richiama l'attività amministrativa Jellyfin
  `RefreshGuide` tramite `GET /ScheduledTasks` e
  `POST /ScheduledTasks/Running/{Id}` (stesso flusso della Moonfin REC).
- **Aggiorna librerie:** richiama `POST /Library/Refresh` con la sessione
  Jellyfin autenticata (richiede permessi di amministratore).
- **Aggiorna liste IPTV del Synology:** richiama in POST un endpoint
  configurabile NAS/Home Assistant. L'app NON inventa endpoint né
  modifica direttamente gli script `PG_IPTV_Jellyfin_AutoUpdate.py`
  o `aggiorna_epg.py`: serve collegarli una sola volta a un servizio
  HTTP protetto. Non salvare password amministrative nel codice APK.
- **Pannello:** accessibile sia da Impostazioni principali sia dalla guida EPG.
- **Branding:** icona distinta cyan/blu con pinna, badge REC rosso, nome
  *Wholphin REC* e banner Android TV / Fire TV, generati per tutte le
  densità nel processo di build da `generate_whol_rec_branding.py`.
- **Firma/identità:** invariati package
  `com.github.damontecres.wholphin.wholrec.debug` e SHA256 della firma
  persistente. Il versionCode cresce automaticamente, quindi l'APK
  aggiorna quello installato senza cancellare le impostazioni.

L'integrazione del codice non implica che gli script NAS siano eseguibili
finché non viene configurato un endpoint HTTP reale nel pannello. I comandi
DVR/EPG devono essere collaudati sul backend Jellyfin 12 e sul Fire TV Cube.

## Correzione REC Live TV HTTP 500 (post #17)

Il server Jellyfin richiede che `POST /LiveTv/Timers` contenga
`ServiceName` per selezionare il servizio DVR. Il prototipo originale
costruiva il timer manuale senza questo campo, provocando un HTTP 500.
La correzione chiama prima `GET /LiveTv/Timers/Defaults` e riutilizza
`ServiceName`, `ServerId`, `Priority` e `KeepUntil` restituiti dal
server, mantenendo `ProgramId = null` per la registrazione senza EPG.
Sono inclusi test che verificano i campi del timer, il limite della durata
e la gestione degli errori. Nessun cambiamento ai motori video, DTS/HDR,
package o firma persistente.

## Player
**Nessuna alterazione** di ExoPlayer/MPV, HDR, Dolby Vision, selezione audio e
streaming: l'esperimento deve confrontare la qualità originale di Wholphin
con Moonfin REC sullo stesso contenuto e server Jellyfin 12.

## Compilazione
L'azione GitHub `whol-rec-android-test.yml` recupera la versione ufficiale
Wholphin al commit bloccato, applica gli overlay e compila un APK Android TV
di test con firma **persistente** usando i Secrets già configurati nel repository
per Moonfin REC; un artifact e una release GitHub vengono pubblicati solo se
test, compilazione e controllo SHA256 del certificato sono riusciti.
Per applicare in locale:
```bash
git clone https://github.com/damontecres/Wholphin.git wholphin-upstream
cd wholphin-upstream && git checkout 572090863cb7d775cb42818fec632e32fb297dc9
cd ..
python3 scripts/apply_whol_rec.py wholphin-upstream
cd wholphin-upstream && ./gradlew :app:assembleDefaultDebug
```

## Collaudo Fire TV Cube
1. Installare **senza disinstallare Moonfin REC** (package distinto).
2. Collegare Jellyfin 12 e provare i canali con e senza EPG.
3. REC di 30 secondi non è disponibile nella prima UI: verificare i 30 minuti,
   interrompendo manualmente dopo 20–40 secondi e dopo oltre un minuto.
4. Verificare file su Jellyfin/NAS, sincronismo audio e qualità Direct Play
   sugli stessi film HEVC+DTS e Dolby Vision usati su Moonfin.
5. Verificare che chiudere la Live TV non interrompa la registrazione.

## Limiti da testare
La partenza immediata senza EPG e lo stop sono soggetti al comportamento DVR
del server e al backend Live TV. I controlli automatici non sostituiscono un
collaudo reale. I comandi EPG/librerie e il bridge IPTV sono inclusi nel ramo di integrazione, ma devono ancora superare la compilazione e il collaudo NAS.

## Aggiornamenti senza perdita dei dati
- Il package rimane sempre `com.github.damontecres.wholphin.wholrec.debug`.
- La pipeline usa la stessa chiave di firma persistente dai GitHub Secrets
  (non genera più una chiave Debug casuale ad ogni build).
- Il `versionCode` è `20001000 + GITHUB_RUN_NUMBER`; cresce automaticamente
  a ogni nuova esecuzione del workflow.
- Ogni APK firmato viene verificato contro il certificato atteso e pubblicato
  in una GitHub pre-release permanente.
- **Unica eccezione:** passaggio da Test 1/Test 2, firmate con chiavi casuali,
  alla prima versione a firma persistente. Android richiede di disinstallare
  **soltanto Wholphin REC Test** una volta. Le installazioni successive possono
  usare `adb install -r nome.apk` senza perdere autenticazione e preferenze.
- Mai disinstallare Moonfin REC: package distinto.
