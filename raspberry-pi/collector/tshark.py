"""
Start TShark and convert its output into Observation objects.
"""

import argparse
import subprocess
from datetime import datetime, timezone

from .models import Observation


def build_tshark_command(monitor_interface: str) -> list[str]:
    """
    Build the TShark command used by the collector.
    """

    return [
        # Program to start.
        "tshark",

        # -l -> line-buffered output so Python receives observations immediately.
        "-l",

        # -i -> network interface TShark captures from.
        "-i",
        monitor_interface,

        # -Y -> applies a TShark display filter.
        # wlan.sa -> only use frames containing a WLAN source address.
        "-Y",
        "wlan.sa",

        # -T fields -> output only the specifically requested packet fields.
        "-T",
        "fields",

        # -E occurrence=f -> use the first value if a field occurs multiple times.
        "-E",
        "occurrence=f",

        # Observation timestamp as Unix epoch time.
        "-e",
        "frame.time_epoch",

        # Wireless source MAC address.
        "-e",
        "wlan.sa",

        # Received signal strength in dBm.
        "-e",
        "radiotap.dbm_antsignal",

        # Frequency the frame was observed on, in MHz.
        "-e",
        "radiotap.channel.freq",
    ]


def parse_tshark_line(
    line: str,
    scanner_id: str,
) -> Observation | None:
    """
    Convert one line of TShark output into an Observation.

    Expected field order:
    timestamp, source MAC, RSSI, frequency
    """

    # TShark separates fields with tabs.
    fields = line.rstrip("\n").split("\t")

    # Every line should contain exactly four fields.
    if len(fields) != 4:
        return None

    timestamp_text, mac, rssi_text, frequency_text = fields

    # Timestamp and MAC are required for an observation.
    if not timestamp_text or not mac:
        return None

    try:
        # TShark gives frame.time_epoch as Unix time.
        observed_at = datetime.fromtimestamp(
            float(timestamp_text),
            tz=timezone.utc,
        )

        # RSSI or frequency may occasionally be missing.
        rssi_dbm = int(rssi_text) if rssi_text else None

        frequency_mhz = (
            int(frequency_text)
            if frequency_text
            else None
        )

        return Observation.create(
            scanner_id=scanner_id,
            observed_at=observed_at,
            observed_mac=mac,
            rssi_dbm=rssi_dbm,
            frequency_mhz=frequency_mhz,
        )

    # Ignore malformed TShark records instead of stopping the collector.
    except (ValueError, OverflowError):
        return None


def stream_observations(
    scanner_id: str,
    monitor_interface: str,
):
    """
    Start TShark and continuously yield valid observations.
    """

    command = build_tshark_command(monitor_interface)

    # Start TShark and read its standard output one line at a time.
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    if process.stdout is None:
        raise RuntimeError("Unable to read TShark output")

    try:
        for line in process.stdout:
            observation = parse_tshark_line(
                line,
                scanner_id,
            )

            if observation is not None:
                yield observation

    finally:
        # Stop TShark when the Python collector exits.
        process.terminate()
        process.wait()


def main() -> None:
    """
    Run the TShark collector from the command line.
    """

    parser = argparse.ArgumentParser(
        description="Read wireless observations from TShark"
    )

    parser.add_argument(
        "--interface",
        required=True,
        help="Monitor-mode interface used by TShark",
    )

    parser.add_argument(
        "--scanner-id",
        required=True,
        help="Identifier assigned to this scanner",
    )

    args = parser.parse_args()

    try:
        for observation in stream_observations(
            scanner_id=args.scanner_id,
            monitor_interface=args.interface,
        ):
            print(observation)

    except KeyboardInterrupt:
        print("\nCollector stopped.")


if __name__ == "__main__":
    main()
