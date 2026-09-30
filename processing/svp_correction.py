"""
Sonar Mapper — Sound Velocity Profile (SVP) correction.

Core function extracted from the TIPE report, Annexe 5 (translated to
English, logic unchanged: `vraie_distance` -> `true_distance`).

Converts a one-way acoustic travel time into a true range by integrating
travel time through a stack of constant-velocity depth layers, instead of
assuming a single speed of sound for the whole water column.

CLI usage (demo):
    python svp_correction.py --time 0.082

NOTE: this script demonstrates the correction function on a single
travel-time value. Applying it to a full survey requires the firmware to
log the raw one-way (or round-trip) travel time rather than a
pre-computed air-speed distance, which firmware/main/main.ino does not
currently do — see README > Design Notes > Roadmap.
"""

import argparse


def true_distance(one_way_time, zones):
    """
    Parameters
    ----------
    one_way_time : float
        One-way acoustic travel time, in seconds.
    zones : list[tuple[float, float]]
        Ordered list of (max_distance, velocity) pairs describing each
        depth layer, from the surface downward. max_distance is the layer
        thickness in meters, velocity is the local speed of sound in m/s.

    Returns
    -------
    float
        Estimated one-way range, in meters.
    """
    distance = 0.0
    time_remaining = one_way_time

    for max_distance, velocity in zones:
        zone_time = max_distance / velocity  # time to cross this layer

        if zone_time <= time_remaining:  # wave fully crosses this layer
            distance += max_distance
            time_remaining -= zone_time
        else:
            # wave only crosses part of this layer
            distance += velocity * time_remaining
            break

    return distance


# Example layered profile — illustrative placeholder values inspired by the
# three-zone velocity model in the report (slide 21), NOT measured data.
# Replace with a real in-situ temperature/salinity profile before use.
EXAMPLE_ZONES = [
    (50.0, 1450.0),    # Zone 1: near-surface, warmer layer
    (200.0, 1490.0),   # Zone 2: thermocline transition
    (1000.0, 1520.0),  # Zone 3: deep, near-constant velocity
]


def main():
    parser = argparse.ArgumentParser(
        description="Convert a one-way travel time to a range using a "
                     "layered sound-velocity profile (SVP)."
    )
    parser.add_argument(
        "--time", type=float, required=True,
        help="One-way travel time, in seconds.",
    )
    args = parser.parse_args()

    range_m = true_distance(args.time, EXAMPLE_ZONES)
    print(f"Estimated range: {range_m:.2f} m")


if __name__ == "__main__":
    main()
