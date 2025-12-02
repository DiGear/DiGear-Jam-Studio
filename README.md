# DiGear Jam Studio

A real-time Python audio mixing application that automatically synchronizes pitch (Key) and tempo (BPM) across multiple song stems. Built with Pygame, SoundDevice, and Rubberband.

## Features

- **8 Audio Slots:** Load stems individually into 8 mixer slots.
- **Auto-Sync:** The first stem loaded sets the "Master" BPM and Key/Mode. All subsequent stems are time-stretched and pitch-shifted to match.
- **Stem Support:** Dedicated handling for Vocals, Bass, Drums, and Lead.
- **Manual Override:** Manually force the Master Key, BPM, and Mode (Major/Minor)
- **Volume Control:** Individual volume sliders for each slot.
- **Bar Offset:** Stems can have their first half play in the second half of the loop, and vice versa.

## Prerequisites

You need **Python 3.x** and the following libraries:

```bash
pip install numpy soundfile sounddevice pygame pyrubberband
````

## Folder Structure

The application expects a specific folder structure to load songs correctly. Create a folder named `Songs` in the same directory as the script.
- NOTE: If you DO NOT have stems for both modes, the system falls back to using relative modes (adding or subtracting 3 semitones) so it should still mix fine.

- PLEASE CHOP ALL STEMS TO YOUR PREFERRED 32 BARS OF THE SONG (ALL stems must be the same)

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
  - **Left Click (Stem Shift Button)** Pressing the small shuffle icon in the corner of any slot shifts the bars by 16, effective swapping verses and chorus, etc.

### Interface

  - **Stem Select Panel:** Choose a song folder and a specific stem (Vocals, Bass, Lead, Drums).
  - **Manual Tuning:** Force the engine to shift all active tracks to a specific Key/Mode/BPM.

## Demo

### here lmao

https://github.com/user-attachments/assets/8180722c-60c3-44be-a130-c8213c66f7d9

