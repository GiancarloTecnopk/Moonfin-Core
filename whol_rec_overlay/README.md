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

## Player
**Nessuna alterazione** di ExoPlayer/MPV, HDR, Dolby Vision, selezione audio e
streaming: l'esperimento deve confrontare la qualità originale di Wholphin
con Moonfin REC sullo stesso contenuto e server Jellyfin 12.

## Compilazione
L'azione GitHub `whol-rec-android-test.yml` recupera la versione ufficiale
Wholphin al commit bloccato, applica gli overlay e compila un APK Android TV
di test con firma debug; un artifact APK viene caricato solo se i test passano.
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
collaudo reale. I pulsanti EPG/librerie personalizzati di Moonfin REC **non
sono ancora in questa build sperimentale**: verranno aggiunti dopo i test.
