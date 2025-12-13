# DiGear Jam Studio

A real-time Python audio mixing application that automatically synchronizes pitch (Key) and tempo (BPM) across multiple song stems. Built with Pygame, SoundDevice, and Rubberband.

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Features

  - **12 Audio Slots:** Load stems individually into 12 mixer slots.
  - **Auto-Sync:** The first stem loaded sets the "Master" BPM and Key/Mode. All subsequent stems are time-stretched and pitch-shifted to match.
  - **Stem Support:** Dedicated handling for Vocals, Bass, Drums, and Lead.
  - **Manual Override:** Manually force the Master Key, BPM, and Mode (Major/Minor).
  - **Customizable UI:** Support for custom color themes (JSON) and system fonts.
  - **Musical Notation:** Toggle between Sharp (\#) and Flat (b) notation.
  - **Save & Load:** Save your current Jam loop layout and mix to reload later.
  - **Bar Offset:** Shift specific stems by half the loop length to create new arrangements.

## Prerequisites

You need **Python 3.x** and the following libraries:

```bash
pip install numpy soundfile sounddevice pygame pyrubberband
```

## Folder Structure

The application requires specific folders to function.

1.  Create a `Songs` folder for your audio. (default songs will be provided at a later point for testing purposes)

**Directory Tree:**

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

### Audio Requirements

  - **Chopping:** Please chop all stems to your preferred 32 bars (All stems must be the exact same length).
  - **Missing Stems:** If you do not have stems for both modes (Major/Minor), the system falls back to using relative modes (pitch shifting by 3 semitones).

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

### Mouse Stuff

  - **Left Click (Empty Circle):** Open the Stem Select panel.
  - **Left Click (Slider):** Adjust volume for that slot.
  - **Right Click (Filled Circle):** Clear/Unload the slot.
  - **Left Click (Small Offset Button):** Shift the stem by 16 bars (swapping first/second half of the loop).

### Interface

  - **Top-Left (Manual Tune):** Force the engine to shift all active tracks to a specific Key, Mode, or BPM.
  - **Top-Right (Save/Load):** Save the current slot configurationor load a previous session.
  - **Also Top-Right (Options):** Open the configuration menu.

## Customization (Options Menu)

Tthe **Options** menu allows you to configure the app.

  - **Theme:** Select a color scheme from the `/themes` folder. You can create your own `.json` theme files following the structure of `default.json`.
  - **Font:** Select a display font from your installed system fonts.
  - **Notation:** Toggle the display of keys between **Sharps (\#)** and **Flats (b)**.

## Demo

### here lmao

https://github.com/user-attachments/assets/8180722c-60c3-44be-a130-c8213c66f7d9