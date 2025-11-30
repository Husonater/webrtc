# 🎓 WebRTC Security Lab - Vollständige System-Erklärung

## 📋 Inhaltsverzeichnis

1. [System-Architektur](#1-system-architektur)
2. [Komponenten im Detail](#2-komponenten-im-detail)
3. [Datenfluss Schritt-für-Schritt](#3-datenfluss-schritt-für-schritt)
4. [Web-Interface Settings](#4-web-interface-settings)
5. [Sicherheitsmaßnahmen im Code](#5-sicherheitsmaßnahmen-im-code)
6. [Praktische Beispiele](#6-praktische-beispiele)

---

## 1. System-Architektur

### Komponenten-Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│                     WebRTC Security Lab                      │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐
│  Browser A       │         │  Browser B       │
│  (Peer A)        │         │  (Peer B)        │
│                  │         │                  │
│  ┌────────────┐  │         │  ┌────────────┐  │
│  │ app.js     │  │         │  │ app.js     │  │
│  │ (Client)   │  │         │  │ (Client)   │  │
│  └────────────┘  │         │  └────────────┘  │
└────────┬─────────┘         └─────────┬────────┘
         │                             │
         │ WebSocket (ws://)           │
         │ Port 8080                   │
         └──────────────┬──────────────┘
                        │
              ┌─────────▼─────────┐
              │  Signaling Server │
              │  (Python aiohttp) │
              │  Port 8080        │
              └───────────────────┘

         HTTP (html/js/css)
┌──────────────┴──────────────┐
│       HTTP Server           │
│    (Python http.server)     │
│        Port 8000            │
└─────────────────────────────┘

         Externe Server
┌─────────────────────────────┐
│  Google STUN Server         │
│  stun.l.google.com:19302    │
└─────────────────────────────┘
┌─────────────────────────────┐
│  TURN Server (Optional)     │
│  openrelay.metered.ca:80    │
└─────────────────────────────┘
```

---

## 2. Komponenten im Detail

### 2.1 HTTP-Server (Port 8000)

**Datei:** Python Built-in `http.server`

**Aufgabe:**
- Stellt statische Dateien bereit (HTML, CSS, JS)
- Läuft auf Port 8000

**Kommando:**
```bash
python3 -m http.server 8000
```

**Bereitgestellte Dateien:**
- `index.html` → Benutzeroberfläche
- `style.css` → Design/Layout
- `app.js` → WebRTC-Logik

---

### 2.2 Signalisierungs-Server (Port 8080)

**Datei:** `signaling_server_aiohttp.py`

**Aufgabe:**
- WebSocket-Verbindungen verwalten
- SDP-Nachrichten zwischen Peers weiterleiten
- ICE-Kandidaten austauschen
- Sicherheitswarnungen loggen

**Wichtige Funktionen:**

#### `websocket_handler(request)`
```python
async def websocket_handler(self, request):
    # 1. WebSocket-Verbindung akzeptieren
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    # 2. Client zur Liste hinzufügen
    self.clients.add(ws)
    
    # 3. Nachrichten empfangen und weiterleiten
    async for msg in ws:
        data = json.loads(msg.data)
        
        # An alle ANDEREN Clients senden (Broadcasting)
        for client in self.clients:
            if client != ws:
                await client.send_str(msg.data)
```

#### `log_message(type, data)`
```python
def log_message(self, msg_type: str, data: dict):
    # Sicherheitsanalyse
    if msg_type == 'offer':
        logger.warning("🔓 SDP OFFER enthält Fingerprints!")
    
    if 'typ host' in candidate:
        logger.warning("⚠️ LOCAL IP exposed!")
```

**WebSocket-Endpoint:** `ws://localhost:8080/ws`

---

### 2.3 Browser-Client (app.js)

**Datei:** `app.js` (17KB JavaScript)

**Hauptklasse:** `WebRTCSecurityLab`

**Struktur:**
```javascript
class WebRTCSecurityLab {
    constructor() {
        // WebSocket zum Signalisierungsserver
        this.ws = null;
        this.wsUrl = 'ws://localhost:8080/ws';
        
        // WebRTC PeerConnection
        this.peerConnection = null;
        this.localStream = null;
        
        // Einstellungen
        this.settings = {
            enableMdns: true,
            privacyBadger: false,
            encryptedSignaling: false
        };
    }
}
```

---

## 3. Datenfluss Schritt-für-Schritt

### Szenario: Zwei Browser-Tabs starten einen Anruf

#### Phase 1: Verbindung zum Signalisierungsserver

**Schritt 1:** User klickt "Mit Server verbinden"
```javascript
// app.js - Zeile 122
connectToSignaling() {
    this.ws = new WebSocket('ws://localhost:8080/ws');
}
```

**Was passiert:**
1. Browser öffnet WebSocket-Verbindung
2. Server empfängt Verbindung
3. Server sendet Willkommensnachricht
4. Browser zeigt Status: "Verbunden" ✅

**Server-Log:**
```
2025-11-25 15:50:01 - INFO - Client verbunden. Total clients: 1
```

---

#### Phase 2: Anruf starten (Peer A)

**Schritt 2:** User in Tab 1 klickt "Anruf starten"

**2.1 Media-Stream erfassen**
```javascript
// app.js - Zeile 169
this.localStream = await navigator.mediaDevices.getUserMedia({
    video: true,
    audio: true
});
```

**Fallback (keine Kamera):**
```javascript
// app.js - Zeile 180
const canvas = document.createElement('canvas');
// ... animiertes Dummy-Video erstellen
this.localStream = canvas.captureStream(25);
```

**2.2 PeerConnection erstellen**
```javascript
// app.js - Zeile 213
this.peerConnection = new RTCPeerConnection({
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' }
    ]
});
```

**2.3 ICE-Kandidaten sammeln (automatisch)**
```javascript
// app.js - Zeile 216
this.peerConnection.onicecandidate = (event) => {
    if (event.candidate) {
        this.handleIceCandidate(event.candidate);
    }
};
```

**Was der Browser macht:**
1. **Host-Kandidaten**: Sammelt lokale IP-Adressen
   ```
   candidate:... 192.168.1.100 54321 typ host
   ```

2. **STUN-Anfrage**: Sendet an Google STUN-Server
   ```
   Browser → stun.l.google.com:19302
   Antwort: "Deine öffentliche IP ist 203.0.113.5"
   ```

3. **srflx-Kandidat**: Öffentliche IP via STUN
   ```
   candidate:... 203.0.113.5 54321 typ srflx
   ```

4. **TURN-Kandidat** (falls konfiguriert):
   ```
   candidate:... 198.51.100.10 49170 typ relay
   ```

**2.4 SDP Offer erstellen**
```javascript
// app.js - Zeile 185
const offer = await this.peerConnection.createOffer();
await this.peerConnection.setLocalDescription(offer);
```

**SDP-Inhalt (Beispiel):**
```
v=0
o=- 1234567890 2 IN IP4 127.0.0.1
s=-
t=0 0
a=fingerprint:sha-256 8A:3B:C5:D7:E9:...
m=video 9 UDP/TLS/RTP/SAVPF 96
c=IN IP4 192.168.1.100
a=rtcp:9 IN IP4 192.168.1.100
...
```

**2.5 Offer über WebSocket senden**
```javascript
// app.js - Zeile 192
this.sendSignaling({
    type: 'offer',
    sdp: offer.sdp
});
```

**WebSocket-Nachricht:**
```json
{
  "type": "offer",
  "sdp": "v=0\r\no=- 1234567890..."
}
```

**Server empfängt und leitet weiter:**
```python
# signaling_server_aiohttp.py - Zeile 51
async for msg in ws:
    data = json.loads(msg.data)
    # Broadcasting an alle anderen Clients
    for client in self.clients:
        if client != ws:
            await client.send_str(msg.data)
```

---

#### Phase 3: Anruf annehmen (Peer B)

**Schritt 3:** Tab 2 empfängt Offer

**3.1 Offer verarbeiten**
```javascript
// app.js - Zeile 316
async handleOffer(sdp) {
    // Lokalen Stream erstellen (falls noch nicht vorhanden)
    this.localStream = await getUserMedia(...);
    
    // PeerConnection erstellen
    this.createPeerConnection();
    
    // Remote Description setzen
    await this.peerConnection.setRemoteDescription({
        type: 'offer',
        sdp: sdp
    });
}
```

**3.2 Answer erstellen**
```javascript
// app.js - Zeile 334
const answer = await this.peerConnection.createAnswer();
await this.peerConnection.setLocalDescription(answer);
```

**3.3 Answer zurücksenden**
```javascript
// app.js - Zeile 337
this.sendSignaling({
    type: 'answer',
    sdp: answer.sdp
});
```

**Server leitet Answer an Peer A:**
```
Peer B → Server → Peer A
```

---

#### Phase 4: ICE-Kandidaten austauschen

**Parallel zum SDP-Austausch:**

**Peer A sendet ICE-Kandidaten:**
```javascript
// app.js - Zeile 282
this.sendSignaling({
    type: 'ice-candidate',
    candidate: candidateStr,
    sdpMid: candidate.sdpMid
});
```

**Peer B empfängt ICE-Kandidaten:**
```javascript
// app.js - Zeile 351
async handleRemoteIceCandidate(candidate, sdpMid) {
    await this.peerConnection.addIceCandidate({
        candidate: candidate,
        sdpMid: sdpMid
    });
}
```

**ICE testet alle Kandidaten-Paare:**
```
Peer A (host) → Peer B (host)     ✅ Funktioniert? → P2P!
Peer A (srflx) → Peer B (srflx)   ⚠️ Falls P2P scheitert
Peer A (relay) → Peer B (relay)   🔴 Letzter Fallback
```

---

#### Phase 5: Verbindung etabliert

**DTLS-Handshake (automatisch):**
```
1. Peer A sendet ClientHello
2. Peer B sendet Certificate (self-signed)
3. Key Exchange (ECDHE)
4. Verschlüsselungsschlüssel abgeleitet
```

**Fingerprint-Verifikation:**
```javascript
// SDP enthält:
a=fingerprint:sha-256 8A:3B:C5:...

// Browser prüft:
if (receivedCertificateHash === sdpFingerprint) {
    // ✅ Verbindung authentifiziert
}
```

**SRTP-Media-Stream startet:**
```
Peer A → [AES-verschlüsselt] → Peer B
Peer B → [AES-verschlüsselt] → Peer A
```

**Status-Update:**
```javascript
// app.js - Zeile 233
this.peerConnection.onconnectionstatechange = () => {
    if (state === 'connected') {
        this.encryption.textContent = 'DTLS-SRTP ✅';
    }
};
```

---

## 4. Web-Interface Settings

### 4.1 mDNS aktivieren

**Checkbox:** `☑ mDNS aktivieren`

**Was es bewirkt:**
```javascript
// app.js - Zeile 92
this.enableMdnsCheckbox.addEventListener('change', (e) => {
    this.settings.enableMdns = e.target.checked;
});
```

**Effekt:**

**Ohne mDNS (☐):**
```
● HOST  192.168.1.100:54321
⚠️ RISIKO 2: Lokale IP-Adresse exponiert!
```

**Mit mDNS (☑):**
```
● HOST  a1b2c3d4-5e6f-7g8h-9i0j.local:54321
✅ IP verschleiert durch mDNS
```

**Wo es implementiert ist:**
```javascript
// app.js - Zeile 271
if (type === 'host' && !this.settings.enableMdns) {
    if (candidateStr.includes('192.168.') || candidateStr.includes('10.')) {
        this.addSecurityWarning('⚠️ RISIKO 2: Lokale IP-Adresse exponiert!');
    }
}
```

**Technisch:**
- Browser-Feature (automatisch in modernen Browsern)
- Ersetzt IP durch `.local`-Hostname
- Nur für host-Kandidaten
- **srflx bleibt sichtbar!**

---

### 4.2 Privacy Badger simulieren

**Checkbox:** `☐ Privacy Badger simulieren`

**Was es bewirkt:**
```javascript
// app.js - Zeile 101
this.privacyBadgerCheckbox.addEventListener('change', (e) => {
    this.settings.privacyBadger = e.target.checked;
});
```

**Effekt:**

**Ohne Privacy Badger (☐):**
```
✅ HOST-Kandidaten werden gesendet
✅ srflx-Kandidaten werden gesendet
✅ relay-Kandidaten werden gesendet
→ Verbindung: P2P (direkt)
```

**Mit Privacy Badger (☑):**
```
🚫 HOST-Kandidaten BLOCKIERT
🚫 srflx-Kandidaten BLOCKIERT
✅ relay-Kandidaten werden gesendet
→ Verbindung: TURN (Relay)
```

**Wo es implementiert ist:**
```javascript
// app.js - Zeile 260
if (this.settings.privacyBadger && (type === 'host' || type === 'srflx')) {
    this.addSecurityWarning(`🚫 Privacy Badger blockiert ${type}-Kandidat`);
    return; // ← Kandidat wird NICHT gesendet!
}
```

**Was passiert:**
1. Browser sammelt trotzdem alle Kandidaten
2. Unsere Simulation filtert host + srflx
3. Nur relay-Kandidaten werden an Peer gesendet
4. Result: Alle Daten via TURN-Server (langsamer)

---

### 4.3 TLS für Signalisierung

**Checkbox:** `☐ TLS für Signalisierung (wss://)`

**Was es bewirkt:**
```javascript
// app.js - Zeile 110
this.encryptedSignalingCheckbox.addEventListener('change', (e) => {
    this.settings.encryptedSignaling = e.target.checked;
    this.wsUrl = e.target.checked 
        ? 'wss://localhost:8443/ws'  // TLS-verschlüsselt
        : 'ws://localhost:8080/ws';  // Unverschlüsselt
});
```

**Effekt:**

**Ohne TLS (☐ ws://):**
```
WebSocket: ws://localhost:8080/ws
└─ Klartext
   └─ SDP-Fingerprints sichtbar
   └─ ICE-Kandidaten sichtbar
   └─ Wireshark kann alles lesen
```

**Mit TLS (☑ wss://):**
```
WebSocket: wss://localhost:8443/ws
└─ TLS 1.3 verschlüsselt
   └─ SDP-Fingerprints geschützt
   └─ ICE-Kandidaten geschützt
   └─ Wireshark sieht nur verschlüsselte Daten
```

**Sicherheitswarnung:**
```javascript
// app.js - Zeile 492
if (!this.settings.encryptedSignaling) {
    this.addSecurityWarning(
        '⚠️ Fingerprint über unverschlüsselten Kanal übertragen - MITM möglich!'
    );
}
```

**Hinweis:** In diesem Demo läuft nur `ws://` (kein TLS-Server implementiert)

---

## 5. Sicherheitsmaßnahmen im Code

### 5.1 IP-Leakage-Erkennung

**Datei:** `app.js` Zeile 246-280

```javascript
handleIceCandidate(candidate) {
    const candidateStr = candidate.candidate;
    
    // Typ erkennen
    let type = 'unknown';
    if (candidateStr.includes('typ host')) type = 'host';
    if (candidateStr.includes('typ srflx')) type = 'srflx';
    if (candidateStr.includes('typ relay')) type = 'relay';
    
    // Warnung bei host-IPs
    if (type === 'host' && !this.settings.enableMdns) {
        if (candidateStr.includes('192.168.') || 
            candidateStr.includes('10.')) {
            this.addSecurityWarning('⚠️ Lokale IP exponiert!');
        }
    }
    
    // Warnung bei srflx
    if (type === 'srflx') {
        this.addSecurityWarning('⚠️ Öffentliche IP exponiert!');
    }
}
```

**Erkannte Risiken:**
- Private IPs (192.168.x.x, 10.x.x.x)
- Öffentliche IPs via STUN
- Auch bei aktivem VPN!

---

### 5.2 Fingerprint-Überwachung

**Datei:** `app.js` Zeile 484-502

```javascript
logSdpSecurity(sdp) {
    // Prüfe auf Fingerprints in SDP
    if (sdp.includes('fingerprint')) {
        const match = sdp.match(/a=fingerprint:(\S+)\s+(\S+)/);
        if (match) {
            const [_, algo, hash] = match;
            this.log('signaling', `🔐 Fingerprint: ${algo} ${hash.substring(0, 20)}...`);
            
            // Warnung bei unverschlüsselter Übertragung
            if (!this.settings.encryptedSignaling) {
                this.addSecurityWarning(
                    '⚠️ Fingerprint über unverschlüsselten Kanal ' +
                    'übertragen - MITM möglich!'
                );
            }
        }
    }
}
```

**Was passiert:**
1. SDP wird geparst
2. Fingerprint extrahiert (SHA-256 Hash des DTLS-Zertifikats)
3. Warnung wenn ws:// statt wss://

---

### 5.3 Server-seitiges Logging

**Datei:** `signaling_server_aiohttp.py` Zeile 21-45

```python
def log_message(self, msg_type: str, data: dict):
    # SDP-Analysen
    if msg_type in ['offer', 'answer']:
        logger.warning(f"🔓 SDP {msg_type.upper()} übertragen!")
        if 'sdp' in data:
            sdp = data.get('sdp', '')
            if 'fingerprint' in sdp:
                logger.warning(f"   Fingerprint detected in SDP")
    
    # ICE-Kandidaten-Analyse
    elif msg_type == 'ice-candidate':
        candidate = data.get('candidate', '')
        if 'typ host' in candidate:
            logger.warning(f"   ⚠️  LOCAL IP exposed!")
        elif 'typ srflx' in candidate:
            logger.warning(f"   ⚠️  PUBLIC IP exposed!")
```

**Server-Log-Ausgabe:**
```
2025-11-25 15:50:20 - WARNING - 🔓 SDP OFFER übertragen!
2025-11-25 15:50:20 - WARNING -    Fingerprint detected in SDP
2025-11-25 15:50:21 - INFO - 🌐 ICE Candidate: candidate:842163049...
2025-11-25 15:50:21 - WARNING -    ⚠️  LOCAL IP exposed!
```

---

### 5.4 TURN-Server-Warnung

**Datei:** `app.js` Zeile 383-387

```javascript
if (type === 'relay') {
    this.connType.textContent = 'TURN (Relay)';
    this.connType.style.color = '#e74c3c'; // Rot
    this.addSecurityWarning(
        '⚠️ RISIKO 3: TURN-Server leitet alle Medien weiter - ' +
        'potentieller Angriffspunkt!'
    );
}
```

**Angezeigt wenn:**
- Privacy Badger aktiviert
- P2P-Verbindung fehlschlägt
- Firewall blockiert direkte Verbindung

---

## 6. Praktische Beispiele

### Beispiel 1: Normale P2P-Verbindung

**Einstellungen:**
- ☑ mDNS aktivieren
- ☐ Privacy Badger
- ☐ TLS

**Datenfluss:**
```
1. Tab 1: "Anruf starten" → getUserMedia() → Stream ✅
2. Tab 1: createOffer() → SDP generiert
3. Tab 1 → WebSocket → Server → Tab 2 (SDP Offer)
4. Tab 2: createAnswer() → SDP generiert
5. Tab 2 → WebSocket → Server → Tab 1 (SDP Answer)
6. Parallel: ICE sammelt Kandidaten
   - HOST: a1b2c3d4.local:54321 (mDNS)
   - SRFLX: 203.0.113.5:54321 (STUN)
7. ICE testet: host↔host funktioniert! ✅
8. DTLS-Handshake: Verschlüsselung aufgebaut ✅
9. SRTP-Media: Video/Audio-Stream läuft ✅
```

**Result:**
- Verbindungstyp: **Direkt (P2P)** 🟢
- Latenz: Niedrig (~5-15ms)
- Warnungen: Öffentliche IP exponiert

---

### Beispiel 2: Privacy Badger aktiviert

**Einstellungen:**
- ☑ mDNS aktivieren
- ☑ Privacy Badger simulieren
- ☐ TLS

**Datenfluss:**
```
1. Tab 1: "Anruf starten" → Stream ✅
2. ICE sammelt Kandidaten:
   - HOST: gesammelt aber BLOCKIERT 🚫
   - SRFLX: gesammelt aber BLOCKIERT 🚫
   - RELAY: gesammelt und GESENDET ✅
3. Tab 1 → Server → Tab 2 (nur relay-Kandidaten)
4. ICE testet: Nur relay↔relay möglich
5. DTLS über TURN-Server
6. SRTP via TURN-Server (alle Daten)
```

**Result:**
- Verbindungstyp: **TURN (Relay)** 🔴
- Latenz: Höher (>50ms)
- Warnungen: TURN-Server als Angriffspunkt

---

### Beispiel 3: Wireshark-Analyse

**Ohne TLS:**
```bash
# Terminal
wireshark -i lo -f "port 8080"
```

**Filter:** `websocket`

**Was Sie sehen:**
```
Frame 1: WebSocket Handshake
Frame 2: TEXT (Offer)
    Data: {"type":"offer","sdp":"v=0...
          a=fingerprint:sha-256 8A:3B:C5:D7..."}
Frame 3: TEXT (ICE Candidate)
    Data: {"type":"ice-candidate",
           "candidate":"...192.168.1.100..."}
```

**Mit TLS (wss://):**
```
Frame 1: TLS Handshake
Frame 2: Application Data [encrypted]
Frame 3: Application Data [encrypted]
```

---

## 📊 Zusammenfassung

### Komponenten

| Komponente | Aufgabe | Port |
|-----------|---------|------|
| **HTTP-Server** | Statische Dateien | 8000 |
| **Signaling-Server** | WebSocket-Relay | 8080 |
| **Browser-Client** | WebRTC-Logik | - |
| **STUN-Server** | IP-Discovery | 19302 |
| **TURN-Server** | Relay (Optional) | 80/443 |

### Settings-Effekte

| Setting | Aus (☐) | An (☑) |
|---------|---------|--------|
| **mDNS** | IPs sichtbar | `.local` Hostnamen |
| **Privacy Badger** | P2P möglich | Nur via TURN |
| **TLS** | Klartext | Verschlüsselt |

### Sicherheitsmaßnahmen

| Maßnahme | Datei | Zeile |
|----------|-------|-------|
| IP-Leakage-Warnung | app.js | 271-279 |
| Fingerprint-Check | app.js | 484-502 |
| Privacy-Badger-Filter | app.js | 260-264 |
| Server-Logging | signaling_server_aiohttp.py | 21-45 |
| TURN-Warnung | app.js | 383-387 |

---

**Das System demonstriert erfolgreich alle drei Haupt-Sicherheitsrisiken von WebRTC!** 🎯
