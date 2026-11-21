#!/usr/bin/env bash
# Stops the cloudflared-web connector when either local origin is dead, so Cloudflare sends
# visitors to the other host instead of returning 502s from a live connector with a dead origin.
# Starts it again once both origins answer. Needs 2 consecutive failures to stop (no flapping).
set -u
state=/run/p59-web-watchdog.fails
ok() { curl -fsS -m 4 -o /dev/null -A watchdog "$1"; }
if ok http://127.0.0.1:8056/healthz && ok http://127.0.0.1:8060/healthz; then
  echo 0 > "$state"
  systemctl is-active --quiet cloudflared-web || { systemctl start cloudflared-web; logger -t p59-watchdog "origins healthy; started cloudflared-web"; }
else
  n=$(( $(cat "$state" 2>/dev/null || echo 0) + 1 )); echo "$n" > "$state"
  if [ "$n" -ge 2 ] && systemctl is-active --quiet cloudflared-web; then
    systemctl stop cloudflared-web; logger -t p59-watchdog "origin unhealthy ($n checks); stopped cloudflared-web"
  fi
fi
