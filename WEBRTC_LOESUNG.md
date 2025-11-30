# WebRTC Laborbericht und Technologie-Analyse

## Einleitung

Dieses Dokument beschreibt die Funktionsweise von WebRTC (Web Real-Time Communication), analysiert dessen Sicherheitsarchitektur und dokumentiert die Ergebnisse des durchgeführten Sicherheitslabors. Es dient als Lösung für die gestellten Aufgaben zur Funktionalität und Sicherheit von WebRTC.

---

## Aufgabe 1: WebRTC Architektur und Funktionsweise

WebRTC ermöglicht Echtzeitkommunikation (Audio, Video, Daten) direkt zwischen Browsern (Peer-to-Peer), ohne dass Plugins installiert werden müssen. Da Browser jedoch oft hinter NAT-Routern (Network Address Translation) und Firewalls sitzen, ist ein komplexer Verbindungsaufbau notwendig.

### Architektur-Diagramm (Beschreibung)

Der Aufbau lässt sich wie folgt visualisieren:

```mermaid
sequenceDiagram
    participant Alice as Browser A (Alice)
    participant Sig as Signalisierungsserver
    participant STUN as STUN-Server
    participant TURN as TURN-Server
    participant Bob as Browser B (Bob)

    Note over Alice, Bob: 1. Signalisierung (über WebSocket/HTTPS)
    Alice->>Sig: Sende SDP Offer (Codecs, Verschlüsselung, ICE-Daten)
    Sig->>Bob: Leite SDP Offer weiter
    Bob->>Sig: Sende SDP Answer
    Sig->>Alice: Leite SDP Answer weiter

    Note over Alice, Bob: 2. ICE Candidate Gathering (Parallel)
    Alice->>STUN: Wer bin ich? (Binding Request)
    STUN-->>Alice: Deine öffentliche IP:Port (srflx candidate)
    Alice->>Sig: Sende ICE Candidates (Host, Srflx, Relay)
    Sig->>Bob: Leite Candidates weiter

    Note over Alice, Bob: 3. P2P Verbindung (DTLS-SRTP)
    Alice<-->>Bob: Direkter Medienfluss (Audio/Video)
    
    Note over Alice, Bob: Falls P2P blockiert (Symmetrisches NAT/Firewall):
    Alice<-->>TURN: Medien Relay
    TURN<-->>Bob: Medien Relay
```

### Begriffserklärungen

#### a) Signalisierung

WebRTC definiert **nicht**, wie Peers sich finden. Dieser Prozess heißt Signalisierung.

- **Funktion:** Austausch von Metadaten (Session Description Protocol - SDP), um eine Verbindung auszuhandeln.
- **Inhalt:** Welche Codecs werden unterstützt? Welche Verschlüsselung wird genutzt? Wie lauten die IP-Adressen (ICE Candidates)?
- **Umsetzung:** Im Labor erfolgt dies über einen Python-WebSocket-Server (`signaling_server.py`). In der Praxis oft HTTPS/WSS.
- **Sicherheitsaspekt:** Da SDP auch die Fingerprints der DTLS-Zertifikate enthält, muss dieser Kanal verschlüsselt sein (HTTPS/WSS), um Man-in-the-Middle-Angriffe (MITM) zu verhindern.

#### b) ICE (Interactive Connectivity Establishment)

ICE ist das Framework, das versucht, den besten Pfad zwischen zwei Peers zu finden. Es sammelt verschiedene "Kandidaten" (mögliche Endpunkte):

1. **Host Candidates:** Die lokale IP-Adresse des Geräts (z.B. `192.168.1.5` oder `10.0.0.2`).
    - *Risiko:* Verrät die interne Netzwerkstruktur.
2. **Srflx Candidates (Server Reflexive):** Die öffentliche IP-Adresse, wie sie vom NAT-Router nach außen sichtbar ist. Ermittelt durch STUN.
    - *Risiko:* Verrät den Standort des Nutzers (Geo-IP).
3. **Relay Candidates:** Die IP-Adresse eines TURN-Servers, der Daten weiterleitet.
    - *Vorteil:* Verbirgt die echte IP des Nutzers.

#### c) STUN / TURN

- **STUN (Session Traversal Utilities for NAT):** Ein leichtgewichtiger Server, der dem Browser sagt: "Deine öffentliche IP ist X und Port Y". Er hilft beim NAT-Traversal, leitet aber keine Medien weiter.
- **TURN (Traversal Using Relays around NAT):** Ein Relay-Server. Wenn keine direkte P2P-Verbindung möglich ist (z.B. strikte Firewalls oder symmetrisches NAT), leitet der TURN-Server den gesamten Traffic weiter. Er benötigt Authentifizierung und Bandbreite.

#### d) Verschlüsselung (DTLS, SRTP)

WebRTC erzwingt Verschlüsselung für Medienströme.

- **DTLS (Datagram Transport Layer Security):** Wird für den Schlüsselaustausch genutzt (ähnlich wie TLS für HTTPS, aber über UDP). Es stellt sicher, dass wir mit dem richtigen Peer sprechen (Authentifizierung über Fingerprints im SDP).
- **SRTP (Secure Real-time Transport Protocol):** Das eigentliche Protokoll für Audio/Video. Die Schlüssel für SRTP werden über den DTLS-Handshake ausgehandelt.

#### e) Namensauflösung mit mDNS

Um das "Host Candidate"-Leck (Verrat der lokalen IP) zu schließen, wurde mDNS (Multicast DNS) eingeführt.

- **Funktion:** Statt `192.168.1.5` sendet der Browser eine zufällige UUID wie `a1b2c3d4.local`.
- **Ablauf:** Wenn der andere Peer im selben lokalen Netzwerk ist, kann er diesen Namen per Multicast auflösen. Wenn nicht, ist die lokale IP irrelevant und wird nicht verraten.

---

## Aufgabe 2: Sicherheitsrisiken und Labor-Demonstration

Im Labor (Browser + Python Server) demonstrieren wir drei typische Risiken:

1. **IP-Leakage (Privatsphäre):** WebRTC kann lokale und öffentliche IPs verraten, selbst wenn ein VPN genutzt wird.
2. **Unverschlüsselte Signalisierung:** Angreifer können Metadaten mitlesen oder manipulieren.
3. **Fingerprinting/Tracking:** Die Kombination aus lokalen IPs und Gerätefähigkeiten erlaubt Browser-Fingerprinting.

### a) Analyse des Nachrichtenflusses (Verschlüsselung)

Der Signalisierungsserver (`signaling_server.py`) leitet Nachrichten zwischen den Peers weiter.

#### Ohne Verschlüsselung (WebSocket `ws://`)

Im Labor ist dies der Standardmodus.

- **Beobachtung:** Ein Angreifer im Netzwerk (oder der Admin des Signalisierungsservers) kann den gesamten Traffic im Klartext lesen.
- **Gefahr:** Die SDP-Nachrichten enthalten die **DTLS-Fingerprints**.
  - *Code-Beispiel (`signaling_server.py`):*

        ```python
        if 'fingerprint' in sdp:
            logger.warning(f"   Fingerprint detected in SDP")
        ```

  - Ein aktiver Angreifer könnte die Fingerprints im SDP austauschen (Man-in-the-Middle) und sich so in die verschlüsselte Medienverbindung einschleusen, ohne dass die Browser dies bemerken (da sie dem Signalisierungskanal vertrauen).

#### Mit Verschlüsselung (WebSocket Secure `wss://`)

Im Labor aktivierbar über die Checkbox "TLS für Signalisierung".

- **Ablauf:** Der Browser baut einen TLS-Tunnel zum Server auf.
- **Schutz:** Der Inhalt (SDP, Candidates) ist für Dritte nicht lesbar. Die Integrität der Fingerprints ist gesichert.

### b) Analyse des Nachrichtenflusses (Privacy Badger / IP-Schutz)

WebRTC sammelt standardmäßig alle verfügbaren Netzwerk-Interfaces.

#### Ohne Privacy Badger (Standard)

- **Ablauf:** Der Browser fragt das Betriebssystem nach lokalen IPs und den STUN-Server nach der öffentlichen IP.
- **Labor-Beobachtung:** Im Log (`app.js` Logik) erscheinen Einträge wie:
  - `candidate:... typ host ... 192.168.x.x` (Lokale IP)
  - `candidate:... typ srflx ... 84.12.x.x` (Öffentliche IP)
- **Risiko:** Webseiten können so echte IP-Adressen von VPN-Nutzern ermitteln.

#### Mit Privacy Badger (Simuliert)

Im Labor simuliert die Checkbox "Privacy Badger" das Verhalten von datenschutzfreundlichen Browser-Erweiterungen oder Modi.

- **Funktionsweise:** Die Erweiterung greift in die WebRTC-API ein und filtert bestimmte Kandidaten.
- **Code-Logik (`app.js`):**

    ```javascript
    if (this.settings.privacyBadger && (type === 'host' || type === 'srflx')) {
        // Blockiere Kandidat
        return; 
    }
    ```

- **Ergebnis:** Es werden **keine** Host- oder Srflx-Kandidaten an den Server gesendet. Nur Relay-Kandidaten (über TURN) wären erlaubt (falls konfiguriert), da diese die IP des Nutzers verschleiern. Die direkte P2P-Verbindung wird geopfert zugunsten der Privatsphäre.

---

## Aufgabe 3: WebRTC im Unternehmensnetzwerk absichern

Um WebRTC in Unternehmen sicher zu nutzen und unkontrollierten Datenabfluss zu verhindern, sind folgende Maßnahmen notwendig:

1. **Erzwingen von TURN (Force Relay):**
    - Über Gruppenrichtlinien (GPO) in Browsern (Chrome/Edge) kann WebRTC so konfiguriert werden, dass **nur** Relay-Kandidaten genutzt werden (`WebRtcIPHandlingPolicy`).
    - Dies verhindert, dass interne IP-Adressen nach außen gelangen und zwingt den Traffic über kontrollierte Server.

2. **Enterprise Firewall & Proxy:**
    - Blockieren von direktem UDP-Traffic auf nicht-standard Ports.
    - Freigabe nur für den offiziellen TURN-Server des Unternehmens (meist Port 443 TCP/UDP oder 3478).
    - Deep Packet Inspection (DPI) ist bei WebRTC (SRTP) schwierig, daher ist die Kontrolle der Endpunkte (Signalisierungsserver) entscheidend.

3. **Eigener Signalisierungs- und TURN-Server:**
    - Nutzung von On-Premise Lösungen (z.B. Jitsi, BigBlueButton) statt öffentlicher Cloud-Dienste.
    - Damit bleiben Metadaten und Medienströme im eigenen Rechenzentrum.

4. **Verschlüsselung erzwingen:**
    - Sicherstellen, dass der Signalisierungsserver nur TLS 1.2/1.3 akzeptiert.

---

## Quellenverzeichnis

1.  
<!-- @import "[TOC]" {cmd="toc" depthFrom=1 depthTo=6 orderedList=false} -->
**RFC 5245:** Interactive Connectivity Establishment (ICE)
2.  **RFC 5389:** Session Traversal Utilities for NAT (STUN)
3.  **RFC 5766:** Traversal Using Relays around NAT (TURN)
4.  **RFC 8826:** Security Considerations for WebRTC
5.  **IETF Draft:** mDNS as a candidate type for WebRTC
