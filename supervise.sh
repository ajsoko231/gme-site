#!/usr/bin/env bash
# Keeps serve.py (port 8080) and a Cloudflare quick tunnel alive.
# Current public URL is written to PUBLIC_URL.txt. Logs: logs/*.log
# Start: nohup ./supervise.sh >/dev/null 2>&1 &
cd "$(dirname "$0")"; mkdir -p logs
CF="$HOME/bin/cloudflared"; PORT=8080
exec 9>logs/supervise.lock; flock -n 9 || { echo "already running"; exit 0; }
log(){ echo "$(date '+%F %T %Z') $*" >> logs/supervise.log; }
start_tunnel(){
  : > logs/cloudflared.log
  nohup "$CF" tunnel --no-autoupdate --url "http://localhost:$PORT" >> logs/cloudflared.log 2>&1 &
  CF_PID=$!; log "started cloudflared pid $CF_PID"
  for _ in $(seq 60); do
    url=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' logs/cloudflared.log | head -1)
    [ -n "$url" ] && { echo "$url" > PUBLIC_URL.txt; log "public URL $url"; return; }
    sleep 1
  done; log "no URL yet from cloudflared"
}
CF_PID=$(pgrep -f "cloudflared tunnel.*localhost:$PORT" | head -1)
[ -z "$CF_PID" ] && start_tunnel || log "adopted cloudflared pid $CF_PID"
while true; do
  if ! curl -s -o /dev/null -m 5 "http://localhost:$PORT/"; then
    log "serve.py down, starting"; nohup python3 serve.py $PORT >> logs/server.log 2>&1 &
  fi
  kill -0 "$CF_PID" 2>/dev/null || { log "cloudflared died, restarting (URL will change)"; start_tunnel; }
  sleep 15
done
