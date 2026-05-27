# Lab Setup

## start wlan1 in monitor mode:

└─$ sudo ip link set wlan1 down
└─$ sudo iw dev wlan1 set type monitor
└─$ sudo ip link set wlan1 up

## find AP's MAC Address
└─$ sudo airmon-ng start wlan1
└─$ sudo airodump-ng wlan1

BSSID: f2:1a:87:05:ce:e3

## Start Monitoring Tool
└─$ sudo python3 deauth_detector.py -i wlan1

## Start Attack
└─$ sudo python3 attack.py -a "f2:1a:87:05:ce:e3" -c "ff:ff:ff:ff:ff:ff"

