# 🌊 Sonar Mapper

**A georeferenced acoustic acquisition chain that turns time-of-flight measurements into a 3D bathymetric mesh.**

![Arduino](https://img.shields.io/badge/Arduino-Uno-00979D?logo=arduino&logoColor=white)
![C++](https://img.shields.io/badge/C%2B%2B-Firmware-00599C?logo=cplusplus&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Blender](https://img.shields.io/badge/Blender-bpy%20%2F%20bmesh-E87D0D?logo=blender&logoColor=white)
![NMEA](https://img.shields.io/badge/GPS-NMEA%200183-success)
![Status](https://img.shields.io/badge/status-research%20prototype-orange)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## 🎬 Demo

<!-- Replace with a GIF: hardware setup + Blender mesh -->
![Demo](docs/demo.gif)

| Validation target | Reconstructed mesh (Blender) |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/3e6a4ad9-9fe2-44ad-8e57-d80c716b2ae2" height="250" alt="Validation target" /> | <img src="https://github.com/user-attachments/assets/d7fc3855-ca40-46ba-825c-6737db270c79" height="250" alt="Reconstructed mesh" /> |
| <img src="https://github.com/user-attachments/assets/990db674-ec0c-4550-ae62-afd5e4360b70" height="250" alt="Hardware setup" /> | <img src="https://github.com/user-attachments/assets/75b55b8e-7877-4a88-a4a3-dfab93da6e8e" height="250" alt="Mesh preview" /> |

---

## 🧭 Overview

Sonar Mapper is an end-to-end measurement chain for single-beam bathymetry:

```
JSN-SR04T ──► Arduino Uno ──► SD (CSV) ──► Python SVP correction ──► Blender mesh
 (ToF echo)   (pulseIn + NMEA)  lat,lon,d      (layered travel time)     (bmesh point cloud)
                    ▲
               GPS Neo-6M
```

Each ping is timestamped by round-trip time, tagged with a GPS fix, logged, then converted to depth using a layered sound-velocity model and rendered as a surface.

---

## ✨ Key Features

- **Time-of-Flight (ToF) ranging**: trigger/echo timing on the Arduino, with `d = v·t / 2`.
- **Georeferenced logging**: NMEA sentences parsed with TinyGPS++, one `lat,lon,distance` record per ping on micro SD, with no host PC needed in the field.
- **Sound Velocity Profile (SVP) correction**: piecewise-constant velocity layers convert travel time to true range instead of assuming a single speed of sound.
- **Point-cloud to mesh generation**: Python/`bmesh` pipeline builds a navigable 3D surface in Blender.
- **In-situ velocity calibration protocol**: known-distance round-trip measurements in fresh water (20 °C, 30 °C) and salt water (20 °C).
- **Physics-driven design choice**: electromagnetic sounding ruled out from skin-depth analysis (see below).

---

## 📁 Repository Layout

```
sonar-mapper/
├── firmware/
│   ├── main/main.ino                    # field acquisition (GPS + SD + ToF)
│   └── pool_calibration/pool_calibration.ino   # raw round-trip time logger
├── processing/
│   └── svp_correction.py                # layered travel-time correction
├── blender/
│   └── import_points.py                 # point cloud -> mesh
└── data/
    └── sample_log.txt                   # example lat,lon,distance log
```

**Provenance**: `firmware/*.ino`, the `true_distance()` function in `svp_correction.py`, and `build_mesh()` in `import_points.py` are extracted from the original TIPE report (Annexes 1, 2, 4, 5, 3 respectively) with comments and variable names translated to English and logic unchanged. The CSV loading in `import_points.py` and the CLI wrapper in `svp_correction.py` were added to connect these stages into one runnable pipeline; they were not part of the original report.

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/<your-user>/sonar-mapper.git && cd sonar-mapper

# 2. Flash the field acquisition firmware
arduino-cli lib install "TinyGPSPlus" && arduino-cli compile --fqbn arduino:avr:uno firmware/main/ && arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno firmware/main/

# 3. Demo the SVP correction on a single travel time
python processing/svp_correction.py --time 0.082

# 4. Build a mesh from a logged survey
blender --python blender/import_points.py -- data/sample_log.txt
```

> Adjust the serial port (`/dev/ttyACM0` or `COM3`) to your setup. `firmware/pool_calibration/` is a separate sketch used only for the speed-of-sound calibration runs, not for field surveys.

### Wiring

| Module | Arduino pins |
|---|---|
| JSN-SR04T (TRIG / ECHO) | `9` / `10` |
| microSD (CS) | `8` (`firmware/main`) or `4` (`firmware/pool_calibration`) |
| microSD (SCK / MOSI / MISO) | `13` / `11` / `12` (hardware SPI) |
| GPS Neo-6M (Arduino RX / TX) | `4` / `3` (SoftwareSerial, 9600 baud) |
| Power | Common 5 V / GND |

### Log format

```
28.603252,1.444262,123.45
```

Fields: `latitude, longitude, range (cm)`, one line per ping (1 Hz). Sample data: `data/sample_log.txt`.

---

## ⚙️ Configuration

No environment variables are used. Parameters are compile-time constants:

| Parameter | Location | Default | Purpose |
|---|---|---|---|
| `trigPin` | `firmware/main/main.ino` | `9` | Transducer trigger output |
| `echoPin` | `firmware/main/main.ino` | `10` | Echo pulse-width input |
| `chipSelect` | `firmware/main/main.ino` | `8` | SD chip-select (field setup) |
| `chipSelect` | `firmware/pool_calibration/pool_calibration.ino` | `4` | SD chip-select (pool test) |
| `gpsSerial` | `firmware/main/main.ino` | `SoftwareSerial(4, 3)` | GPS UART (RX, TX) |
| `0.034` | `firmware/main/main.ino` | cm/µs | Speed of sound **in air**, must be replaced for water |
| `EXAMPLE_ZONES` | `processing/svp_correction.py` | list of `(max_distance, velocity)` | SVP layers used for travel-time integration — illustrative, calibrate before real use |

---

## 🔬 Design Notes

### Why acoustics and not RF?

The electromagnetic skin depth in a conductor is `δ = √(2 / (ωμσ))`. For seawater (σ ≈ 4 S/m) this gives roughly 25 cm at 1 MHz, so EM sounding is unusable at any useful range. Acoustic waves propagate with far lower attenuation in water.

### Why an SVP correction?

Sound speed in seawater depends on temperature, salinity and pressure, all of which vary with depth (thermocline, halocline, pycnocline). Assuming a constant velocity biases depth estimates. `true_distance()` integrates travel time layer by layer: full traversal of a layer consumes `d_max / v` of the travel-time budget, and the remaining time is converted in the last layer reached.

---

## 🧪 Results

### Sound velocity measurements

Round-trip time over a known distance in a pool (values selected for consistency across runs):

| Medium | Measured (m/s) | Reference (m/s) | Deviation |
|---|---|---|---|
| Fresh water, 30 °C | 1526 | 1507 | +1.3 % |
| Fresh water, 20 °C | 1496 | 1482 | +0.9 % |
| Salt water, 20 °C | 1556 | 1522 | +2.2 % |

Individual samples scatter widely (roughly 1200 to 2000 m/s), so the averages resolve the medium dependence but not a precise velocity.

### Validation status

| Environment | Result |
|---|---|
| Air | ✅ A stacked-object target is reconstructed with recognizable geometry (two steps plus a small object on top) |
| Water | ⚠️ Range readings are unstable, with pool distances scattered between about 1.2 and 3.2 m against a fixed geometry |

The rest of the chain (NMEA parsing, SD logging, SVP processing, mesh generation) is validated. The limiting element is the transducer.

---

## 🔍 Root-Cause Analysis: Why the Transducer Fails in Water

The JSN-SR04T is a sealed, air-coupled ultrasonic transducer (nominally around 40 kHz — check your datasheet). It is splash-proof, but it is **acoustically designed for air loading**. Two mechanisms explain the unreliable underwater ranging. Both follow from first principles and observed behavior; they have not yet been confirmed with oscilloscope measurements (see Roadmap).

### 1. Acoustic impedance mismatch

Energy transfer across an interface depends on characteristic acoustic impedance `Z = ρ·c`. The intensity transmission coefficient is:

```
T = 4·Z1·Z2 / (Z1 + Z2)²
```

| Medium | Z (MRayl) |
|---|---|
| Air | ≈ 0.0004 |
| Water | ≈ 1.5 |
| Piezoceramic (PZT) | ≈ 30 |

- The device's membrane and housing are tuned to couple efficiently into air. Driving water directly with it corresponds to a strong mismatch: for a 0.0004 to 1.5 MRayl transition, `T ≈ 10⁻³` (about −30 dB), before any device-specific losses.
- A transducer built for water avoids this with a **quarter-wave matching layer** (thickness λ/4 in the layer material, impedance near `√(Z_piezo · Z_water)`, i.e. a few MRayl) between the ceramic and the water. This is absent here, so both emitted power and echo sensitivity are degraded.
- The added mass loading of water also shifts and damps the resonance of a device optimized for air, moving it away from its nominal operating frequency.

### 2. Transducer ringing and blind zone

After the excitation burst, a high-Q piezoelectric resonator keeps oscillating for a ring-down time `τ`. Echoes returning during this window are masked at the receiver. The blind range is:

```
d_blind = c · τ / 2
```

Since `c_water ≈ 4.4 · c_air`, the same ring-down time gives a blind zone about 4.4 times longer in water. As an illustration, `τ = 1 ms` gives about 0.17 m in air but about 0.75 m in water. In a pool a few meters deep, this consumes a large fraction of the useful range.

The module also outputs only a thresholded pulse width on `ECHO`. Under weak return signal, its detector can trigger on residual ringing or on multipath reflections from pool walls and the free surface instead of the true bottom echo, which is consistent with the wide scatter observed.

### Roadmap

- [ ] Probe the raw TX/RX signal with an oscilloscope to measure ring-down time `τ` and confirm the blind zone.
- [ ] Characterize the echo with a reference hydrophone.
- [ ] Modify `firmware/main/main.ino` to log the raw `duration` (or one-way time) instead of a pre-computed air-speed distance, so `svp_correction.py` can be applied to real survey data.
- [ ] Replace the air-coupled unit with a water-rated transducer including a matching layer, with a dedicated TX driver and RX chain (gain, time-varied gain).
- [ ] Log full echo waveforms and perform threshold or matched-filter detection, instead of relying on the module's pulse width.
- [ ] Compare SVP-corrected and constant-velocity depth on real in-water data.
- [ ] Add a temperature and conductivity sensor to feed the SVP model.

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| MCU | Arduino Uno (C++) |
| Transducer | JSN-SR04T |
| Positioning | u-blox Neo-6M (NMEA, UART) |
| Storage | microSD over SPI |
| Arduino libraries | `TinyGPSPlus`, `SoftwareSerial`, `SPI`, `SD` |
| Processing | Python 3 (layered SVP travel-time model) |
| 3D | Blender API (`bpy`, `bmesh`) |

---

## 👤 Author

**Léopold Latona**. Research project in wave physics and applied computer science (TIPE, French preparatory program).

## 📄 License

Released under the [MIT License](LICENSE).

## 📚 References

- X. Lurton, *Underwater Acoustics: Presentation and Applications*, Ifremer, 1998
- [RBR, Speed of sound in water](https://rbr-global.com/speed-of-sound-in-water/)
- [Makerguides, JSN-SR04T tutorial](https://www.makerguides.com/jsn-sr04t-arduino-tutorial/)
- [Ordnance Survey, Blender for geospatial projects](https://docs.os.uk/more-than-maps/deep-dive/using-blender-for-geospatial-projects)
