FROM debian:stable
RUN apt update && apt install -y hostapd wpasupplicant iproute2 iputils-ping aircrack-ng iw tcpdump
RUN apt update && apt install -y python3 python3-scapy