# WebRTC Security Lab - Scripts Übersicht

## 🚀 Start-Scripts

### Empfohlen: All-in-One Script ⭐

**Startet das komplette Labor mit einem Befehl:**
```bash
./start_lab.sh
```

**Features:**
- ✅ Startet Signaling-Server automatisch
- ✅ Startet HTTP-Server automatisch  
- ✅ Öffnet Browser automatisch
- ✅ Zeigt farbige Status-Updates
- ✅ Überwacht Server-Gesundheit
- ✅ Automatisches Cleanup bei Ctrl+C
- ✅ Detaillierte Logs in `/tmp/`

---

### Alternative: Einzelne Scripts

**Wenn Sie die Server manuell starten möchten:**

#### Terminal 1: Signaling Server
```bash
./start_server.sh
```

#### Terminal 2: HTTP Server  
```bash
./start_client.sh
```

---

## 📋 Verwendung

### Quick Start

```bash
cd webrtc-lab
./start_lab.sh
```

Das Script:
1. ✅ Prüft Python-Installation
2. ✅ Prüft websockets-Modul
3. ✅ Startet beide Server
4. ✅ Öffnet Browser auf http://localhost:8000
5. ⏸️ Wartet (Server laufen im Hintergrund)
6. 🛑 Stoppt bei Ctrl+C

### Erwartete Ausgabe

```
=================================================
    🔒 WebRTC Security Lab
    Sicherheits-Demonstrationsumgebung
=================================================

✅ Python 3: Python 3.11.x

📦 Prüfe Dependencies...
✅ websockets-Modul gefunden

🚀 Starte Signaling Server...
✅ Signaling Server läuft (PID: 12345)
   URL: ws://localhost:8080
   Log: /tmp/webrtc-signaling.log

🌐 Starte HTTP Server...
✅ HTTP Server läuft (PID: 12346)
   URL: http://localhost:8000
   Log: /tmp/webrtc-http.log

🌍 Öffne Browser...
✅ Browser geöffnet

=================================================
    ✅ Labor läuft!
=================================================

📋 Wichtige Informationen:

  Web-Client:      http://localhost:8000
  Signaling:       ws://localhost:8080

📝 Nächste Schritte:
  1. Öffnen Sie einen zweiten Browser-Tab
  2. Navigieren Sie zu http://localhost:8000
  3. In beiden Tabs: 'Mit Server verbinden' klicken
  4. In einem Tab: 'Anruf starten' klicken
  5. Beobachten Sie ICE-Kandidaten und Sicherheitswarnungen

🔍 Logs anzeigen:
  Signaling: tail -f /tmp/webrtc-signaling.log
  HTTP:      tail -f /tmp/webrtc-http.log

⏹️  Zum Beenden: Ctrl+C drücken

=================================================
```

---

## 🔍 Log-Dateien

### Signaling Server Log
```bash
tail -f /tmp/webrtc-signaling.log
```

**Zeigt:**
- WebSocket-Verbindungen
- SDP-Nachrichten (Offer/Answer)
- ICE-Kandidaten
- Sicherheitswarnungen (IP-Leakage, Fingerprints)

### HTTP Server Log
```bash
tail -f /tmp/webrtc-http.log
```

**Zeigt:**
- HTTP-Requests
- Ausgelieferte Dateien
- Zugriffsfehler

---

## 🐛 Troubleshooting

### Problem: "websockets-Modul nicht gefunden"

**Das Script wechselt automatisch zur vereinfachten Version.**

Für volle Funktionalität:
```bash
sudo apt install python3-websockets
```

### Problem: "Port bereits belegt"

**Port 8000 oder 8080 wird bereits verwendet.**

Prüfen:
```bash
lsof -i :8000
lsof -i :8080
```

Lösung:
```bash
# Prozess beenden
kill -9 <PID>
```

### Problem: "Browser öffnet nicht"

**Kein grafischer Browser gefunden.**

Manuell öffnen:
```
http://localhost:8000
```

### Server manuell stoppen

Falls das Script nicht antwortet:
```bash
pkill -f "signaling_server"
pkill -f "http.server.*8000"
```

---

## 💡 Tipps

### Logs in Echtzeit beobachten

**Terminal 3 (während Labor läuft):**
```bash
# Signaling-Server-Ausgabe
tail -f /tmp/webrtc-signaling.log

# HTTP-Server-Ausgabe  
tail -f /tmp/webrtc-http.log

# Beide gleichzeitig
tail -f /tmp/webrtc-*.log
```

### Mehrere Clients testen

1. Labor starten: `./start_lab.sh`
2. Browser-Tab 1: http://localhost:8000
3. Browser-Tab 2: http://localhost:8000
4. Browser-Tab 3: http://localhost:8000 (Optional)

### Server-Status prüfen

```bash
# Laufende Server anzeigen
ps aux | grep -E "(signaling|http.server)"

# Ports prüfen
netstat -tulpn | grep -E "(8000|8080)"
```

---

## 📁 Script-Dateien

| Script | Zweck | Empfohlen |
|--------|-------|-----------|
| `start_lab.sh` | Startet komplettes Labor | ⭐ Ja |
| `start_server.sh` | Nur Signaling-Server | Manuell |
| `start_client.sh` | Nur HTTP-Server | Manuell |

---

## ✅ Erfolg!

Wenn Sie diese Ausgabe sehen, läuft das Labor:

```
✅ Signaling Server läuft (PID: ...)
✅ HTTP Server läuft (PID: ...)
✅ Browser geöffnet
```

**Viel Erfolg beim Testen der WebRTC-Sicherheitsrisiken!** 🔒
