# Wholphin REC → aggiornamento liste IPTV sul Synology

Questo bridge è **opzionale**: serve soltanto a rendere raggiungibile via
HTTP l'attuale script `PG_IPTV_Jellyfin_AutoUpdate.py` che aggiorna le
playlist sul DS425+. Wholphin REC usa già autonomamente le API Jellyfin
per **Aggiorna EPG** (`RefreshGuide`) e **Aggiorna librerie**.

## Installazione sul Synology
1. Copiare `whol_rec_bridge.py` sul NAS, per esempio in una cartella
   `docker/whol-rec-bridge`.
2. Individuare il **vero percorso** dello script IPTV esistente; non è
   hardcodato perché può cambiare tra installazioni.
3. Generare un token: `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`.
4. Impostare le variabili d'ambiente ed eseguire il servizio come
   utente NAS autorizzato alla scrittura dei file delle playlist.

```sh
export WHOL_REC_BIND=0.0.0.0
export WHOL_REC_PORT=8767
export WHOL_REC_TOKEN='INSERIRE_UN_TOKEN_CASUALE_DI_ALMENO_32_CARATTERI'
export WHOL_REC_IPTV_SCRIPT='/percorso/reale/PG_IPTV_Jellyfin_AutoUpdate.py'
export WHOL_REC_TIMEOUT=180
python3 whol_rec_bridge.py
```

Nella schermata **Impostazioni → Wholphin REC · TV e registrazioni →
Configura URL aggiornamento IPTV**, inserire:

```
http://IP-DEL-NAS:8767/hooks/iptv/TOKEN-CASUALE
```

Poi scegliere **Aggiorna liste IPTV (NAS/HA)**. L'app invia un POST
senza inoltrare il token Jellyfin: il server risponde HTTP 202
e avvia lo script sul NAS. Sono rifiutate richieste simultanee (HTTP 409).

## Sicurezza

- Non pubblicare la porta 8767 su Internet né esporla con port-forwarding.
- Limitare l'accesso tramite firewall Synology alla LAN/dispositivi TV.
- Meglio usare un reverse proxy HTTPS o un webhook Home Assistant esistente
  se si necessita di attraversare reti diverse.
- Il token di 32+ caratteri è un segreto, **non** va condiviso nei log.
- Il servizio non accetta comandi, percorsi o argomenti arbitrari via HTTP.
- Se lo script IPTV è già esposto da un endpoint autenticato sul NAS/HA,
  non occorre installare questo bridge: basta inserire quell'URL nell'app.
- Per l'EPG `aggiorna_epg.py` esiste una pianificazione NAS separata:
  il pulsante **Aggiorna EPG** di Wholphin REC richiama invece il task
  `RefreshGuide` di Jellyfin e non esegue automaticamente lo script Python
  di aggregazione sul NAS.

## Verifica

```sh
curl http://IP-DEL-NAS:8767/health
curl -X POST 'http://IP-DEL-NAS:8767/hooks/iptv/TOKEN-CASUALE'
```

Il percorso dello script IPTV e la connettività tra TV e NAS devono
essere verificati sul dispositivo reale.
