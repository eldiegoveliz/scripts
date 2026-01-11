#!/bin/bash

state_file="/tmp/waybar_pct_state"

state=$(cat "$state_file" 2>/dev/null || echo "1")

if [ "$state" = "1" ]; then
	line=$(sed -n "1p" "/home/diego/scripts/grafstoncks/portfolio-tracker/pct.txt")
	next_state="2"
else
	line=$(sed -n "2p" "/home/diego/scripts/grafstoncks/portfolio-tracker/pct.txt")
	next_state="1"
fi

echo "$next_state" > "$state_file"

echo "{\"text\": \"$line\"}"
