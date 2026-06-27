#!/bin/bash
# Local desktop notification system
# Usage: ./scripts/notify.sh [--sound] "Message text"
# Example: ./scripts/notify.sh --sound "Module generation complete"

MESSAGE="${1:-Task finished}"
SOUND=false
URGENCY=1  # 1=normal, 2=critical

case "$1" in
    --sound|-s)
        MESSAGE="${2:-Task finished}"
        SOUND=true
        ;;
    --urgent|-u)
        MESSAGE="${2:-Task finished}"
        URGENCY=2
        SOUND=true
        ;;
esac

# Sound — anime-style ascending chime (C5→E5→G5)
if [ "$SOUND" = true ]; then
    SOUND_FILE="$HOME/.local/share/opencode/chime.wav"
    mkdir -p "$HOME/.local/share/opencode"
    python3 -c "
import wave, struct, math, array, sys, os
SR = 44100
dur = 0.25
notes = [523.25, 659.25, 783.99, 1046.5]  # C5, E5, G5, C6
data = array.array('h')
for n in notes:
    for i in range(int(SR * dur)):
        t = i / SR
        val = int(10000 * math.sin(2 * math.pi * n * t) * math.exp(-5 * t))
        data.append(val)
with wave.open(sys.argv[1], 'w') as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes(data.tobytes())
" "$SOUND_FILE"
    paplay "$SOUND_FILE" &
fi

# Desktop notification via dbus (works without notify-send)
python3 -c "
import dbus, sys
bus = dbus.SessionBus()
notif = bus.get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications')
iface = dbus.Interface(notif, 'org.freedesktop.Notifications')
iface.Notify('OpenCode', 0, 'dialog-information', 'OpenCode Agent', sys.argv[1], [], {'urgency': dbus.Byte(int(sys.argv[2]))}, 3000)
" "$MESSAGE" "$URGENCY"
