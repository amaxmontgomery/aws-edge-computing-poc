"""
Aggregate repeated wireless observations into useful per-MAC state.

Each valid TShark frame still counts as an observation, but repeated
observations from the same scanner and MAC update one aggregate record
instead of creating a separate long-term record for every frame.
"""

from dataclasses import dataclass, field
from datetime import datetime

from .models import Observation


@dataclass
class ObservationAggregate:
    """
    Aggregated state for one observed MAC address on one scanner.
    """

    # Scanner that produced these observations.
    scanner_id: str

    # MAC address being observed.
    observed_mac: str

    # Time this MAC was first observed.
    first_seen: datetime

    # Time this MAC was most recently observed.
    last_seen: datetime

    # Total number of valid frames observed for this MAC.
    frame_count: int

    # Number of observation sessions.
    session_count: int

    # Most recently known RSSI value.
    latest_rssi_dbm: int | None

    # Weakest RSSI value observed.
    min_rssi_dbm: int | None

    # Strongest RSSI value observed.
    max_rssi_dbm: int | None

    # Average of all observations that contained RSSI.
    average_rssi_dbm: float | None

    # Most recently known frequency.
    frequency_mhz: int | None

    # Most recently known Wi-Fi channel.
    channel: int | None

    # Most recently known Wi-Fi band.
    band: str | None

    # Internal values used to calculate the running RSSI average.
    # repr=False keeps these implementation details out of printed output.
    _rssi_total: int = field(default=0, repr=False)
    _rssi_sample_count: int = field(default=0, repr=False)

    @classmethod
    def create(
        cls,
        observation: Observation,
    ) -> "ObservationAggregate":
        """
        Create a new aggregate from the first observation of a MAC.
        """

        # RSSI may be missing from an observation.
        if observation.rssi_dbm is None:
            rssi_total = 0
            rssi_sample_count = 0
            average_rssi_dbm = None
        else:
            rssi_total = observation.rssi_dbm
            rssi_sample_count = 1
            average_rssi_dbm = float(observation.rssi_dbm)

        return cls(
            scanner_id=observation.scanner_id,
            observed_mac=observation.observed_mac,
            first_seen=observation.observed_at,
            last_seen=observation.observed_at,
            frame_count=1,
            session_count=1,
            latest_rssi_dbm=observation.rssi_dbm,
            min_rssi_dbm=observation.rssi_dbm,
            max_rssi_dbm=observation.rssi_dbm,
            average_rssi_dbm=average_rssi_dbm,
            frequency_mhz=observation.frequency_mhz,
            channel=observation.channel,
            band=observation.band,
            _rssi_total=rssi_total,
            _rssi_sample_count=rssi_sample_count,
        )

    def update(
        self,
        observation: Observation,
        session_gap_seconds: int,
    ) -> None:
        """
        Update this aggregate with another observation.
        """

        # The observation must belong to the same scanner and MAC.
        if observation.scanner_id != self.scanner_id:
            raise ValueError(
                "Observation scanner_id does not match aggregate"
            )

        if observation.observed_mac != self.observed_mac:
            raise ValueError(
                "Observation MAC does not match aggregate"
            )

        # Calculate how long this MAC went without being observed.
        gap_seconds = (
            observation.observed_at - self.last_seen
        ).total_seconds()

        # More than the configured gap starts a new observation session.
        #
        # This only means the MAC was not observed during that period.
        # It does not prove that the physical device left and returned.
        if gap_seconds > session_gap_seconds:
            self.session_count += 1

        # Every valid observation increments the frame count.
        self.frame_count += 1

        # This is now the most recent observation time.
        self.last_seen = observation.observed_at

        # Update RSSI statistics only when RSSI is available.
        if observation.rssi_dbm is not None:
            self.latest_rssi_dbm = observation.rssi_dbm

            if (
                self.min_rssi_dbm is None
                or observation.rssi_dbm < self.min_rssi_dbm
            ):
                self.min_rssi_dbm = observation.rssi_dbm

            if (
                self.max_rssi_dbm is None
                or observation.rssi_dbm > self.max_rssi_dbm
            ):
                self.max_rssi_dbm = observation.rssi_dbm

            self._rssi_total += observation.rssi_dbm
            self._rssi_sample_count += 1

            self.average_rssi_dbm = (
                self._rssi_total
                / self._rssi_sample_count
            )

        # Keep the most recently known channel information.
        if observation.frequency_mhz is not None:
            self.frequency_mhz = observation.frequency_mhz
            self.channel = observation.channel
            self.band = observation.band


class ObservationAggregator:
    """
    Maintain aggregate records for observed MAC addresses.
    """

    def __init__(
        self,
        session_gap_seconds: int,
    ) -> None:
        """
        Create an aggregator with the configured session gap.
        """

        if session_gap_seconds <= 0:
            raise ValueError(
                "session_gap_seconds must be greater than zero"
            )

        self.session_gap_seconds = session_gap_seconds

        # Key:
        # (scanner_id, observed_mac)
        #
        # Value:
        # ObservationAggregate
        self._aggregates: dict[
            tuple[str, str],
            ObservationAggregate,
        ] = {}

    def add(
        self,
        observation: Observation,
    ) -> ObservationAggregate:
        """
        Add an observation and return its updated aggregate.
        """

        key = (
            observation.scanner_id,
            observation.observed_mac,
        )

        aggregate = self._aggregates.get(key)

        # First time this scanner has observed this MAC.
        if aggregate is None:
            aggregate = ObservationAggregate.create(
                observation
            )

            self._aggregates[key] = aggregate

            return aggregate

        # Existing MAC: update its current aggregate.
        aggregate.update(
            observation,
            self.session_gap_seconds,
        )

        return aggregate
