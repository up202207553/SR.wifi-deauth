# create the virtual radios
sudo modprobe mac80211_hwsim radios=3


# Get container IDs
AP_PID=$(docker inspect -f '{{.State.Pid}}' ap)
CL_PID=$(docker inspect -f '{{.State.Pid}}' client)
ATK=$(docker inspect -f '{{.State.Pid}}' attacker)

echo "AP PID: $AP_PID"
echo "Client PID: $CL_PID"
echo "Attacker PID: $ATK"

# Move virtual radios into containers
sudo ip link set wlan0 netns $AP_PID
sudo ip link set wlan1 netns $CL_PID
sudo ip link set wlan2 netns $ATK

# Bring radios up and assign ips
ip link set wlan0 up
ip addr add 10.0.0.1/24 dev wlan0

ip link set wlan1 up
ip addr add 10.0.0.2/24 dev wlan1
#ip route add default via 10.0.0.1

# the attacker is placed in monitor mode
iw wlan2 set monitor control
ip link set wlan2 up


# for clean up run sudo modprobe -r mac80211_hwsim




