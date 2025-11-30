# 🔒 WebRTC Security Lab

Praktisches Labor zur Demonstration von WebRTC-Sicherheitsrisiken für die Aufgabe 20: WebRTC – Funktionalität und Sicherheit.

## 📋 Übersicht

Dieses Lab demonstriert:
- ✅ WebRTC-Architektur und ICE-Kandidaten
- ⚠️ 3 kritische Sicherheitsrisiken
- 🔓 Unverschlüsselte vs. verschlüsselte Signalisierung
- 🛡️ Privacy Badger-Effekte auf WebRTC
- 📊 Echtzeit-Analyse von Netzwerkverbindungen

## 🚀 Schnellstart

### 1. Installation

```bash
cd webrtc-lab

# Python-Abhängigkeiten installieren
pip install -r requirements.txt
```

### 2. Lab starten

**Terminal 1: Signalisierungsserver**
```bash
python signaling_server.py
```

**Terminal 2: HTTP-Server für Web-Client**
```bash
python -m http.server 8000
```

### 3. Browser öffnen

Öffnen Sie **zwei Browser-Tabs** auf:
```
http://localhost:8000
```

## 🎯 Verwendung

### Verbindung herstellen

1. **In beiden Tabs**: Klicken Sie auf "🔌 Mit Server verbinden"
2. **In einem Tab**: Klicken Sie auf "📞 Anruf starten"
3. **Erlauben Sie** Kamera-/Mikrofon-Zugriff
4. **Beobachten Sie** die ICE-Kandidaten und Sicherheitswarnungen

### Sicherheitsexperimente

#### Experiment 1: IP-Leakage

**Ohne mDNS:**
- [ ] mDNS-Checkbox **deaktivieren**
- [ ] Anruf starten
- [ ] **Beobachten**: Lokale IPs (192.168.x.x) werden exponiert

**Mit mDNS:**
- [x] mDNS-Checkbox **aktivieren**
- [x] Anruf starten
- [x] **Beobachten**: `.local`-Hostnamen statt IPs

#### Experiment 2: Privacy Badger

**Ohne Privacy Badger:**
- [ ] Privacy Badger **deaktiviert**
- [ ] **Ergebnis**: Alle Kandidaten-Typen (host, srflx, relay)
- [ ] **Verbindung**: Direkt P2P (optimal)

**Mit Privacy Badger:**
- [x] Privacy Badger **aktiviert**
- [x] **Ergebnis**: Nur relay-Kandidaten
- [x] **Verbindung**: Über TURN-Server (höhere Latenz)

#### Experiment 3: Verschlüsselte Signalisierung

**Unverschlüsselt (Standard):**
- [ ] "TLS für Signalisierung" **deaktiviert**
- [ ] Signaling-Server-Log prüfen
- [ ] **Warnung**: SDP-Fingerprints im Klartext

**Verschlüsselt:**
- [x] "TLS für Signalisierung" **aktiviert**
- [x] **Hinweis**: In diesem Demo nicht implementiert
- [x] In Produktion würde `wss://` verwendet

## 📊 Was Sie beobachten können

### ICE-Kandidaten-Panel
- **Host** (grün): Lokale IP-Adressen
- **srflx** (gelb): Öffentliche IP via STUN
- **relay** (rot): TURN-Server-Adresse

### Sicherheitswarnungen
- ⚠️ Risiko 1: Unverschlüsselte Signalisierung
- ⚠️ Risiko 2: IP-Adress-Leakage
- ⚠️ Risiko 3: TURN-Server als Angriffspunkt

### Verbindungsstatistiken
- **Verbindungstyp**: P2P / STUN / TURN
- **Lokale IP**: Ihre ausgehende Adresse
- **Remote IP**: Adresse des Peers
- **Verschlüsselung**: DTLS-SRTP Status

## 🔬 Erweiterte Analyse

### Wireshark-Analyse

```bash
# WebSocket-Traffic aufzeichnen
tcpdump -i lo -w webrtc.pcap port 8080

# In Wireshark öffnen
wireshark webrtc.pcap

# Filter
tcp.port == 8080 && websocket
```

**Was Sie sehen**:
- Unverschlüsseltes WebSocket: SDP-Nachrichten im Klartext
- ICE-Kandidaten mit IP-Adressen
- DTLS-Fingerprints

### Signaling-Server-Log

Der Server loggt automatisch:
```
🔓 SDP OFFER übertragen (enthält Fingerprints!)
⚠️  LOCAL IP exposed!
⚠️  PUBLIC IP exposed!
```

## 🛡️ Sicherheitsdemonstrationen

### Demo 1: MITM-Angriff (Konzept)

**Szenario**: Unverschlüsselte Signalisierung
- Angreifer kann SDP-Fingerprints lesen
- Manipulation möglich → MITM

**Mitigation**: WSS (WebSocket Secure) verwenden

### Demo 2: VPN-Bypass

**Ohne mDNS + STUN**:
- WebRTC sammelt öffentliche IP via STUN
- VPN wird umgangen!
- Echte IP wird exponiert

**Mitigation**: 
- mDNS aktivieren
- Privacy Badger verwenden
- Nur eigene STUN-Server erlauben

### Demo 3: Privacy vs. Performance

**Trade-off visualisiert**:
- Privacy Badger AN → Geschützt, aber langsamer
- Privacy Badger AUS → Schneller, aber exponiert

## 📚 Dokumentation

### Hauptdokumente

1. **[webrtc_dokumentation.md](../webrtc_dokumentation.md)**
   - WebRTC-Architektur
   - Signalisierung, ICE, STUN/TURN
   - DTLS, SRTP-Verschlüsselung
   - mDNS-Namensauflösung

2. **[sicherheitsanalyse.md](../sicherheitsanalyse.md)**
   - 3 Sicherheitsrisiken im Detail
   - Nachrichtenfluss-Analysen
   - Privacy Badger-Effekte
   - Unternehmenssicherheit

## 🏢 Unternehmensnetzwerk-Empfehlungen

Aus der Sicherheitsanalyse:

1. ✅ **WSS statt WS** für Signalisierung
2. ✅ **Eigene TURN-Server** (Coturn)
3. ✅ **Firewall-Regeln** (nur bekannte Server)
4. ✅ **mDNS-Policy** in Browsern aktivieren
5. ✅ **CSP-Header** setzen
6. ✅ **Monitoring** implementieren

## 🔧 Troubleshooting

### Server startet nicht
```bash
# Port bereits belegt?
lsof -i :8080
kill -9 <PID>

# Python-Abhängigkeiten fehlen?
pip install --upgrade websockets aiohttp
```

### Keine Videoanzeige
- Browser-Berechtigungen prüfen (Kamera/Mikrofon)
- HTTPS kann erforderlich sein (getUserMedia-Policy)
- Andere Browser testen (Chrome, Firefox)

### Keine ICE-Kandidaten
- Firewall blockiert UDP?
- STUN-Server nicht erreichbar?
- Browser-Konsole prüfen (F12)

## 📝 Lizenz

Bildungszwecke - Sichere Unternehmensnetzwerke

## ⚠️ Sicherheitshinweis

Dieses Lab demonstriert **absichtlich** Sicherheitsrisiken zu Bildungszwecken. 

**Nicht für Produktion verwenden!**

Für produktive Umgebungen:
- Verwenden Sie immer TLS/WSS
- Betreiben Sie eigene STUN/TURN-Server
- Implementieren Sie Authentifizierung
- Führen Sie regelmäßige Security Audits durch
# webrtc
