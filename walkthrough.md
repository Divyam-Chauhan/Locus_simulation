# LOCUS Digital Twin - Project Walkthrough

The LOCUS Digital Twin is now fully implemented as a PyGame Software-in-the-Loop simulation with an advanced tactical UI and highly robust mathematical validation.

## Changes Made
1. **Mathematical Engine:** Implemented absolute time-of-flight based on pixel distance ($343\text{ m/s}$ speed of sound scaled to $800\text{px/m}$). Built the TDOA calculation mapping $\Delta X$ and $\Delta Y$ mathematically to standard Polar Coordinates ($E=0^\circ, N=90^\circ, W=180^\circ, S=270^\circ$).
2. **Dual-Mode Execution:** 
   - **1x Mode:** Instant mathematical resolution. Static circle rendering removed per UX request.
   - **5x Slower Mode:** Visually animates the shockwave. As the wave intersects with each of the 4 microphones, they individually lock in their real-world microsecond timestamps.
3. **Refractory Lockout:** A UI element strictly enforces the $50,000\text{µs}$ ($50\text{ms}$) hardware timeout immediately after the first mic is hit.
4. **Friendly Fire Zone:** An internal $0.125\text{m}$ ($100\text{px}$) zone around the array. Clicks within this zone are marked in dark red, their math is aborted, and they are flagged as ignored by the system to prevent false alarms from the wearer's own weapon.
5. **Deduplicating History Log:** 
   - The HUD logs up to 8 threats, sorting them by time (e.g., "Just now", "20s ago", "2m ago").
   - If a new threat is detected within $\pm 5^\circ$ of an existing log, the old entry is overwritten with the precise new angle, its timer is reset, and it is bumped to the top of the list.
   - For memory management, entries older than 5 minutes ($300\text{s}$) are completely purged from the array to simulate ESP32 memory overhead handling.
6. **Time-Decay Fading & Ghost Lines:** 
   - History entries on the HUD start as bright Neon Green and slowly fade to dark gray over $60\text{s}$.
   - Every history entry also renders a persisting "Ghost Line" on the tactical grid matching its decay color, giving the wearer an immediate visual read on the hot zones in their perimeter without reading text.

## What Was Tested
- **Math Verification:** Executed a 10-point test suite on the TDOA engine confirming exact math resolution for cardinal and ordinal directions.
- **UX Render Loop:** Verified that the 1x mode instantaneously resolves. Verified that "5x Slower" properly ends its animation cycle past the final mic hit so the system un-freezes.
- **Memory Purge:** Monitored the history list to ensure elements purge correctly after reaching the maximum lifespan.
- **Deduplication Logic:** Clicking at $45^\circ$, then $47^\circ$, verified that only one entry remains at $47^\circ$. 

## Validation Results
The simulation flawlessly mirrors the PRD logic while incorporating high-level UI/UX additions that make the visual interface tactically viable and memory-efficient.
