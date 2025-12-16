# DiGear Jam Studio

A real-time Python audio mixing application that automatically synchronizes pitch (Key) and tempo (BPM) across multiple song stems. Built with Pygame, SoundDevice, and Rubberband.

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Features

  - **12 Audio Slots:** Load stems individually into 12 mixer slots.
  - **Auto-Sync:** The first stem loaded sets the "Master" BPM and Key/Mode. All subsequent stems are time-stretched and pitch-shifted to match using `pyrubberband`.
  - **Stem Support:** Dedicated handling for Vocals, Bass, Drums, and Lead.
  - **Mixer Controls**: Per-track Volume sliders, **Mute**, and **Solo** functionality.
  - **Manual Override:** Manually force the Master Key, BPM, and Mode (Major/Minor).
  - **WAV Export:** Render your current live mix to a `.wav` file.
  - **Customizable UI:** Support for custom color themes (JSON) and system fonts.
  - **Musical Notation:** Toggle between Sharp (\#) and Flat (b) notation.
  - **Save & Load:** Save your current Jam loop layout and mix to reload later.
  - **Bar Offset:** Shift specific stems by half the loop length to create new arrangements.

## Prerequisites

You need **Python 3.x** and the following libraries:

```bash
pip install numpy soundfile sounddevice pygame pyrubberband tqdm
```

> **Note:** `pyrubberband` requires the **Rubberband CLI tool** to be installed on your system path. This specific app includes the binaries, but sometimes it needs to be installed to your system path anyways lol.
> * **Windows:** Download the CLI from [breakfastquay.com](https://breakfastquay.com/rubberband/) and add it to your PATH.
> * **Mac:** `brew install rubberband`
> * **Linux (this example is for arch-based systems):** `sudo pacman -S rubberband`

## Folder Structure

The application requires specific folders to function.

1.  Create a `Songs` folder for your audio. (this differs from the `stock songs` folder purely for organization purposes)

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
        ├── lead_minor.ogg
        ├
        ├── custom_stem.json | more info on this below
        └── custom_stem.ogg | more info on this below
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

### Custom Stem Format

You can add custom stems that DON'T follow the basic 4 stem model by putting them in the folder labelled `custom_stem.ogg` and `custom_stem.json`. The format is relatively similar to `meta.json`. The main difference is needing to specify the color it will have in the slot. Note that these DON'T use the same dual-mode system, and ALWAYS operates in relative mode (get around this by making 2 `.ogg` and `.json` files). It was just easier for me to code it that way lol. This code is a mess btw. Anyways enough rambling mid readme. Here's the format for custom stems:

```json
{
    "bpm": 128,
    "key": "F#",
    "scale": "minor"
    "color": [255, 0, 0]
}
```

*Valid scales:* major, minor, neutral (use this for stuff like percussion).

## Controls

### Mouse Stuff

 - **Left Click (Slot):** Add a stem to the slot.
 - **Right Click (Occupied Slot):** Clear/Unload the slot.
 - **Left Click (Slider):** Adjust volume for that slot.
 - **"M" Button:** Mute the track.
 - **"S" Button:** Solo the track (mutes all non-soloed tracks).
 - **"1/2" Button:** Shift the stem by 16 bars (swapping first/second half of the loop).

### Interface

 - **Restart Icon:** Resets the playback loop to the start.
 - **Play/Pause Icon:** Toggles the audio engine.
 - **Top-Left (Manual Tune):** Force the engine to shift all active tracks to a specific Key, Mode, or BPM.
 - **Top-Left (Reset):** Reinitalizes the app (this does not erase your settings)
 - **Top-Right (Save/Load):** Save the current slot configuration or load a previous session.
 - **Top-Right (Options):** Open the configuration menu.
 -  **Bottom-Right (Export WAV):** Renders the current loop to a `.wav` file.

## Customization (Options Menu)

The **Options** menu allows you to configure the app.

  - **Master Vol:** Sets the volume for the entire app.
  - **Theme:** Select a color scheme from the `/themes` folder. You can create your own `.json` theme files following the structure of `default.json`.
  - **Font:** Select a display font from your installed system fonts.
  - **Notation:** Toggle the display of keys between **Sharps (\#)** and **Flats (b)**.

## Demo

### here lmao

https://github.com/user-attachments/assets/8180722c-60c3-44be-a130-c8213c66f7d9
