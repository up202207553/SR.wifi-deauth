#!/bin/sh
# create the virtual radios
sudo modprobe mac80211_hwsim radios=3

docker-compose down
docker rm -f ap client attacker 2>/dev/null

docker-compose build
docker-compose up -d

sleep 10

# Get container IDs
AP_PID=$(docker inspect -f '{{.State.Pid}}' ap)
CL_PID=$(docker inspect -f '{{.State.Pid}}' client)
ATK=$(docker inspect -f '{{.State.Pid}}' attacker)

echo "AP PID: $AP_PID"
echo "Client PID: $CL_PID"
echo "Attacker PID: $ATK"

sudo ip link set wlan0 down
sudo ip link set wlan1 down
sudo ip link set wlan2 down


PHY0=$(iw dev wlan0 info | awk '/wiphy/{print "phy"$2}')
PHY1=$(iw dev wlan1 info | awk '/wiphy/{print "phy"$2}')
PHY2=$(iw dev wlan2 info | awk '/wiphy/{print "phy"$2}')

# Move virtual radios into containers
sudo iw phy $PHY0 set netns $AP_PID
sudo iw phy $PHY1 set netns $CL_PID
sudo iw phy $PHY2 set netns $ATK

# Bring radios up and assign ips

docker exec -d ap sh -c "ip link set wlan0 up && ip addr add 10.0.0.1/24 dev wlan0 && hostapd /volumes/hostapd.conf"
sleep 5

docker exec client sh -c "ip link set wlan1 up && wpa_supplicant -Dnl80211 -iwlan1 -c /volumes/client.conf -B"
sleep 2
docker exec client sh -c "ip addr add 10.0.0.2/24 dev wlan1 && ip route add default via 10.0.0.1"


# the attacker is placed in monitor mode
docker exec attacker sh -c "iw wlan2 set monitor control && ip link set wlan2 up"
docker exec attacker sh -c "iw wlan2 set channel 6"

# for clean up run sudo modprobe -r mac80211_hwsim
