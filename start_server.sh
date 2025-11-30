#!/bin/bash
# WebRTC Lab - Signaling Server Starter

echo "================================================="
echo "    WebRTC Security Lab - Signaling Server"
echo "================================================="
echo ""

# Prüfe ob Python verfügbar ist
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 nicht gefunden!"
    exit 1
fi

echo "✅ Python 3 gefunden: $(python3 --version)"
echo ""

# Versuche Dependencies zu installieren
echo "📦 Installiere Abhängigkeiten..."

# Option 1: Virtual Environment (empfohlen)
if [ ! -d "venv" ]; then
    echo "   Erstelle Virtual Environment..."
    if python3 -m venv venv 2>/dev/null; then
        echo "   ✅ Virtual Environment erstellt"
        source venv/bin/activate
        pip install -q -r requirements.txt
        echo "   ✅ Dependencies installiert"
    else
        echo "   ⚠️  venv nicht verfügbar, versuche pipx..."
        # Option 2: pipx
        if command -v pipx &> /dev/null; then
            pipx install websockets aiohttp
        else
            # Option 3: System-Pakete
            echo "   ℹ️  Bitte installieren Sie: sudo apt install python3-websockets python3-aiohttp"
            echo "   Oder: sudo apt install python3-venv && python3 -m venv venv"
        fi
    fi
else
    source venv/bin/activate
    echo "   ✅ Virtual Environment aktiviert"
fi

echo ""
echo "================================================="
echo "🚀 Starte Signaling Server..."
echo "================================================="
echo ""
echo "   URL: ws://localhost:8080"
echo "   Mode: Unverschlüsselt (Demo)"
echo ""
echo "   Drücken Sie Ctrl+C zum Beenden"
echo ""
echo "================================================="
echo ""

# Server starten
if [ -f "venv/bin/python" ]; then
    venv/bin/python signaling_server.py
else
    python3 signaling_server.py
fi
