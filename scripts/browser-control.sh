#!/bin/bash
# Browser control wrapper - works around CLI bug using working HTTP POST calls
# Usage: ./browser-control.sh [start|stop|status|navigate <url>|screenshot|snapshot|tabs]

GATEWAY="http://127.0.0.1:18791"
TOKEN="4497935e23ec7da36b6b53fec1536260883625738f1ac36a"
PROFILE="${BROWSER_PROFILE:-openclaw}"

do_post() {
    local endpoint="$1"
    local data="$2"
    curl -s "$GATEWAY/$endpoint" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -X POST \
        -d "$data"
}

case "$1" in
    start)
        do_post "start" "{\"profile\":\"$PROFILE\"}"
        ;;
    stop)
        do_post "stop" "{\"profile\":\"$PROFILE\"}"
        ;;
    status)
        curl -s "http://127.0.0.1:18791/" -H "Authorization: Bearer $TOKEN"
        ;;
    navigate)
        do_post "navigate" "{\"profile\":\"$PROFILE\",\"url\":\"$2\"}"
        ;;
    screenshot)
        do_post "screenshot" "{\"profile\":\"$PROFILE\"}"
        ;;
    snapshot)
        do_post "snapshot" "{\"profile\":\"$PROFILE\"}"
        ;;
    tabs)
        do_post "tabs" "{\"profile\":\"$PROFILE\"}"
        ;;
    *)
        echo "Browser Control Wrapper (backup for CLI bug)"
        echo "Usage: $0 {start|stop|status|navigate <url>|screenshot|snapshot|tabs}"
        echo ""
        echo "Examples:"
        echo "  $0 status"
        echo "  $0 navigate https://google.com"
        echo "  $0 screenshot"
        exit 1
        ;;
esac
