#!/bin/bash
# WebRTC Lab - Client HTTP Server Starter

echo "================================================="
echo "    WebRTC Security Lab - HTTP Server"
echo "================================================="
echo ""

cd "$(dirname "$0")"

echo "🌐 Starte HTTP Server für Web-Client..."
echo ""
echo "   URL: http://localhost:8000"
echo "   Öffnen Sie zwei Browser-Tabs auf dieser URL"
echo ""
echo "   Drücken Sie Ctrl+C zum Beenden"
echo ""
echo "================================================="
echo ""

python3 -m http.server 8000
