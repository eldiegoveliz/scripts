#!/bin/bash

BAT0="/sys/class/power_supply/BAT0/capacity"
BAT1="/sys/class/power_supply/BAT1/capacity"

while true; do
    bat0_level=$(cat $BAT0)
    bat1_level=$(cat $BAT1)

    if [[ "$bat1_level" -le 30 ]]; then
        # Do something: notify, switch workload, suspend, etc.
        notify-send "Battery Low" "BAT1 is below 30%. Consider plugging in or suspending."
        # You could optionally hibernate, etc.
    fi

    sleep 120
done
