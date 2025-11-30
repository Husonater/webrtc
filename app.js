/**
 * WebRTC Security Lab - Client-seitige Logik
 * Demonstriert Sicherheitsrisiken und verschiedene ICE-Kandidaten-Typen
 */

class WebRTCSecurityLab {
    constructor() {
        // WebSocket-Verbindung
        this.ws = null;
        this.wsUrl = 'ws://localhost:8080/ws';

        // WebRTC
        this.peerConnection = null;
        this.localStream = null;

        // Konfiguration
        this.config = {
            iceServers: [
                // Öffentlicher Google STUN-Server (für srflx-Kandidaten)
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' },
                // Öffentlicher TURN-Server (Demo) - Credentials sind public
                // ACHTUNG: In Produktion eigene TURN-Server verwenden!
                {
                    urls: 'turn:openrelay.metered.ca:80',
                    username: 'openrelayproject',
                    credential: 'openrelayproject'
                }
            ]
        };

        // Sicherheitseinstellungen
        this.settings = {
            enableMdns: true,
            privacyBadger: false,
            encryptedSignaling: false
        };

        // Tracking
        this.iceCandidates = {
            host: [],
            srflx: [],
            relay: []
        };
        this.securityWarnings = [];

        this.init();
    }

    init() {
        this.bindElements();
        this.attachEventListeners();
        this.log('signaling', 'Anwendung initialisiert');
    }

    bindElements() {
        // Buttons
        this.connectBtn = document.getElementById('connectBtn');
        this.startCallBtn = document.getElementById('startCallBtn');
        this.hangupBtn = document.getElementById('hangupBtn');

        // Status
        this.connectionStatus = document.getElementById('connectionStatus');

        // Checkboxen
        this.enableMdnsCheckbox = document.getElementById('enableMdns');
        this.privacyBadgerCheckbox = document.getElementById('privacyBadger');
        this.encryptedSignalingCheckbox = document.getElementById('encryptedSignaling');

        // Videos
        this.localVideo = document.getElementById('localVideo');
        this.remoteVideo = document.getElementById('remoteVideo');

        // Log-Bereiche
        this.iceCandidatesLog = document.getElementById('iceCandidates');
        this.securityWarningsLog = document.getElementById('securityWarnings');
        this.signalingLog = document.getElementById('signalingLog');

        // Stats
        this.connType = document.getElementById('connType');
        this.localIp = document.getElementById('localIp');
        this.remoteIp = document.getElementById('remoteIp');
        this.encryption = document.getElementById('encryption');
    }

    attachEventListeners() {
        this.connectBtn.addEventListener('click', () => this.connectToSignaling());
        this.startCallBtn.addEventListener('click', () => this.startCall());
        this.hangupBtn.addEventListener('click', () => this.hangup());

        // Einstellungen
        this.enableMdnsCheckbox.addEventListener('change', (e) => {
            this.settings.enableMdns = e.target.checked;
            this.addSecurityWarning(
                e.target.checked
                    ? 'mDNS aktiviert - Lokale IPs werden verschleiert'
                    : '⚠️ mDNS deaktiviert - Lokale IPs werden exponiert!'
            );
        });

        this.privacyBadgerCheckbox.addEventListener('change', (e) => {
            this.settings.privacyBadger = e.target.checked;
            this.addSecurityWarning(
                e.target.checked
                    ? 'Privacy Badger simuliert - ICE-Kandidaten werden gefiltert'
                    : 'Privacy Badger deaktiviert'
            );
        });

        this.encryptedSignalingCheckbox.addEventListener('change', (e) => {
            this.settings.encryptedSignaling = e.target.checked;
            this.wsUrl = e.target.checked ? 'wss://localhost:8443/ws' : 'ws://localhost:8080/ws';
            this.addSecurityWarning(
                e.target.checked
                    ? 'Verschlüsselte Signalisierung aktiviert (WSS)'
                    : '⚠️ Unverschlüsselte Signalisierung (WS) - Fingerprints können abgefangen werden!'
            );
        });
    }

    // WebSocket-Verbindung
    connectToSignaling() {
        this.updateStatus('connecting');
        this.log('signaling', `Verbinde zu ${this.wsUrl}...`);

        try {
            this.ws = new WebSocket(this.wsUrl);

            this.ws.onopen = () => {
                this.updateStatus('connected');
                this.log('signaling', '✅ Mit Signalisierungsserver verbunden');
                this.startCallBtn.disabled = false;
                this.connectBtn.disabled = true;

                if (!this.settings.encryptedSignaling) {
                    this.addSecurityWarning('⚠️ RISIKO 1: Unverschlüsselte Signalisierung - SDP-Fingerprints können abgefangen werden!');
                }
            };

            this.ws.onmessage = (event) => {
                this.handleSignalingMessage(JSON.parse(event.data));
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.log('signaling', '❌ Verbindungsfehler');
                this.updateStatus('disconnected');
            };

            this.ws.onclose = () => {
                this.log('signaling', 'Verbindung zum Server geschlossen');
                this.updateStatus('disconnected');
                this.connectBtn.disabled = false;
                this.startCallBtn.disabled = true;
            };

        } catch (error) {
            console.error('Connection error:', error);
            this.updateStatus('disconnected');
        }
    }

    async startCall() {
        this.log('signaling', 'Starte WebRTC-Verbindung...');

        try {
            // Versuche echte Medien zu bekommen
            try {
                this.localStream = await navigator.mediaDevices.getUserMedia({
                    video: true,
                    audio: true
                });
            } catch (mediaError) {
                // Fallback: Erstelle Dummy-Video (Canvas-basiert)
                this.log('signaling', '⚠️ Keine Kamera gefunden - verwende Dummy-Video');
                this.addSecurityWarning('ℹ️ Keine Kamera verfügbar - Demo läuft mit Dummy-Video');

                // Erstelle Canvas mit animiertem Inhalt
                const canvas = document.createElement('canvas');
                canvas.width = 640;
                canvas.height = 480;
                const ctx = canvas.getContext('2d');

                // Animation
                let hue = 0;
                setInterval(() => {
                    hue = (hue + 1) % 360;
                    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
                    gradient.addColorStop(0, `hsl(${hue}, 70%, 50%)`);
                    gradient.addColorStop(1, `hsl(${(hue + 60) % 360}, 70%, 50%)`);
                    ctx.fillStyle = gradient;
                    ctx.fillRect(0, 0, canvas.width, canvas.height);

                    // Text
                    ctx.fillStyle = 'white';
                    ctx.font = 'bold 24px Arial';
                    ctx.textAlign = 'center';
                    ctx.fillText('WebRTC Security Lab', canvas.width / 2, canvas.height / 2 - 20);
                    ctx.font = '18px Arial';
                    ctx.fillText('Dummy Video (Keine Kamera verfügbar)', canvas.width / 2, canvas.height / 2 + 20);
                    ctx.fillText(new Date().toLocaleTimeString(), canvas.width / 2, canvas.height / 2 + 50);
                }, 100);

                // Canvas zu MediaStream
                this.localStream = canvas.captureStream(25); // 25 FPS
            }

            this.localVideo.srcObject = this.localStream;
            this.log('signaling', '✅ Lokaler Media-Stream erfasst');

            // PeerConnection erstellen
            this.createPeerConnection();

            // Media-Tracks hinzufügen
            this.localStream.getTracks().forEach(track => {
                this.peerConnection.addTrack(track, this.localStream);
            });

            // Offer erstellen
            const offer = await this.peerConnection.createOffer();
            await this.peerConnection.setLocalDescription(offer);

            this.log('signaling', '📤 Sende SDP Offer');
            this.logSdpSecurity(offer.sdp);

            // Offer über Signalisierung senden
            this.sendSignaling({
                type: 'offer',
                sdp: offer.sdp
            });

            this.startCallBtn.disabled = true;
            this.hangupBtn.disabled = false;

        } catch (error) {
            console.error('Error starting call:', error);
            this.log('signaling', `❌ Fehler: ${error.message}`);
        }
    }

    createPeerConnection() {
        // mDNS-Konfiguration
        const config = { ...this.config };

        // Hinweis: Browser-APIs für mDNS sind limitiert
        // In echten Browsern wird mDNS automatisch angewendet

        this.peerConnection = new RTCPeerConnection(config);

        // ICE-Kandidaten-Handler
        this.peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.handleIceCandidate(event.candidate);
            }
        };

        // Remote-Stream-Handler
        this.peerConnection.ontrack = (event) => {
            this.log('signaling', '✅ Remote-Stream empfangen');
            this.remoteVideo.srcObject = event.streams[0];
        };

        // Verbindungsstatus
        this.peerConnection.onconnectionstatechange = () => {
            const state = this.peerConnection.connectionState;
            this.log('signaling', `Verbindungsstatus: ${state}`);

            if (state === 'connected') {
                this.updateConnectionStats();
                this.encryption.textContent = 'DTLS-SRTP ✅';
            }
        };

        // ICE-Verbindungsstatus
        this.peerConnection.oniceconnectionstatechange = () => {
            const state = this.peerConnection.iceConnectionState;
            this.log('signaling', `ICE-Status: ${state}`);
        };
    }

    handleIceCandidate(candidate) {
        const candidateStr = candidate.candidate;

        // Kandidaten-Typ bestimmen
        let type = 'unknown';
        if (candidateStr.includes('typ host')) {
            type = 'host';
        } else if (candidateStr.includes('typ srflx')) {
            type = 'srflx';
        } else if (candidateStr.includes('typ relay')) {
            type = 'relay';
        }

        // Privacy Badger-Simulation
        if (this.settings.privacyBadger && (type === 'host' || type === 'srflx')) {
            this.addSecurityWarning(`🚫 Privacy Badger blockiert ${type}-Kandidat`);
            this.log('ice', `🚫 BLOCKIERT (Privacy Badger): ${type.toUpperCase()}`);
            return; // Kandidat nicht senden
        }

        // Speichern und anzeigen
        this.iceCandidates[type].push(candidateStr);
        this.displayIceCandidate(type, candidateStr);

        // Sicherheitswarnungen
        if (type === 'host' && !this.settings.enableMdns) {
            if (candidateStr.includes('192.168.') || candidateStr.includes('10.')) {
                this.addSecurityWarning('⚠️ RISIKO 2: Lokale IP-Adresse exponiert!');
            }
        }

        if (type === 'srflx') {
            this.addSecurityWarning('⚠️ RISIKO 2: Öffentliche IP-Adresse exponiert (auch bei aktivem VPN!)');
        }

        // An Peer senden
        this.sendSignaling({
            type: 'ice-candidate',
            candidate: candidateStr,
            sdpMid: candidate.sdpMid,
            sdpMLineIndex: candidate.sdpMLineIndex
        });
    }

    async handleSignalingMessage(message) {
        const { type, sdp, candidate, sdpMid, sdpMLineIndex } = message;

        this.log('signaling', `📥 Empfangen: ${type}`);

        switch (type) {
            case 'welcome':
                this.log('signaling', `Server-Modus: ${message.encrypted ? 'Verschlüsselt' : 'Unverschlüsselt'}`);
                break;

            case 'offer':
                this.logSdpSecurity(sdp);
                await this.handleOffer(sdp);
                break;

            case 'answer':
                this.logSdpSecurity(sdp);
                await this.handleAnswer(sdp);
                break;

            case 'ice-candidate':
                await this.handleRemoteIceCandidate(candidate, sdpMid, sdpMLineIndex);
                break;
        }
    }

    async handleOffer(sdp) {
        if (!this.peerConnection) {
            // Lokale Medien abrufen
            this.localStream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: true
            });
            this.localVideo.srcObject = this.localStream;

            this.createPeerConnection();

            this.localStream.getTracks().forEach(track => {
                this.peerConnection.addTrack(track, this.localStream);
            });
        }

        await this.peerConnection.setRemoteDescription({ type: 'offer', sdp });

        const answer = await this.peerConnection.createAnswer();
        await this.peerConnection.setLocalDescription(answer);

        this.sendSignaling({
            type: 'answer',
            sdp: answer.sdp
        });

        this.log('signaling', '📤 Sende SDP Answer');
        this.hangupBtn.disabled = false;
    }

    async handleAnswer(sdp) {
        await this.peerConnection.setRemoteDescription({ type: 'answer', sdp });
        this.log('signaling', '✅ Answer empfangen und gesetzt');
    }

    async handleRemoteIceCandidate(candidate, sdpMid, sdpMLineIndex) {
        try {
            await this.peerConnection.addIceCandidate({
                candidate,
                sdpMid,
                sdpMLineIndex
            });
            this.log('ice', `✅ Remote ICE-Kandidat hinzugefügt`);
        } catch (error) {
            console.error('Error adding ICE candidate:', error);
        }
    }

    async updateConnectionStats() {
        if (!this.peerConnection) return;

        const stats = await this.peerConnection.getStats();

        stats.forEach(report => {
            if (report.type === 'candidate-pair' && report.state === 'succeeded') {
                // Ermittle aktives Kandidaten-Paar
                stats.forEach(candidate => {
                    if (candidate.id === report.localCandidateId) {
                        this.localIp.textContent = `${candidate.ip || candidate.address}:${candidate.port}`;

                        const type = candidate.candidateType;
                        if (type === 'host') {
                            this.connType.textContent = 'Direkt (P2P)';
                            this.connType.style.color = '#27ae60';
                        } else if (type === 'srflx') {
                            this.connType.textContent = 'STUN (NAT Traversal)';
                            this.connType.style.color = '#f39c12';
                        } else if (type === 'relay') {
                            this.connType.textContent = 'TURN (Relay)';
                            this.connType.style.color = '#e74c3c';
                            this.addSecurityWarning('⚠️ RISIKO 3: TURN-Server leitet alle Medien weiter - potentieller Angriffspunkt!');
                        }
                    }

                    if (candidate.id === report.remoteCandidateId) {
                        this.remoteIp.textContent = `${candidate.ip || candidate.address}:${candidate.port}`;
                    }
                });
            }
        });
    }

    sendSignaling(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    hangup() {
        this.log('signaling', 'Verbindung wird beendet...');

        if (this.peerConnection) {
            this.peerConnection.close();
            this.peerConnection = null;
        }

        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
            this.localStream = null;
        }

        this.localVideo.srcObject = null;
        this.remoteVideo.srcObject = null;

        this.startCallBtn.disabled = false;
        this.hangupBtn.disabled = true;

        // Reset stats
        this.connType.textContent = '-';
        this.localIp.textContent = '-';
        this.remoteIp.textContent = '-';
        this.encryption.textContent = '-';

        this.log('signaling', '✅ Verbindung beendet');
    }

    // UI-Hilfsfunktionen
    updateStatus(status) {
        this.connectionStatus.className = `status ${status}`;
        const statusText = {
            'disconnected': 'Getrennt',
            'connecting': 'Verbindet...',
            'connected': 'Verbunden'
        };
        this.connectionStatus.textContent = statusText[status] || status;
    }

    log(category, message) {
        const timestamp = new Date().toLocaleTimeString('de-DE');
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.textContent = `[${timestamp}] ${message}`;

        this.signalingLog.appendChild(logEntry);
        this.signalingLog.scrollTop = this.signalingLog.scrollHeight;
    }

    displayIceCandidate(type, candidate) {
        const entry = document.createElement('div');
        entry.className = 'log-entry';

        const badge = document.createElement('span');
        badge.className = `badge ${type}`;
        badge.textContent = type.toUpperCase();

        const text = document.createTextNode(` ${candidate.substring(0, 60)}...`);

        entry.appendChild(badge);
        entry.appendChild(text);

        this.iceCandidatesLog.appendChild(entry);
        this.iceCandidatesLog.scrollTop = this.iceCandidatesLog.scrollHeight;
    }

    addSecurityWarning(message) {
        const entry = document.createElement('div');
        entry.className = 'log-entry danger';
        entry.textContent = message;

        this.securityWarningsLog.appendChild(entry);
        this.securityWarningsLog.scrollTop = this.securityWarningsLog.scrollHeight;

        this.securityWarnings.push({
            timestamp: new Date().toISOString(),
            message
        });
    }

    logSdpSecurity(sdp) {
        // Prüfe auf Fingerprints
        if (sdp.includes('fingerprint')) {
            const fingerprintMatch = sdp.match(/a=fingerprint:(\S+)\s+(\S+)/);
            if (fingerprintMatch) {
                const [_, algo, hash] = fingerprintMatch;
                this.log('signaling', `🔐 Fingerprint: ${algo} ${hash.substring(0, 20)}...`);

                if (!this.settings.encryptedSignaling) {
                    this.addSecurityWarning('⚠️ Fingerprint über unverschlüsselten Kanal übertragen - MITM möglich!');
                }
            }
        }

        // Prüfe auf Verschlüsselung-Profile
        if (sdp.includes('SRTP')) {
            this.log('signaling', '✅ SRTP-Verschlüsselung konfiguriert');
        }
    }
}

// Initialisierung
document.addEventListener('DOMContentLoaded', () => {
    window.lab = new WebRTCSecurityLab();
});
