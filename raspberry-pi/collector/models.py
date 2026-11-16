"""
Data models and helper functions for wireless observations.

This module defines what a normalized wireless observation looks like
after TShark output has been parsed.
"""

# Imports
# Converts the Observation dataclass into a dictionary
from dataclasses import asdict, dataclass

# Handles observation timestamps and UTC conversion
from datetime import datetime, timezone

# Used for MAC address validation
import re

# Used to describe the return type of to_dict()
from typing import Any


# Expected MAC address format:
# aa:bb:cc:dd:ee:ff
#
# r -> raw string
# re.compile -> creates a reusable regex pattern object named _MAC_PATTERN
# [0-9a-fA-F] -> allows one hexadecimal character: 0-9, a-f, or A-F
# {2} -> requires exactly two hexadecimal characters for each MAC octet
# (?:...){5} -> repeats the "two hex characters + colon" group 5 times
# [0-9a-fA-F]{2} -> matches the final MAC octet without a trailing colon
# ^ and $ -> require the entire string to match the expected MAC format
# Rejects incorrectly formatted MAC addresses
_MAC_PATTERN = re.compile(
    r"^(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$"
)


def normalize_mac(mac: str) -> str:
    """
    Validate and normalize an observed MAC address.

    Example:
        AA:BB:CC:DD:EE:FF
    becomes:
        aa:bb:cc:dd:ee:ff
    """

    # Remove surrounding spaces and convert the address to lowercase.
    normalized = mac.strip().lower()

    # Reject values that do not match the expected MAC address format.
    if not _MAC_PATTERN.fullmatch(normalized):
        raise ValueError(f"Invalid MAC address: {mac!r}")

    return normalized


def frequency_to_channel(
    frequency_mhz: int | None,
) -> int | None:
    """
    Convert a Wi-Fi frequency in MHz to its channel number.
    """

    # Frequency may be missing from some observations.
    if frequency_mhz is None:
        return None

    # Standard 2.4 GHz channels 1 through 13.
    if (
        2412 <= frequency_mhz <= 2472
        and (frequency_mhz - 2407) % 5 == 0
    ):
        return (frequency_mhz - 2407) // 5

    # Standard 5 GHz channel calculation.
    if (
        5000 <= frequency_mhz <= 5900
        and frequency_mhz % 5 == 0
    ):
        return (frequency_mhz - 5000) // 5

    return None


def frequency_to_band(
    frequency_mhz: int | None,
) -> str | None:
    """
    Determine whether a frequency belongs to the 2.4 GHz or 5 GHz band.
    """

    if frequency_mhz is None:
        return None

    if 2400 <= frequency_mhz < 2500:
        return "2.4 GHz"

    if 5000 <= frequency_mhz < 5900:
        return "5 GHz"

    return None


@dataclass(frozen=True)
class Observation:
    """
    One normalized wireless observation received from TShark.
    """

    # Identifies which scanner produced the observation.
    scanner_id: str

    # Time the observation occurred.
    observed_at: datetime

    # Source MAC observed by TShark.
    observed_mac: str

    # Received signal strength in dBm.
    rssi_dbm: int | None

    # Frequency reported by TShark.
    frequency_mhz: int | None

    # Channel calculated from frequency_mhz.
    channel: int | None

    # Wi-Fi band calculated from frequency_mhz.
    band: str | None

    @classmethod
    def create(
        cls,
        *,
        scanner_id: str,
        observed_at: datetime,
        observed_mac: str,
        rssi_dbm: int | None,
        frequency_mhz: int | None,
    ) -> "Observation":
        """
        Create a validated and normalized observation.
        """

        # Every observation must identify which scanner produced it.
        if not scanner_id.strip():
            raise ValueError("scanner_id cannot be empty")

        # Require timezone information so the time is not ambiguous.
        if observed_at.tzinfo is None:
            raise ValueError(
                "observed_at must contain timezone information"
            )

        # Build the normalized observation.
        return cls(
            scanner_id=scanner_id.strip(),

            # Store timestamps in UTC for consistency across systems.
            observed_at=observed_at.astimezone(timezone.utc),

            # Validate and normalize the observed MAC.
            observed_mac=normalize_mac(observed_mac),

            rssi_dbm=rssi_dbm,

            # Keep the original frequency from TShark.
            frequency_mhz=frequency_mhz,

            # Also calculate human-readable channel and band information.
            channel=frequency_to_channel(frequency_mhz),
            band=frequency_to_band(frequency_mhz),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the observation into a JSON-friendly dictionary.
        """

        data = asdict(self)

        # Convert Python datetime to an ISO 8601 UTC timestamp.
        #
        # Example:
        # 2026-11-16T15:30:00Z
        data["observed_at"] = (
            self.observed_at
            .astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

        return data
