#!/usr/bin/env python3
"""
Wi-Fi Deauthentication Attack Detector
Network Security Project - Group G2

Passively monitors 802.11 wireless traffic for deauthentication
frame floods, which are characteristic of a deauth attack.

Usage:
    sudo python3 deauth_detector.py -i <interface> [options]

Requirements:
    - Wireless interface in monitor mode
    - pip install scapy
    - Run as root
"""

import argparse
import logging
import signal
import sys
import time
from collections import defaultdict
from datetime import datetime

from scapy.all import Dot11, Dot11Deauth, sniff


# ---------------------------------------------------------------------------
# Configuration defaults (can be overridden via CLI arguments)
# ---------------------------------------------------------------------------

DEFAULT_INTERFACE   = "wlan1mon"
DEFAULT_THRESHOLD   = 50       # deauth frames from a single source
DEFAULT_TIME_WINDOW = 10       # seconds over which frames are counted
DEFAULT_LOG_FILE    = "deauth_alerts.log"


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging(log_file: str) -> logging.Logger:
    logger = logging.getLogger("deauth_detector")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")

    # File handler — captures everything WARNING and above
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.WARNING)
    fh.setFormatter(fmt)

    # Console handler — INFO and above for live feedback
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


# ---------------------------------------------------------------------------
# Detector class
# ---------------------------------------------------------------------------

class DeauthDetector:
    """
    Tracks deauthentication frames per source MAC address within a rolling
    time window. Raises an alert when the frame count exceeds a threshold.
    """

    # Reason codes defined in IEEE 802.11-2016, Table 9-45
    REASON_CODES = {
        1:  "Unspecified",
        2:  "Previous authentication no longer valid",
        3:  "Deauthenticated because sending STA is leaving BSS",
        4:  "Disassociated due to inactivity",
        5:  "Disassociated because AP is unable to handle all associated STAs",
        6:  "Class 2 frame received from nonauthenticated STA",
        7:  "Class 3 frame received from nonassociated STA",
        8:  "Disassociated because sending STA is leaving BSS",
        9:  "STA requesting (re)association is not authenticated",
    }

    def __init__(self, interface: str, threshold: int,
                 time_window: int, whitelist: list, logger: logging.Logger):
        self.interface   = interface
        self.threshold   = threshold
        self.time_window = time_window
        self.whitelist   = set(mac.lower() for mac in whitelist)
        self.logger      = logger

        # { src_mac: [timestamp, ...] }
        self.frame_log   = defaultdict(list)

        # Stats
        self.total_frames   = 0
        self.total_alerts   = 0
        self.start_time     = None

    # ------------------------------------------------------------------
    # Packet handler
    # ------------------------------------------------------------------

    def handle_packet(self, packet) -> None:
        if not packet.haslayer(Dot11Deauth):
            return

        src = packet[Dot11].addr2
        dst = packet[Dot11].addr1

        if src is None:
            return

        src = src.lower()
        dst = dst.lower() if dst else "unknown"

        # Skip whitelisted sources (known legitimate APs)
        if src in self.whitelist:
            return

        self.total_frames += 1
        now = time.time()

        # Sliding window — discard frames outside the time window
        self.frame_log[src] = [
            t for t in self.frame_log[src] if now - t < self.time_window
        ]
        self.frame_log[src].append(now)

        count = len(self.frame_log[src])

        # Determine reason code if present
        reason = getattr(packet[Dot11Deauth], "reason", None)
        reason_str = self.REASON_CODES.get(reason, f"Code {reason}") if reason else "N/A"

        # Classify target
        is_broadcast = dst == "ff:ff:ff:ff:ff:ff"
        target_label = "BROADCAST" if is_broadcast else dst

        self.logger.debug(
            f"Deauth frame | src={src} dst={target_label} "
            f"reason={reason_str} count={count}/{self.threshold}"
        )

        if count >= self.threshold:
            self.total_alerts += 1
            severity = "CRITICAL" if is_broadcast else "WARNING"
            self.logger.warning(
                f"[{severity}] Deauth flood detected! "
                f"src={src} target={target_label} "
                f"frames={count} in {self.time_window}s "
                f"reason={reason_str}"
            )
            # Print a prominent alert to stdout as well
            print(
                f"\n{'='*60}\n"
                f"  ALERT [{severity}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"  Source  : {src}\n"
                f"  Target  : {target_label}\n"
                f"  Frames  : {count} in {self.time_window}s\n"
                f"  Reason  : {reason_str}\n"
                f"{'='*60}\n"
            )

    # ------------------------------------------------------------------
    # Start / stop
    # ------------------------------------------------------------------

    def start(self) -> None:
        self.start_time = time.time()
        self.logger.info(
            f"Detector started on {self.interface} | "
            f"threshold={self.threshold} frames/{self.time_window}s"
        )
        if self.whitelist:
            self.logger.info(f"Whitelisted MACs: {', '.join(self.whitelist)}")

        try:
            sniff(
                iface=self.interface,
                prn=self.handle_packet,
                store=False,
                filter="type mgt subtype deauth",
            )
        except PermissionError:
            self.logger.error("Permission denied. Run as root (sudo).")
            sys.exit(1)
        except OSError as e:
            self.logger.error(f"Interface error: {e}")
            sys.exit(1)

    def print_summary(self) -> None:
        elapsed = time.time() - self.start_time if self.start_time else 0
        print(
            f"\n{'='*60}\n"
            f"  Session Summary\n"
            f"  Runtime     : {elapsed:.1f}s\n"
            f"  Total frames: {self.total_frames}\n"
            f"  Alerts fired: {self.total_alerts}\n"
            f"{'='*60}\n"
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Wi-Fi Deauthentication Attack Detector",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-i", "--interface",
        default=DEFAULT_INTERFACE,
        help="Monitor-mode wireless interface to sniff on",
    )
    parser.add_argument(
        "-t", "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help="Number of deauth frames from a single source to trigger an alert",
    )
    parser.add_argument(
        "-w", "--window",
        type=int,
        default=DEFAULT_TIME_WINDOW,
        help="Rolling time window in seconds",
    )
    parser.add_argument(
        "-l", "--log",
        default=DEFAULT_LOG_FILE,
        help="Path to the alert log file",
    )
    parser.add_argument(
        "--whitelist",
        nargs="*",
        default=[],
        metavar="MAC",
        help="One or more source MAC addresses to ignore (e.g. your own AP)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    logger = setup_logging(args.log)

    detector = DeauthDetector(
        interface=args.interface,
        threshold=args.threshold,
        time_window=args.window,
        whitelist=args.whitelist,
        logger=logger,
    )

    # Graceful shutdown on Ctrl+C
    def on_sigint(sig, frame):
        print("\nStopping detector...")
        detector.print_summary()
        sys.exit(0)

    signal.signal(signal.SIGINT, on_sigint)

    detector.start()


if __name__ == "__main__":
    main()
