# 🛡️ LOCUS: Tactical Acoustic TDOA Digital Twin

### Software-in-the-Loop (SIL) Verification Engine

---

## 1. Executive Summary

**LOCUS** (Localization of Acoustic Impulse & Directional Threat System) is an edge-compute acoustic threat detection system designed for modern tactical environments. Traditional DSP sampling at high audio rates creates prohibitive CPU overhead and clock drift on low-power nodes.

This repository houses the **Software-in-the-Loop (SIL) Digital Twin** (`Locus_simulation.py`). Because physical acoustic testing with 140+ dB SPL shockwaves presents hardware constraints, this PyGame simulation mathematically validates the Time Difference of Arrival (TDOA) algorithm, wave propagation physics, and ESP32 hardware lockout logic before physical deployment.

---

## 2. Mathematical Foundation: Microsecond TDOA

```text
                +Y / North (Sensor N)
                       |
                       |
 -X / West (Sensor W)--+-- +X / East (Sensor E)
                       |
                       |
                -Y / South (Sensor S)

```

### 2.1 Physics & Propagation Constants

* **Speed of Sound ($c$):** $343 \text{ m/s}$ (at standard atmospheric baseline)


* **Array Baseline ($d$):** $15\text{ cm}$ ($0.15\text{ m}$) cross-array baseline


* **Maximum Time-of-Flight:** For a sensor separation $d$, maximum differential time delay $\Delta t_{max}$ across an axis is:

$$\Delta t_{max} = \frac{0.15\text{ m}}{343\text{ m/s}} \approx 437.32\text{ }\mu\text{s}$$




### 2.2 Standard Polar Angle TDOA Solver

The algorithm uses standard trigonometric angles where **East is $0^\circ$**, **North is $90^\circ$**, and the cycle completes at $360^\circ$[cite: 1].

1. **Calculate Microsecond Time Deltas:**
We invert the arrival times to point the vector *towards* the origin.

$$\Delta X = t_{\text{West}} - t_{\text{East}}$$


$$\Delta Y = t_{\text{South}} - t_{\text{North}}$$


2. **Calculate Vector Angle:**
Using the standard Cartesian 2-argument arctangent:

$$\theta = \text{atan2}(\Delta Y, \Delta X)$$


3. **Convert to Degrees & Wrap:**

$$\text{Angle} = (\text{degrees}(\theta) + 360) \pmod{360}$$



---

### 3. Hardware-Software Equivalence Architecture

The Python SIL simulation strictly mirrors the low-level C++ firmware executing on the physical ESP32-S3.

| Feature / Subsystem | Physical Hardware (ESP32-S3) | Python SIL Simulation (`Locus_simulation.py`) |
| :--- | :--- | :--- |
| **Signal Detection** | Piezo Disc → LM339 Comparator | Spatial distance-to-time wavefront collision |
| **Timer Resolution** | 1-MHz Clock (`esp_timer_get_time()`) | Absolute time-of-flight in µs |
| **Refractory Dead-Time** | 50 ms Hardware ISR Lockout | 50,000 µs software state-machine pause |
| **Execution UI** | OLED / Serial HUD (<50 ms) | Dual-Mode PyGame HUD (Real-Time & Slow-Mo) |

---

## 4. Installation & Execution

### Prerequisites

* Python 3.8+


* Pygame 2.5+



```bash
# Clone the repository
git clone https://github.com/Divyam-Chauhan/Locus_simulation.git
cd Locus_simulation

# Install dependencies
pip install -r requirements.txt

# Launch the Digital Twin
python Locus_simulation.py

```

### Interactive HUD Controls

* **Left Mouse Click:** Click anywhere on the tactical grid to simulate an acoustic blast origin.


* **`S` Key / Toggle Button:** Switch between **REAL-TIME (1x)** (instant calculation) and **SLOW-MOTION (5x)** (visualizes wavefront crossing the 15cm baseline).


* **`R` Key:** Reset sensor state machine and clear diagnostic panels.



---

---
