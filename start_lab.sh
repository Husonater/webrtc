#!/bin/bash
# WebRTC Security Lab - Master-Starter
# Startet Signaling-Server, HTTP-Server und öffnet Browser

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Banner
echo -e "${PURPLE}"
echo "================================================="
echo "    🔒 WebRTC Security Lab"
echo "    Sicherheits-Demonstrationsumgebung"
echo "================================================="
echo -e "${NC}"

# Verzeichnis wechseln
cd "$(dirname "$0")"

# Cleanup-Funktion
cleanup() {
    echo -e "\n${YELLOW}Stoppe Server...${NC}"
    if [ ! -z "$SIGNALING_PID" ]; then
        kill $SIGNALING_PID 2>/dev/null || true
    fi
    if [ ! -z "$HTTP_PID" ]; then
        kill $HTTP_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}Labor gestoppt.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Prüfe Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 nicht gefunden!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python 3: $(python3 --version)${NC}\n"

# Prüfe Dependencies
echo -e "${BLUE}📦 Prüfe Dependencies...${NC}"

if python3 -c "import aiohttp" 2>/dev/null; then
    echo -e "${GREEN}✅ aiohttp-Modul gefunden (WebSocket-Unterstützung)${NC}"
    SIGNALING_SERVER="signaling_server_aiohttp.py"
elif python3 -c "import websockets" 2>/dev/null; then
    echo -e "${GREEN}✅ websockets-Modul gefunden${NC}"
    SIGNALING_SERVER="signaling_server.py"
else
    echo -e "${YELLOW}⚠️  Keine WebSocket-Module gefunden${NC}"
    echo -e "${YELLOW}   Verwende Standard-Library Version (Voll funktionsfähig)${NC}"
    SIGNALING_SERVER="signaling_server_stdlib.py"
fi

echo ""

# Starte Signaling Server im Hintergrund
echo -e "${BLUE}🚀 Starte Signaling Server...${NC}"
python3 $SIGNALING_SERVER > /tmp/webrtc-signaling.log 2>&1 &
SIGNALING_PID=$!

# Warte kurz
sleep 1

# Prüfe ob Signaling Server läuft
if ! kill -0 $SIGNALING_PID 2>/dev/null; then
    echo -e "${RED}❌ Signaling Server konnte nicht gestartet werden${NC}"
    echo -e "${YELLOW}Log-Ausgabe:${NC}"
    cat /tmp/webrtc-signaling.log
    exit 1
fi

echo -e "${GREEN}✅ Signaling Server läuft (PID: $SIGNALING_PID)${NC}"
echo -e "   URL: ws://localhost:8080"
echo -e "   Log: /tmp/webrtc-signaling.log"
echo ""

# Starte HTTP Server im Hintergrund
echo -e "${BLUE}🌐 Starte HTTP Server...${NC}"
python3 -m http.server 8000 > /tmp/webrtc-http.log 2>&1 &
HTTP_PID=$!

# Warte kurz
sleep 1

# Prüfe ob HTTP Server läuft
if ! kill -0 $HTTP_PID 2>/dev/null; then
    echo -e "${RED}❌ HTTP Server konnte nicht gestartet werden${NC}"
    echo -e "${YELLOW}Mögliche Ursache: Port 8000 bereits belegt${NC}"
    cleanup
    exit 1
fi

echo -e "${GREEN}✅ HTTP Server läuft (PID: $HTTP_PID)${NC}"
echo -e "   URL: http://localhost:8000"
echo -e "   Log: /tmp/webrtc-http.log"
echo ""

# Öffne Browser (falls möglich)
echo -e "${BLUE}🌍 Öffne Browser...${NC}"

BROWSER_OPENED=false

# Versuche Browser zu öffnen
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:8000" 2>/dev/null &
    BROWSER_OPENED=true
elif command -v firefox &> /dev/null; then
    firefox "http://localhost:8000" &>/dev/null &
    BROWSER_OPENED=true
elif command -v google-chrome &> /dev/null; then
    google-chrome "http://localhost:8000" &>/dev/null &
    BROWSER_OPENED=true
elif command -v chromium &> /dev/null; then
    chromium "http://localhost:8000" &>/dev/null &
    BROWSER_OPENED=true
fi

if [ "$BROWSER_OPENED" = true ]; then
    echo -e "${GREEN}✅ Browser geöffnet${NC}"
else
    echo -e "${YELLOW}⚠️  Browser konnte nicht automatisch geöffnet werden${NC}"
    echo -e "${YELLOW}   Bitte manuell öffnen: http://localhost:8000${NC}"
fi

echo ""
echo -e "${PURPLE}================================================="
echo "    ✅ Labor läuft!"
echo "=================================================${NC}"
echo ""
echo -e "${GREEN}📋 Wichtige Informationen:${NC}"
echo ""
echo -e "  ${BLUE}Web-Client:${NC}      http://localhost:8000"
echo -e "  ${BLUE}Signaling:${NC}       ws://localhost:8080"
echo ""
echo -e "${YELLOW}📝 Nächste Schritte:${NC}"
echo "  1. Öffnen Sie einen zweiten Browser-Tab"
echo "  2. Navigieren Sie zu http://localhost:8000"
echo "  3. In beiden Tabs: 'Mit Server verbinden' klicken"
echo "  4. In einem Tab: 'Anruf starten' klicken"
echo "  5. Beobachten Sie ICE-Kandidaten und Sicherheitswarnungen"
echo ""
echo -e "${YELLOW}🔍 Logs anzeigen:${NC}"
echo "  Signaling: tail -f /tmp/webrtc-signaling.log"
echo "  HTTP:      tail -f /tmp/webrtc-http.log"
echo ""
echo -e "${RED}⏹️  Zum Beenden: Ctrl+C drücken${NC}"
echo ""
echo -e "${PURPLE}=================================================${NC}"
echo ""

# Warte auf User-Input (Ctrl+C)
while true; do
    sleep 1
    
    # Prüfe ob Server noch laufen
    if ! kill -0 $SIGNALING_PID 2>/dev/null; then
        echo -e "\n${RED}⚠️  Signaling Server ist abgestürzt!${NC}"
        echo -e "${YELLOW}Log:${NC}"
        tail -20 /tmp/webrtc-signaling.log
        cleanup
    fi
    
    if ! kill -0 $HTTP_PID 2>/dev/null; then
        echo -e "\n${RED}⚠️  HTTP Server ist abgestürzt!${NC}"
        echo -e "${YELLOW}Log:${NC}"
        tail -20 /tmp/webrtc-http.log
        cleanup
    fi
done
