#!/bin/bash
# VirtualHelmet simulation test commands
BROKER="127.0.0.1"
pub() { mosquitto_pub -h "$BROKER" -t "helmet/voice/commands" -m "{\"command\":\"$1\"}"; echo "Sent: $1"; sleep 1; }

pub lights_on
pub lights_off
pub status
pub battery
pub distance
pub heading
pub temperature
pub mark_waypoint
pub night_mode
sleep 2
pub resume
pub power_save
sleep 2
pub resume
pub music_play
pub music_pause
pub music_next
pub volume_up
pub volume_down
