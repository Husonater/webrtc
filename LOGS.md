# 📋 Log-Dateien - Übersicht

## 📍 Speicherort

Die Log-Dateien werden vom `start_lab.sh` Script automatisch in `/tmp/` erstellt:

```bash
/tmp/webrtc-signaling.log    # Signalisierungs-Server-Log
/tmp/webrtc-http.log          # HTTP-Server-Log
```

---

## 📖 Log-Dateien anzeigen

### Live-Ansicht (verfolgt neue Zeilen)

```bash
# Signaling-Server-Log
tail -f /tmp/webrtc-signaling.log

# HTTP-Server-Log
tail -f /tmp/webrtc-http.log

# Beide gleichzeitig
tail -f /tmp/webrtc-*.log
```

### Letzte 50 Zeilen anzeigen

```bash
# Signaling-Server
tail -50 /tmp/webrtc-signaling.log

# HTTP-Server
tail -50 /tmp/webrtc-http.log
```

### Komplette Log-Datei anzeigen

```bash
# Mit less (scrollbar)
less /tmp/webrtc-signaling.log

# Mit cat (ganzer Inhalt)
cat /tmp/webrtc-signaling.log
```

### In VS Code öffnen

```bash
code /tmp/webrtc-signaling.log
```

---

## 🔍 Was die Logs enthalten

### Signaling-Server-Log (`/tmp/webrtc-signaling.log`)

**Typischer Inhalt:**
```
2025-11-25 16:09:14 - INFO - Client verbunden. Total clients: 1
2025-11-25 16:09:14 - INFO - Received: offer
2025-11-25 16:09:14 - WARNING - 🔓 SDP OFFER übertragen (enthält Fingerprints!)
2025-11-25 16:09:14 - WARNING -    Fingerprint detected in SDP
2025-11-25 16:09:15 - INFO - Received: ice-candidate
2025-11-25 16:09:15 - INFO - 🌐 ICE Candidate: candidate:842163049 1 udp...
2025-11-25 16:09:15 - WARNING -    ⚠️  LOCAL IP exposed!
2025-11-25 16:09:16 - INFO - Received: ice-candidate
2025-11-25 16:09:16 - INFO - 🌐 ICE Candidate: candidate:842163050 1 udp...
2025-11-25 16:09:16 - WARNING -    ⚠️  PUBLIC IP exposed!
2025-11-25 16:09:20 - INFO - Client verbunden. Total clients: 2
2025-11-25 16:09:21 - INFO - Received: answer
2025-11-25 16:09:21 - WARNING - 🔓 SDP ANSWER übertragen (enthält Fingerprints!)
```

**Zeigt:**
- ✅ Client-Verbindungen
- ✅ SDP-Nachrichten (Offer/Answer)
- ✅ ICE-Kandidaten mit IP-Adressen
- ⚠️ Sicherheitswarnungen (exponierte IPs, Fingerprints)

---

### HTTP-Server-Log (`/tmp/webrtc-http.log`)

**Typischer Inhalt:**
```
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
127.0.0.1 - - [25/Nov/2025 16:08:41] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [25/Nov/2025 16:08:41] "GET /style.css HTTP/1.1" 200 -
127.0.0.1 - - [25/Nov/2025 16:08:41] "GET /app.js HTTP/1.1" 200 -
```

**Zeigt:**
- ✅ HTTP-Requests
- ✅ Ausgelieferte Dateien (HTML, CSS, JS)
- ✅ HTTP-Status-Codes (200 = OK, 404 = Not Found)

---

## 🔬 Nützliche Log-Analysen

### Alle exponierten IPs finden

```bash
grep "exposed" /tmp/webrtc-signaling.log
```

**Ausgabe:**
```
2025-11-25 16:09:15 - WARNING -    ⚠️  LOCAL IP exposed!
2025-11-25 16:09:16 - WARNING -    ⚠️  PUBLIC IP exposed!
```

---

### Alle SDP-Nachrichten finden

```bash
grep "SDP" /tmp/webrtc-signaling.log
```

**Ausgabe:**
```
2025-11-25 16:09:14 - WARNING - 🔓 SDP OFFER übertragen!
2025-11-25 16:09:21 - WARNING - 🔓 SDP ANSWER übertragen!
```

---

### ICE-Kandidaten zählen

```bash
grep "ICE Candidate" /tmp/webrtc-signaling.log | wc -l
```

**Ausgabe:**
```
6  # Anzahl der gesammelten ICE-Kandidaten
```

---

### Fingerprints extrahieren

```bash
grep "Fingerprint" /tmp/webrtc-signaling.log
```

**Ausgabe:**
```
2025-11-25 16:09:14 - WARNING -    Fingerprint detected in SDP
2025-11-25 16:09:21 - WARNING -    Fingerprint detected in SDP
```

---

## 📊 Log-Analyse-Script

**Speichern Sie als `analyze_logs.sh`:**

```bash
#!/bin/bash
echo "=== WebRTC Log-Analyse ==="
echo ""
echo "📁 Log-Dateien:"
ls -lh /tmp/webrtc-*.log
echo ""
echo "👥 Client-Verbindungen:"
grep "Client verbunden" /tmp/webrtc-signaling.log | wc -l
echo ""
echo "⚠️  Exponierte IPs:"
grep "exposed" /tmp/webrtc-signaling.log | wc -l
echo ""
echo "📤 SDP-Nachrichten:"
grep "SDP" /tmp/webrtc-signaling.log | wc -l
echo ""
echo "🌐 ICE-Kandidaten:"
grep "ICE Candidate" /tmp/webrtc-signaling.log | wc -l
echo ""
echo "🔐 Fingerprints:"
grep "Fingerprint detected" /tmp/webrtc-signaling.log | wc -l
```

**Ausführen:**
```bash
chmod +x analyze_logs.sh
./analyze_logs.sh
```

---

## 🗑️ Logs löschen

```bash
# Alte Logs löschen
rm /tmp/webrtc-*.log

# Labor neu starten (erstellt neue Logs)
./start_lab.sh
```

---

## 💡 Tipps

### In mehreren Terminals gleichzeitig beobachten

**Terminal 1:**
```bash
tail -f /tmp/webrtc-signaling.log
```

**Terminal 2:**
```bash
tail -f /tmp/webrtc-http.log
```

**Terminal 3:**
```bash
# Labor läuft hier
./start_lab.sh
```

---

### Logs für Dokumentation speichern

```bash
# Kopiere Logs in Ihr Projekt
cp /tmp/webrtc-signaling.log ./logs/experiment-$(date +%Y%m%d-%H%M%S).log

# Mit Zeitstempel
cp /tmp/webrtc-signaling.log ./signaling-log-ohne-security.log
cp /tmp/webrtc-signaling.log ./signaling-log-mit-security.log
```

---

## 📋 Zusammenfassung

| Log-Datei | Pfad | Inhalt |
|-----------|------|--------|
| **Signaling** | `/tmp/webrtc-signaling.log` | WebSocket, SDP, ICE, Warnungen |
| **HTTP** | `/tmp/webrtc-http.log` | HTTP-Requests, Dateien |

**Wichtigste Befehle:**
```bash
# Live anzeigen
tail -f /tmp/webrtc-signaling.log

# Letzte 50 Zeilen
tail -50 /tmp/webrtc-signaling.log

# Nach Warnungen suchen
grep "⚠️" /tmp/webrtc-signaling.log
```

---

**Die Logs sind perfekt für Ihre Dokumentation - sie zeigen die Sicherheitsrisiken im Detail!** 📊
