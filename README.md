# DiGear Jam Studio

A real-time Python audio mixing application that automatically synchronizes pitch (Key) and tempo (BPM) across multiple song stems. Built with Pygame, SoundDevice, and Rubberband.

## Features

- **8 Audio Slots:** Load stems individually into 8 mixer slots.
- **Auto-Sync:** The first stem loaded sets the "Master" BPM and Key. All subsequent stems are time-stretched and pitch-shifted to match.
- **Stem Support:** Dedicated handling for Vocals, Bass, Drums, and Lead.
- **Manual Override:** Manually force the Master Key and Mode (Major/Minor) via the GUI. (BPM COMING WHEN I FIGURE IT OUT LOL)
- **Volume Control:** Individual volume sliders for each slot.

## Prerequisites

You need **Python 3.x** and the following libraries:

```bash
pip install numpy soundfile sounddevice pygame pyrubberband
````

## Folder Structure

The application expects a specific folder structure to load songs correctly. Create a folder named `Songs` in the same directory as the script.
- NOTE: If you DO NOT have stem for both modes, the system falls back to using relative modes (adding or subtracting 3 semitones) so it should still mix fine.

**Structure:**

```text
ROOT/
├── main.py
└── Songs/
    └── SongName/
        ├── meta.json
        ├── drums.ogg
        ├── vocals_major.ogg
        ├── vocals_minor.ogg
        ├── bass_major.ogg
        ├── bass_minor.ogg
        ├── lead_major.ogg
        └── lead_minor.ogg
```

### meta.json Format

Every song folder **must** contain a `meta.json` file with the song's original data:

```json
{
    "bpm": 128,
    "key": "F#",
    "scale": "minor"
}
```
*Valid scales:* major, minor.

## Controls

### Mouse

  - **Left Click (Empty Circle):** Open the Stem Select panel.
  - **Left Click (Slider):** Adjust volume for that slot.
  - **Right Click (Filled Circle):** Clear/Unload the slot.
  - **Top-Left Button:** Open Manual Tuning panel.

### Interface

  - **Stem Select Panel:** Choose a song folder and a specific stem (Vocals, Bass, Lead, Drums).
  - **Manual Tuning:** Force the engine to shift all active tracks to a specific Key/Mode.
