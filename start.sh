#!/bin/sh
# create the virtual radios
sudo modprobe -r mac80211_hwsim
sudo modprobe mac80211_hwsim radios=4

docker-compose down
docker rm -f ap client attacker defender 2>/dev/null

docker-compose build
docker-compose up -d

sleep 5

# Get container IDs
AP_PID=$(docker inspect -f '{{.State.Pid}}' ap)
CL_PID=$(docker inspect -f '{{.State.Pid}}' client)
ATK=$(docker inspect -f '{{.State.Pid}}' attacker)
DEF=$(docker inspect -f '{{.State.Pid}}' defender)

echo "AP PID: $AP_PID"
echo "Client PID: $CL_PID"
echo "Attacker PID: $ATK"
echo "Defender PID: $DEF"

sudo ip link set wlan0 down
sudo ip link set wlan1 down
sudo ip link set wlan2 down
sudo ip link set wlan3 down


PHY0=$(iw dev wlan0 info | awk '/wiphy/{print "phy"$2}')
PHY1=$(iw dev wlan1 info | awk '/wiphy/{print "phy"$2}')
PHY2=$(iw dev wlan2 info | awk '/wiphy/{print "phy"$2}')
PHY3=$(iw dev wlan3 info | awk '/wiphy/{print "phy"$2}')

# Move virtual radios into containers
sudo iw phy $PHY0 set netns $AP_PID
sudo iw phy $PHY1 set netns $CL_PID
sudo iw phy $PHY2 set netns $ATK
sudo iw phy $PHY3 set netns $DEF

# Bring radios up and assign ips

docker exec -d ap sh -c "ip link set wlan0 up && ip addr add 10.0.0.1/24 dev wlan0 && hostapd /volumes/hostapd.conf"
sleep 5

docker exec client sh -c "ip link set wlan1 up && wpa_supplicant -Dnl80211 -iwlan1 -c /volumes/client.conf -B"
sleep 2
docker exec client sh -c "ip addr add 10.0.0.2/24 dev wlan1 && ip route add default via 10.0.0.1"


# the attacker is placed in monitor mode
docker exec attacker sh -c "iw wlan2 set monitor control && ip link set wlan2 up"
docker exec attacker sh -c "iw wlan2 set channel 6"

# the defender is placed in monitor mode
docker exec defender sh -c "iw wlan3 set monitor control && ip link set wlan3 up"
docker exec defender sh -c "iw wlan3 set channel 6"



