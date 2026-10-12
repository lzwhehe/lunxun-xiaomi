#!/usr/bin/env bash
# Send a one-line patrol summary to Telegram.
# Usage:
#   bash notify_telegram.sh "message text"   # send a message
#   bash notify_telegram.sh --get-chat-id    # list chat ids that messaged the bot
# Config: telegram.env next to this script (never printed):
#   TELEGRAM_BOT_TOKEN=...
#   TELEGRAM_CHAT_ID=...
#   TELEGRAM_PROXY=http://127.0.0.1:7890   (optional)

set -u
# Git's usr\bin\bash.exe started directly from PowerShell has no coreutils on PATH.
export PATH="/usr/bin:/mingw64/bin:$PATH"
dir="${0%/*}"; [ "$dir" = "$0" ] && dir="."
cfg="$dir/telegram.env"

if [ ! -f "$cfg" ]; then
  echo "ERROR: $cfg not found" >&2
  exit 2
fi

# Read KEY=VALUE lines without executing the file; strip CR from Windows line endings.
TELEGRAM_BOT_TOKEN=""; TELEGRAM_CHAT_ID=""; TELEGRAM_PROXY=""
while IFS='=' read -r key val; do
  key="${key//[[:space:]]/}"
  val="${val//$'\r'/}"
  val="${val#"${val%%[![:space:]]*}"}"
  val="${val%"${val##*[![:space:]]}"}"
  case "$key" in
    TELEGRAM_BOT_TOKEN) TELEGRAM_BOT_TOKEN="$val" ;;
    TELEGRAM_CHAT_ID)   TELEGRAM_CHAT_ID="$val" ;;
    TELEGRAM_PROXY)     TELEGRAM_PROXY="$val" ;;
  esac
done < "$cfg"

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
  echo "ERROR: TELEGRAM_BOT_TOKEN is empty in telegram.env" >&2
  exit 2
fi
if [ -n "$TELEGRAM_PROXY" ] && [[ "$TELEGRAM_PROXY" != *://* ]]; then
  echo "ERROR: TELEGRAM_PROXY must look like http://127.0.0.1:7890 (is the token on the wrong line?)" >&2
  exit 2
fi

proxy_args=()
[ -n "$TELEGRAM_PROXY" ] && proxy_args=(-x "$TELEGRAM_PROXY")
api="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}"

if [ "${1:-}" = "--get-chat-id" ]; then
  resp="$(curl -s --max-time 20 "${proxy_args[@]}" "$api/getUpdates")" || { echo "ERROR: request failed (network/proxy?)" >&2; exit 1; }
  ids="$(printf '%s' "$resp" | grep -o '"chat":{"id":-\?[0-9]*' | grep -o -- '-\?[0-9]*$' | sort -u)"
  if [ -z "$ids" ]; then
    echo "No chats found. Send any message to your bot in Telegram first, then rerun."
    printf '%s\n' "$resp" | head -c 300; echo
    exit 1
  fi
  echo "chat ids:"; printf '%s\n' "$ids"
  exit 0
fi

msg="${1:-}"
if [ -z "$msg" ]; then
  echo "Usage: bash notify_telegram.sh \"message\"" >&2
  exit 2
fi
if [ -z "$TELEGRAM_CHAT_ID" ]; then
  echo "ERROR: TELEGRAM_CHAT_ID is empty in telegram.env" >&2
  exit 2
fi

# curl.exe on Windows re-decodes argv with the ANSI code page (GBK here), which
# mangles Chinese. Pass the text through a file so curl reads raw UTF-8 bytes.
tmp="$(mktemp)"; trap 'rm -f "$tmp"' EXIT
printf '%s' "$msg" > "$tmp"
# MSYS does not rewrite the path inside "text@...", so hand curl a Windows path.
command -v cygpath >/dev/null 2>&1 && tmp="$(cygpath -m "$tmp")"
resp="$(curl -s --max-time 20 "${proxy_args[@]}" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text@${tmp}" \
  --data-urlencode "disable_web_page_preview=true" \
  "$api/sendMessage")" || { echo "ERROR: request failed (network/proxy?)" >&2; exit 1; }

if printf '%s' "$resp" | grep -q '"ok":true'; then
  echo "sent"
else
  echo "ERROR: Telegram rejected the message:" >&2
  printf '%s\n' "$resp" | head -c 300 >&2; echo >&2
  exit 1
fi
