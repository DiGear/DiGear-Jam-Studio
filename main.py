import datetime
import json
import math
import os
import threading

import numpy as np
import pygame
import pyrubberband as rb
import sounddevice as sd
import soundfile as sf

# -------------------- this shit is vaguely related --------------------

KEY_TO_INT = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}

KEYS_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
KEYS_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

use_flat_notation = False

SAMPLE_RATE = 44100
BUFFER_SIZE = 2048
CHANNELS = 2
SONG_FOLDERS = ["Songs", "Stock Songs"]

if not os.path.exists("projects"):
    os.makedirs("projects")

# ----------- part of the pygame stuff -----------

pygame.init()

pygame.key.set_repeat(400, 30)

SCREEN_W, SCREEN_H = 840, 825
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

pygame.display.set_caption("DiGear Jam Studio")

# ensure themes folder exists
if not os.path.exists("themes"):
    os.makedirs("themes")

try:
    favicon = pygame.image.load("favicon.png")
    pygame.display.set_icon(favicon)
except:
    pass

# ---------- theme shit ----------

palette = {  # these are the same values used in the "default.json" this is just fallback shit
    # ALSO PEP 8 makes this unclear if it should be caps or not
    # but it looks better lowercased
    "bg_dark": (10, 10, 14),
    "bg_light": (25, 25, 35),
    "panel_bg": (20, 20, 25),
    "overlay": (0, 0, 0, 180),
    "popup_bg": (40, 40, 40),
    "popup_border": (0, 200, 80),
    "hover_outline": (128, 128, 128),
    "text_main": (240, 240, 255),
    "text_dim": (200, 200, 200),
    "text_dark": (0, 0, 0),
    "text_mode_label": (200, 255, 200),
    "slot_default": (80, 130, 255),
    "slot_empty": (60, 60, 60),
    "slot_vocals": (255, 230, 100),
    "slot_bass": (100, 255, 150),
    "slot_drums": (100, 230, 255),
    "slot_lead": (255, 120, 200),
    "accent": (80, 130, 255),
    "input_bg": (30, 30, 30),
    "input_border": (60, 60, 60),
    "input_active": (100, 100, 255),
    "scrollbar": (100, 100, 100),
    "slider_track": (120, 120, 120),
    "slider_fill": (0, 200, 80),
    "slider_knob": (255, 255, 255),
    "btn_manual": (0, 170, 60),
    "btn_save": (230, 120, 40),
    "btn_load": (60, 120, 210),
    "btn_ctrl": (80, 80, 80),
    "btn_icon": (198, 198, 198),
    "btn_confirm": (0, 160, 80),
    "btn_confirm_hl": (51, 179, 115),
    "btn_cancel": (160, 60, 60),
    "btn_cancel_hl": (179, 99, 99),
}

circle_color_empty = None
circle_color_default = None
stem_colors = {}
text_color = None
slider_color = None
slider_fill = None
slider_tip = None

FONT_SETTINGS = [  # i dont fucking know if PEP 8 specifies this to be capitalized or not
    # im making it capitalized since its like a global config thing even though its NOT a constant
    "Arial",  # default font
    20,
    22,
    28,
]

FONT_SMALL = None
FONT_MEDIUM = None
FONT_LARGE = None

current_theme_name = "default"


def save_config():
    config = {
        "theme": current_theme_name,
        "font": FONT_SETTINGS[0],
        "use_flats": use_flat_notation,
        "master_volume": audio_engine.master_volume,
    }
    try:
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)
        print("Config saved.")
    except Exception as e:
        print(f"Error saving config: {e}")


def update_fonts(font_name=None):
    global FONT_SMALL, FONT_MEDIUM, FONT_LARGE, FONT_SETTINGS
    if font_name:
        FONT_SETTINGS[0] = font_name

    try:
        FONT_SMALL = pygame.font.SysFont(FONT_SETTINGS[0], FONT_SETTINGS[1])
        FONT_MEDIUM = pygame.font.SysFont(FONT_SETTINGS[0], FONT_SETTINGS[2])
        FONT_LARGE = pygame.font.SysFont(FONT_SETTINGS[0], FONT_SETTINGS[3])
    except:
        FONT_SMALL = pygame.font.SysFont("Arial", FONT_SETTINGS[1])
        FONT_MEDIUM = pygame.font.SysFont("Arial", FONT_SETTINGS[2])
        FONT_LARGE = pygame.font.SysFont("Arial", FONT_SETTINGS[3])


def update_graphics_constants():
    global circle_color_empty, circle_color_default, stem_colors, text_color
    global slider_color, slider_fill, slider_tip

    circle_color_empty = palette["slot_empty"]
    circle_color_default = palette["slot_default"]

    stem_colors = {
        "vocals": palette["slot_vocals"],
        "bass": palette["slot_bass"],
        "drums": palette["slot_drums"],
        "lead": palette["slot_lead"],
    }

    text_color = palette["text_main"]
    slider_color = palette["slider_track"]
    slider_fill = palette["slider_fill"]
    slider_tip = palette["slider_knob"]


def load_theme(theme_name):
    global current_theme_name
    path = os.path.join("themes", theme_name + ".json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                for k, v in data.items():
                    if k in palette:
                        palette[k] = tuple(v)
            update_graphics_constants()
            current_theme_name = theme_name
            print(f"Loaded theme: {theme_name}.")
        except Exception as e:
            print(f"Failed to load theme: {e}")
    else:
        print(f"Theme not found: {path}")
    update_graphics_constants()


init_theme = "default"
init_font = "Arial"
init_flats = False

SLIDER_W = 120
SLIDER_H = 10
CIRCLE_RADIUS = 60

# -------------------- most of the functions are here --------------------


def draw_text_centered(text, font, color, target_rect):
    surf = font.render(text, True, color)
    text_rect = surf.get_rect(center=target_rect.center)
    screen.blit(surf, text_rect)


def get_display_key(key_str):
    if not key_str:
        return "???"
    idx = KEY_TO_INT.get(key_str, 0)
    return KEYS_FLAT[idx] if use_flat_notation else KEYS_SHARP[idx]


def key_shift_semitones(target_key, source_key):
    # calc semitone diff
    raw = KEY_TO_INT[target_key] - KEY_TO_INT[source_key]
    if raw > 6:
        raw -= 12
    elif raw < -6:
        raw += 12
    return raw


def match_bpm_timescale(original_bpm, master_bpm):
    # find best bpm match
    candidates = [
        original_bpm * 0.0625,
        original_bpm * 0.125,
        original_bpm * 0.25,
        original_bpm * 0.5,  # half time
        original_bpm,  # og
        original_bpm * 2,  # double time
        original_bpm * 4,
        original_bpm * 8,
        original_bpm * 16,
    ]
    return min(candidates, key=lambda b: abs(b - master_bpm))


def darken_color(color, factor=0.6):  # one less hard-coded thing
    r, g, b = color
    return (int(r * factor), int(g * factor), int(b * factor))


def lighten_color(color, factor=1.5):
    r, g, b = color
    return (
        min(255, int(r * factor)),
        min(255, int(g * factor)),
        min(255, int(b * factor)),
    )


def lerp_color(c1, c2, t):
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def load_audio_data(path):
    audio, sr = sf.read(path, dtype="float32")
    if audio.ndim == 1:
        audio = np.stack([audio, audio], axis=1)
    if sr != SAMPLE_RATE:
        print(f"Warning: samplerate mismatch in: {path}")
    peak = np.max(np.abs(audio))
    if peak:
        audio /= peak
    return audio


def draw_slider(x, y, w, h, value):
    track_outline_col = darken_color(slider_color, factor=0.4)
    knob_outline_col = darken_color(slider_tip, factor=0.4)
    pygame.draw.rect(screen, slider_color, (x, y, w, h))
    filled = int(w * value)
    if filled > 0:
        pygame.draw.rect(screen, slider_fill, (x, y, filled, h))
    pygame.draw.rect(screen, track_outline_col, (x, y, w, h), 2)
    knob_x = x + filled
    knob_y = y + h // 2
    knob_radius = h // 2 + 2
    pygame.draw.circle(screen, slider_tip, (knob_x, knob_y), knob_radius)
    pygame.draw.circle(screen, knob_outline_col, (knob_x, knob_y), knob_radius, 2)


def draw_half_offset(surface, x, y, active, hovered):
    base_color = palette["accent"] if active else (60, 60, 60)

    if hovered:
        color_bg = lighten_color(base_color, 1.2)
    else:
        color_bg = base_color

    color_border = palette["input_border"]
    color_text = (255, 255, 255)

    rect = pygame.Rect(x, y, 32, 32)

    pygame.draw.rect(surface, color_bg, rect, border_radius=4)
    pygame.draw.rect(surface, color_border, rect, 2, border_radius=4)

    font = FONT_SMALL
    txt = font.render("1/2", True, color_text)
    txt_rect = txt.get_rect(center=rect.center)
    surface.blit(txt, txt_rect)


def draw_mute_solo(surface, x, y, muted, soloed, mx, my):
    btn_size = 20
    gap = 4

    # mute Button
    r_mute = pygame.Rect(x, y, btn_size, btn_size)

    mute_base = palette["btn_save"] if muted else (60, 60, 60)
    if r_mute.collidepoint(mx, my):
        col_m = lighten_color(mute_base, 1.2)
    else:
        col_m = mute_base

    pygame.draw.rect(surface, col_m, r_mute, border_radius=3)
    pygame.draw.rect(surface, (150, 150, 150), r_mute, 1, border_radius=3)

    m_surf = FONT_SMALL.render("M", True, (255, 255, 255))
    surface.blit(m_surf, m_surf.get_rect(center=r_mute.center))

    # solo Button
    r_solo = pygame.Rect(x + btn_size + gap, y, btn_size, btn_size)

    solo_base = palette["btn_load"] if soloed else (60, 60, 60)
    if r_solo.collidepoint(mx, my):
        col_s = lighten_color(solo_base, 1.2)
    else:
        col_s = solo_base

    text_col_s = (255, 255, 255)

    pygame.draw.rect(surface, col_s, r_solo, border_radius=3)
    pygame.draw.rect(surface, (150, 150, 150), r_solo, 1, border_radius=3)

    s_surf = FONT_SMALL.render("S", True, text_col_s)
    surface.blit(s_surf, s_surf.get_rect(center=r_solo.center))

    return r_mute, r_solo


def draw_dynamic_text(surface, text, font, center_x, center_y, max_width, color):
    # draws text with outline and scales if too big
    if not text:
        return

    text_surf = font.render(text, True, color)
    outline_surf = font.render(text, True, palette["text_dark"])

    width, height = text_surf.get_size()
    if width > max_width:
        scale_factor = max_width / width
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        text_surf = pygame.transform.smoothscale(text_surf, (new_width, new_height))
        outline_surf = pygame.transform.smoothscale(
            outline_surf, (new_width, new_height)
        )

    rect = text_surf.get_rect(center=(center_x, center_y))

    # draw outline
    offsets = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
    for dx, dy in offsets:
        surface.blit(outline_surf, (rect.x + dx, rect.y + dy))
    surface.blit(text_surf, rect)


# -------------------- classes --------------------


class Slot(threading.Thread):
    def __init__(self, idx):
        super().__init__()
        self.idx = idx
        self.daemon = True  # ensure thread dies when app closes

        # audio state
        self.empty = True
        self.stem = None
        self.song_name = None
        self.type = None
        self.key = None
        self.scale = None
        self.bpm = None
        self.volume = 1.0
        self.target_volume = 1.0
        self.offset = 0
        self.half = 0
        self.mute = False
        self.solo = False

        # thread synchronization
        self.start_event = threading.Event()
        self.done_event = threading.Event()
        self.output_buffer = None

        self.req_pos = 0
        self.req_frames = 0
        self.req_channels = 2

    def run(self):
        while True:
            self.start_event.wait()
            self.start_event.clear()

            self.process_audio()

            self.done_event.set()

    def process_audio(self):
        # silence mega mayhem
        self.output_buffer = np.zeros(
            (self.req_frames, self.req_channels), dtype=np.float32
        )

        if self.empty or self.stem is None:
            return

        audio = self.stem.astype(np.float32)
        length = len(audio)
        if length == 0:
            return

        current_offset = (length // 2) if self.half == 1 else 0
        offset_pos = (self.req_pos + current_offset) % length

        end = offset_pos + self.req_frames

        if end <= length:
            chunk = audio[offset_pos:end]
        else:
            wrap = end - length
            part1 = audio[offset_pos:length]
            part2 = audio[0:wrap]
            chunk = np.vstack((part1, part2))

        if chunk.ndim < 2:
            chunk = np.hstack([chunk, chunk])

        if chunk.shape[0] != self.req_frames:
            if chunk.shape[0] > self.req_frames:
                chunk = chunk[: self.req_frames]
            else:
                pad = self.req_frames - chunk.shape[0]
                chunk = np.vstack(
                    (chunk, np.zeros((pad, self.req_channels), dtype=np.float32))
                )

        self.output_buffer = chunk * self.volume


class AudioEngine:
    def __init__(self, slots, samplerate=44100):
        self.slots = slots
        self.sr = samplerate
        self.position = 0
        self.max_length = 0
        self.stream = None
        self.master_volume = 1.0

    def update_max_length(self):
        lengths = [
            len(s.stem) for s in self.slots if not s.empty and s.stem is not None
        ]
        self.max_length = max(lengths) if lengths else 0

    def audio_callback(self, outdata, frames, time, status):
        if status:
            print("Audio callback status:", status)

        active_lengths = [
            len(s.stem) for s in self.slots if not s.empty and s.stem is not None
        ]
        self.max_length = max(active_lengths) if active_lengths else 0

        if self.max_length == 0:
            outdata.fill(0)
            return

        self.position %= self.max_length

        for slot in self.slots:
            slot.req_pos = self.position
            slot.req_frames = frames
            slot.req_channels = CHANNELS
            slot.start_event.set()

        for slot in self.slots:
            slot.done_event.wait()
            slot.done_event.clear()

        mix = np.zeros((frames, CHANNELS), dtype=np.float32)

        any_solo = any(s.solo for s in self.slots if not s.empty)

        for slot in self.slots:
            if slot.empty:
                continue

            should_play = False
            if any_solo:
                if slot.solo:
                    should_play = True
            else:
                if not slot.mute:
                    should_play = True

            if should_play:
                mix += slot.output_buffer

        mix *= self.master_volume

        outdata[:] = np.clip(mix, -1.0, 1.0)

        self.position += frames
        self.position %= self.max_length

    def restart(self):
        self.position = 0
        if self.stream is None or not self.stream.active:
            self.start()

    def start(self):
        self.update_max_length()
        self.stream = sd.OutputStream(
            samplerate=self.sr,
            channels=CHANNELS,
            blocksize=BUFFER_SIZE,
            dtype="float32",
            callback=self.audio_callback,
        )
        self.stream.start()
        print("Audio engine started.")

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            print("Audio engine stopped.")


# -------------------- the rest of the pygame bullshit, did you know i hate pygame? --------------------
# this pygame shit sucks so much we shoulda used something else man idk
# pyqt6?? some tkinter shit???
# ALSO PYGAME HAS A UI LIBRARY I COULD HAVE DOWNLOADED FUCKKKKK
# dude what is arcade
# dear pygui what am i writing a letter


class TextInput:
    def __init__(self, x, y, w, h, text=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = palette["input_border"]
        self.color_active = palette["input_active"]
        self.color = self.color_inactive
        self.text = text
        self.font = FONT_MEDIUM
        self.txt_surface = self.font.render(text, True, palette["text_main"])
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive
            return False

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    if len(event.unicode) > 0 and (
                        event.unicode.isalnum() or event.unicode in " .-_"
                    ):
                        self.text += event.unicode
                self.txt_surface = self.font.render(
                    self.text, True, palette["text_main"]
                )
        return False

    def draw(self, screen):
        pygame.draw.rect(screen, palette["input_bg"], self.rect)
        screen.blit(self.txt_surface, (self.rect.x + 10, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)


class DropdownMenu:
    def __init__(self, x, y, w, h, options, default_index=0, max_display_items=5):
        self.rect = pygame.Rect(x, y, w, h)
        self.options = options
        self.index = default_index
        self.is_open = False
        self.font = FONT_SMALL
        self.active_option_color = palette["input_border"]
        self.hover_color = palette["accent"]
        self.bg_color = palette["input_bg"]
        self.text_color = palette["text_main"]
        self.border_color = palette["scrollbar"]
        self.scroll_y = 0
        self.max_display_items = max_display_items
        self.item_height = h
        self.scrollbar_width = 15

    def get_selected(self):
        if not self.options:
            return None
        if 0 <= self.index < len(self.options):
            return self.options[self.index]
        return None

    def update_options(self, new_options):
        self.options = new_options
        if self.index >= len(self.options):
            self.index = 0
        self.scroll_y = 0

    def draw(self, screen):
        self.bg_color = palette["input_bg"]
        self.text_color = palette["text_main"]
        self.border_color = palette["scrollbar"]

        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)

        text_val = self.options[self.index] if self.options else "---"
        if os.path.sep in str(text_val):
            text_val = os.path.basename(text_val)

        surf = self.font.render(str(text_val), True, self.text_color)

        text_y = self.rect.y + (self.rect.height - surf.get_height()) // 2
        screen.blit(surf, (self.rect.x + 10, text_y))

    def draw_list(self, screen):
        if self.is_open and self.options:
            mx, my = pygame.mouse.get_pos()

            current_bg = palette["input_bg"]
            current_border = palette["scrollbar"]
            current_text = palette["text_main"]
            current_hover = palette["accent"]
            current_active = palette["input_border"]

            num_items = len(self.options)
            total_height = num_items * self.item_height
            display_count = min(num_items, self.max_display_items)
            display_height = display_count * self.item_height

            list_rect = pygame.Rect(
                self.rect.x,
                self.rect.y + self.rect.height,
                self.rect.width,
                display_height,
            )
            pygame.draw.rect(screen, current_bg, list_rect)

            old_clip = screen.get_clip()
            screen.set_clip(list_rect)

            start_y = list_rect.y - self.scroll_y

            for i, opt in enumerate(self.options):
                opt_y = start_y + (i * self.item_height)

                if opt_y + self.item_height < list_rect.y or opt_y > list_rect.bottom:
                    continue

                opt_rect = pygame.Rect(
                    self.rect.x,
                    opt_y,
                    self.rect.width - self.scrollbar_width,
                    self.item_height,
                )

                is_hovered = opt_rect.collidepoint(mx, my) and list_rect.collidepoint(
                    mx, my
                )

                color = current_hover if is_hovered else current_active

                pygame.draw.rect(screen, color, opt_rect)
                pygame.draw.rect(screen, current_border, opt_rect, 1)

                display_text = str(opt)
                if os.path.sep in display_text:
                    display_text = os.path.basename(display_text)

                surf = self.font.render(display_text, True, current_text)

                text_y = opt_rect.y + (self.item_height - surf.get_height()) // 2
                screen.blit(surf, (opt_rect.x + 10, text_y))

            screen.set_clip(old_clip)

            pygame.draw.rect(screen, current_border, list_rect, 2)

            if total_height > display_height:
                sb_bg_rect = pygame.Rect(
                    self.rect.right - self.scrollbar_width,
                    list_rect.y,
                    self.scrollbar_width,
                    display_height,
                )
                pygame.draw.rect(screen, current_bg, sb_bg_rect)

                ratio = display_height / total_height
                thumb_h = max(20, display_height * ratio)

                max_scroll = total_height - display_height
                scroll_ratio = self.scroll_y / max_scroll
                thumb_y = list_rect.y + scroll_ratio * (display_height - thumb_h)

                sb_thumb_rect = pygame.Rect(
                    self.rect.right - self.scrollbar_width + 2,
                    thumb_y,
                    self.scrollbar_width - 4,
                    thumb_h,
                )
                pygame.draw.rect(
                    screen, palette["scrollbar"], sb_thumb_rect, border_radius=4
                )

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()

            if self.is_open and self.options:
                display_height = (
                    min(len(self.options), self.max_display_items) * self.item_height
                )
                list_rect = pygame.Rect(
                    self.rect.x,
                    self.rect.y + self.rect.height,
                    self.rect.width,
                    display_height,
                )

                if list_rect.collidepoint(mx, my):
                    total_height = len(self.options) * self.item_height
                    max_scroll = max(0, total_height - display_height)

                    scroll_speed = 20
                    self.scroll_y -= event.y * scroll_speed

                    if self.scroll_y < 0:
                        self.scroll_y = 0
                    if self.scroll_y > max_scroll:
                        self.scroll_y = max_scroll
                    return True

            elif not self.is_open and self.rect.collidepoint(mx, my):
                if self.options:
                    if event.y > 0:
                        self.index -= 1
                    elif event.y < 0:
                        self.index += 1

                    self.index = max(0, min(self.index, len(self.options) - 1))
                    return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            if self.is_open and self.options:
                display_height = (
                    min(len(self.options), self.max_display_items) * self.item_height
                )
                list_rect = pygame.Rect(
                    self.rect.x,
                    self.rect.y + self.rect.height,
                    self.rect.width,
                    display_height,
                )

                if list_rect.collidepoint(mx, my):
                    if mx > self.rect.right - self.scrollbar_width:
                        return True

                    relative_y = my - list_rect.y + self.scroll_y
                    idx = int(relative_y // self.item_height)

                    if 0 <= idx < len(self.options):
                        self.index = idx
                        self.is_open = False
                        return True

                if not self.rect.collidepoint(mx, my) and not list_rect.collidepoint(
                    mx, my
                ):
                    self.is_open = False

            if self.rect.collidepoint(mx, my):
                self.is_open = not self.is_open
                return True

        return False


# -------------------- slot shit --------------------

slots = []
for i in range(12):
    s = Slot(i)
    s.start()
    slots.append(s)

audio_engine = AudioEngine(slots, SAMPLE_RATE)

init_theme = "default"
init_font = "Arial"
init_flats = False

if os.path.exists("config.json"):
    try:
        with open("config.json", "r") as f:
            config_data = json.load(f)
            init_theme = config_data.get("theme", "default")
            init_font = config_data.get("font", "Arial")
            init_flats = config_data.get("use_flats", False)
            init_vol = config_data.get("master_volume", 1.0)
            audio_engine.master_volume = init_vol
            print("Config loaded.")
    except Exception as e:
        print(f"Error loading config: {e}")

use_flat_notation = init_flats
update_fonts(init_font)
load_theme(init_theme)

master_bpm = None
master_key = None
master_scale = None
manual_override_open = False

dragging_slider = None
panel_open = False
selected_slot = None

# relative/parallel mode shit
use_relative_mode = False

audio_engine.start()

options_open = False
available_themes = [
    f.replace(".json", "") for f in os.listdir("themes") if f.endswith(".json")
]
available_fonts = pygame.font.get_fonts()
available_fonts.sort()
if "arial" not in available_fonts and len(available_fonts) > 0:  # yeah this thing lol
    available_fonts.insert(0, "arial")

all_fonts = available_fonts.copy()


def get_idx(lst, item):
    try:
        return lst.index(item)
    except ValueError:
        return 0


# option s
dropdown_theme = DropdownMenu(
    350,
    200,
    200,
    35,
    available_themes,
    default_index=get_idx(available_themes, current_theme_name),
    max_display_items=15,
)
dropdown_font = DropdownMenu(
    350,
    270,
    200,
    35,
    available_fonts,
    default_index=get_idx(available_fonts, FONT_SETTINGS[0]),
    max_display_items=14,
)

btn_notation_toggle = pygame.Rect(350, 340, 200, 35)

saving_mode = False
loading_mode = False
save_input = TextInput(
    (SCREEN_W - 300) // 2, (SCREEN_H - 100) // 2 + 20, 300, 40, text="My_Jam"
)
dropdown_load_project = None


def reset_master():
    global master_bpm, master_key, master_scale
    master_bpm = None
    master_key = None
    master_scale = None


def get_song_list():
    all_songs = []

    for folder in SONG_FOLDERS:
        if not os.path.exists(folder):
            os.makedirs(folder)
            continue

        songs = [
            os.path.join(folder, x)
            for x in os.listdir(folder)
            if os.path.isdir(os.path.join(folder, x))
        ]
        all_songs.extend(songs)

    all_songs.sort(key=lambda x: os.path.basename(x).lower())

    return all_songs


def add_stem_to_slot(slot_id, song_folder, stem_type):
    global master_bpm, master_key, master_scale

    meta_path = os.path.join(song_folder, "meta.json")
    with open(meta_path, "r") as f:
        meta = json.load(f)

    song_key = meta["key"]
    song_bpm = meta["bpm"]

    print(f"\nLoading stem '{stem_type}' from: {song_folder}")

    # set master if first track
    if master_bpm is None:
        master_bpm = song_bpm
        master_key = song_key
        master_scale = meta.get("scale", "major")
        print(f"Master set to {master_key} {master_scale}.")

    file_to_load = loaded_scale = ""

    if stem_type == "drums":
        file_to_load = "drums.ogg"
        loaded_scale = "neutral"
    else:
        target_scale = master_scale

        target_path = os.path.join(song_folder, f"{stem_type}_{target_scale}.ogg")

        if os.path.exists(target_path):
            file_to_load = f"{stem_type}_{target_scale}.ogg"
            loaded_scale = target_scale
        else:
            fallback_scale = "minor" if target_scale == "major" else "major"
            fallback_path = os.path.join(
                song_folder, f"{stem_type}_{fallback_scale}.ogg"
            )

            if os.path.exists(fallback_path):
                file_to_load = f"{stem_type}_{fallback_scale}.ogg"
                loaded_scale = fallback_scale
                print(
                    f"No matching mode file found. Falling back to the relative mode of {loaded_scale}."
                )
            else:
                print(f"ERROR: No stem files found for {stem_type}.")
                return

    # load Audio
    full_path = os.path.join(song_folder, file_to_load)
    stem_audio = load_audio_data(full_path)

    # time Stretch
    adjusted_bpm = match_bpm_timescale(song_bpm, master_bpm)
    stretch_ratio = master_bpm / adjusted_bpm
    if stretch_ratio != 1.0:
        print(
            f"Applying time stretch: {song_bpm} base BPM -> {adjusted_bpm} multiple BPM -> {master_bpm} adjusted BPM"
        )
        stem_audio = rb.time_stretch(stem_audio, SAMPLE_RATE, stretch_ratio)

    # pitch shift (now with fallback shit)
    if stem_type != "drums":
        semis = key_shift_semitones(master_key, song_key)
        if loaded_scale == master_scale:
            pass

        elif loaded_scale != "neutral":
            print("Applying relative mode offset.")
            if loaded_scale == "minor" and master_scale == "major":
                semis -= 3
            elif loaded_scale == "major" and master_scale == "minor":
                semis += 3

        if semis != 0:
            print(f"Pitch shift: {semis:+d} semitones.")
            stem_audio = rb.pitch_shift(stem_audio, SAMPLE_RATE, semis)

    # sync length
    if audio_engine.max_length == 0:
        audio_engine.max_length = len(stem_audio)

    master_length = audio_engine.max_length
    cur_len = len(stem_audio)

    # micro stretch to align samples exactly
    if cur_len != master_length:
        ratio = master_length / cur_len
        if 0.5 < ratio < 2.0:
            stem_audio = rb.time_stretch(stem_audio, SAMPLE_RATE, 1 / ratio)
            if len(stem_audio) > master_length:
                stem_audio = stem_audio[:master_length]
            elif len(stem_audio) < master_length:
                pad = master_length - len(stem_audio)
                stem_audio = np.vstack(
                    (stem_audio, np.zeros((pad, stem_audio.shape[1]), dtype=np.float32))
                )

    slot = slots[slot_id]
    slot.empty = False
    slot.stem = stem_audio
    slot.song_name = os.path.basename(song_folder)
    slot.type = stem_type
    slot.key = song_key
    slot.scale = loaded_scale
    slot.bpm = song_bpm
    slot.offset = 0
    slot.half = 0

    print("Stem loaded.")
    audio_engine.update_max_length()


def clear_slot(i):
    slot = slots[i]
    slot.empty = True
    slot.stem = None
    slot.song_name = None
    slot.type = None
    slot.volume = 1.0
    slot.target_volume = 1.0
    slot.offset = 0
    slot.half = 0
    slot.mute = False
    slot.solo = False
    print(f"Slot {i} cleared.")


def shift_slot(i):
    slot = slots[i]
    slot.half = 1 if slot.half == 0 else 0


def toggle_master_playback():
    (
        audio_engine.stop
        if audio_engine.stream and audio_engine.stream.active
        else audio_engine.start
    )()


# -------------------- saving and loading and exporting --------------------


def export_mix_to_wav(filename="export.wav"):
    print("Starting export...")

    max_len = audio_engine.max_length
    if max_len == 0:
        print("ERROR: No audio data to export.")
        return

    master_mix = np.zeros((max_len, CHANNELS), dtype=np.float32)

    for slot in slots:
        if slot.empty or slot.stem is None:
            continue

        if slot.mute:
            continue

        audio = slot.stem
        sl_len = len(audio)

        offset_samples = (sl_len // 2) if slot.half == 1 else 0
        processed_audio = np.roll(audio, -offset_samples, axis=0)

        if sl_len < max_len:
            repeats = (max_len // sl_len) + 1
            tiled = np.tile(processed_audio, (repeats, 1))
            processed_audio = tiled[:max_len]
        elif sl_len > max_len:
            processed_audio = processed_audio[:max_len]
        master_mix += processed_audio * slot.volume

    master_mix *= audio_engine.master_volume
    master_mix = np.clip(master_mix, -1.0, 1.0)

    try:
        sf.write(filename, master_mix, SAMPLE_RATE)
        print(f"Exported to: {filename}")
    except Exception as e:
        print(f"Export failed: {e}")


def save_project(filename="project_data.json"):
    data = {
        "master": {
            "bpm": master_bpm,
            "key": master_key,
            "scale": master_scale,
            "master_volume": audio_engine.master_volume,
        },
        "slots": [],
    }

    for i, slot in enumerate(slots):
        if not slot.empty:
            slot_data = {
                "index": i,
                "song_name": slot.song_name,
                "type": slot.type,
                "volume": slot.volume,
                "half": slot.half,
                "mute": slot.mute,
                "solo": slot.solo,
                "detected_key": slot.key,
                "detected_scale": slot.scale,
            }
            data["slots"].append(slot_data)

    full_path = os.path.join("projects", filename)

    try:
        with open(full_path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Project saved to: {full_path}")
    except Exception as e:
        print(f"Error saving: {e}")


def load_project(filename):
    full_path = os.path.join("projects", filename)
    if not os.path.exists(full_path):
        print("No save file found.")
        return

    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill(palette["overlay"])
    screen.blit(overlay, (0, 0))

    wait_w, wait_h = 300, 100
    wait_rect = pygame.Rect(
        (SCREEN_W - wait_w) // 2, (SCREEN_H - wait_h) // 2, wait_w, wait_h
    )
    pygame.draw.rect(screen, palette["popup_bg"], wait_rect)
    pygame.draw.rect(screen, palette["popup_border"], wait_rect, 3)
    draw_text_centered(
        "Loading Project...", FONT_LARGE, palette["text_main"], wait_rect
    )
    pygame.display.flip()

    try:
        with open(full_path, "r") as f:
            data = json.load(f)

        audio_engine.stop()

        global master_bpm, master_key, master_scale
        master_bpm = data["master"]["bpm"]
        master_key = data["master"]["key"]
        master_scale = data["master"]["scale"]

        if "master_volume" in data["master"]:
            audio_engine.master_volume = data["master"]["master_volume"]

        for i in range(12):
            clear_slot(i)

        audio_engine.max_length = 0

        for slot_data in data["slots"]:
            idx = slot_data["index"]
            song_name = slot_data["song_name"]
            stem_type = slot_data["type"]

            song_path = None
            for folder in SONG_FOLDERS:
                potential_path = os.path.join(folder, song_name)
                if os.path.exists(potential_path):
                    song_path = potential_path
                    break

            if song_path:
                add_stem_to_slot(idx, song_path, stem_type)

                s = slots[idx]
                s.volume = slot_data.get("volume", 1.0)
                s.target_volume = slot_data.get("volume", 1.0)
                s.half = slot_data.get("half", 0)
                s.mute = slot_data.get("mute", False)
                s.solo = slot_data.get("solo", False)
            else:
                print(f"'{song_name}' not found during load.")

        audio_engine.start()
        print("Project loaded successfully.")

    except Exception as e:
        print(f"Error loading project: {e}")


# stem select
dropdown_song_select = DropdownMenu(
    240, 200, 360, 35, get_song_list(), max_display_items=16
)
dropdown_stem_type_select = DropdownMenu(
    240, 260, 360, 35, ["vocals", "bass", "lead", "drums"], max_display_items=4
)

# manual tune
dropdown_manual_key = DropdownMenu(
    220,
    235,
    180,
    35,
    KEYS_FLAT if use_flat_notation else KEYS_SHARP,
    max_display_items=12,
)
dropdown_manual_scale = DropdownMenu(
    440, 235, 180, 35, ["major", "minor"], max_display_items=2
)
input_manual_bpm = TextInput(370, 200, 100, 35)

# -------------------- main loop --------------------

dragging_master_vol = False  # gurhugf

clock = pygame.time.Clock()
running = True
pulse_timer = 0

while running:
    # bg
    screen.fill(palette["bg_dark"])

    # grid
    grid_size = 40
    for x in range(0, SCREEN_W, grid_size):
        pygame.draw.line(screen, palette["bg_light"], (x, 0), (x, SCREEN_H))
    for y in range(0, SCREEN_H, grid_size):
        pygame.draw.line(screen, palette["bg_light"], (0, y), (SCREEN_W, y))

    mx, my = pygame.mouse.get_pos()

    input_blocked = (
        panel_open
        or manual_override_open
        or options_open
        or saving_mode
        or loading_mode
    )

    # slider sm64
    lerp_speed = 0.33

    for s in slots:
        if s.volume != s.target_volume:
            diff = s.target_volume - s.volume
            if abs(diff) < 0.001:
                s.volume = s.target_volume
            else:
                s.volume += diff * lerp_speed

    # manual tune button
    mt_btn_rect = pygame.Rect(20, 20, 200, 40)
    mt_btn_color = palette["btn_manual"]

    if mt_btn_rect.collidepoint(mx, my) and not input_blocked:
        mt_outline_col = lighten_color(mt_btn_color, factor=1.2)
    else:
        mt_outline_col = darken_color(mt_btn_color)

    pygame.draw.rect(screen, mt_btn_color, mt_btn_rect, border_radius=4)
    pygame.draw.rect(screen, mt_outline_col, mt_btn_rect, 4, border_radius=4)

    draw_text_centered(
        "Set Manual Tuning", FONT_MEDIUM, palette["text_main"], mt_btn_rect
    )

    # export WAV button
    btn_exp_w = 140
    btn_exp_h = 40
    btn_exp_rect = pygame.Rect(
        SCREEN_W - btn_exp_w - 20, SCREEN_H - btn_exp_h - 20, btn_exp_w, btn_exp_h
    )

    exp_col = palette["accent"]

    if btn_exp_rect.collidepoint(mx, my) and not input_blocked:
        exp_outline = lighten_color(exp_col, 1.2)
    else:
        exp_outline = darken_color(exp_col)

    pygame.draw.rect(screen, exp_col, btn_exp_rect, border_radius=4)
    pygame.draw.rect(screen, exp_outline, btn_exp_rect, 4, border_radius=4)

    draw_text_centered("Export WAV", FONT_MEDIUM, palette["text_main"], btn_exp_rect)

    # save and load buttons
    btn_save_rect = pygame.Rect(SCREEN_W - 320, 20, 90, 40)
    btn_load_rect = pygame.Rect(SCREEN_W - 220, 20, 90, 40)

    save_col = palette["btn_save"]
    load_col = palette["btn_load"]

    if btn_save_rect.collidepoint(mx, my) and not input_blocked:
        save_outline = lighten_color(save_col, 1.2)
    else:
        save_outline = darken_color(save_col)

    if btn_load_rect.collidepoint(mx, my) and not input_blocked:
        load_outline = lighten_color(load_col, 1.2)
    else:
        load_outline = darken_color(load_col)

    pygame.draw.rect(screen, save_col, btn_save_rect, border_radius=4)
    pygame.draw.rect(screen, save_outline, btn_save_rect, 4, border_radius=4)

    pygame.draw.rect(screen, load_col, btn_load_rect, border_radius=4)
    pygame.draw.rect(screen, load_outline, btn_load_rect, 4, border_radius=4)

    draw_text_centered("Save", FONT_MEDIUM, palette["text_main"], btn_save_rect)
    draw_text_centered("Load", FONT_MEDIUM, palette["text_main"], btn_load_rect)

    # option button
    btn_opt_rect = pygame.Rect(SCREEN_W - 120, 20, 90, 40)

    if btn_opt_rect.collidepoint(mx, my) and not input_blocked:
        opt_outline = lighten_color(palette["btn_ctrl"], 1.2)
    else:
        opt_outline = darken_color(palette["btn_ctrl"])

    pygame.draw.rect(screen, palette["btn_ctrl"], btn_opt_rect, border_radius=4)
    pygame.draw.rect(screen, opt_outline, btn_opt_rect, 4, border_radius=4)
    draw_text_centered("Options", FONT_MEDIUM, palette["text_main"], btn_opt_rect)

    # what
    pulse_val = 0.0
    if audio_engine.stream and audio_engine.stream.active:
        pulse_timer += clock.get_time()

    if master_bpm and master_bpm > 0:
        ms_per_beat = 60000 / master_bpm

        base_sine_wave = math.sin(
            (pulse_timer * 2 * math.pi) / ms_per_beat - (math.pi / 2)
        )

        tanh_gain = 3.0
        curved_sin = math.tanh(base_sine_wave * tanh_gain)  # math tuah

        max_val = math.tanh(tanh_gain)
        pulse_val = (curved_sin / max_val + 1) / 2

    # pause play restart button
    ctrl_btn_w = 60
    ctrl_btn_h = 40
    ctrl_gap = 12
    ctrl_y = 20
    total_ctrl_w = (ctrl_btn_w * 2) + ctrl_gap
    ctrl_start_x = (SCREEN_W // 2) - (total_ctrl_w // 2)

    btn_restart_rect = pygame.Rect(ctrl_start_x, ctrl_y, ctrl_btn_w, ctrl_btn_h)
    btn_play_rect = pygame.Rect(
        ctrl_start_x + ctrl_btn_w + ctrl_gap, ctrl_y, ctrl_btn_w, ctrl_btn_h
    )

    btn_ctrl_col = palette["btn_ctrl"]
    icon_col = palette["btn_icon"]

    # restart button
    if btn_restart_rect.collidepoint(mx, my) and not input_blocked:
        restart_outline = lighten_color(btn_ctrl_col, 1.2)
    else:
        restart_outline = darken_color(btn_ctrl_col)

    pygame.draw.rect(screen, btn_ctrl_col, btn_restart_rect, border_radius=2)
    pygame.draw.rect(screen, restart_outline, btn_restart_rect, 4, border_radius=2)

    pygame.draw.rect(
        screen,
        icon_col,
        (btn_restart_rect.centerx - 10, btn_restart_rect.centery - 8, 4, 16),
    )
    pts_restart = [
        (btn_restart_rect.centerx - 5, btn_restart_rect.centery),
        (btn_restart_rect.centerx + 9, btn_restart_rect.centery - 8),
        (btn_restart_rect.centerx + 9, btn_restart_rect.centery + 8),
    ]
    pygame.draw.polygon(screen, icon_col, pts_restart)

    # pause button
    if btn_play_rect.collidepoint(mx, my) and not input_blocked:
        play_outline = lighten_color(btn_ctrl_col, 1.2)
    else:
        play_outline = darken_color(btn_ctrl_col)

    pygame.draw.rect(screen, btn_ctrl_col, btn_play_rect, border_radius=2)
    pygame.draw.rect(screen, play_outline, btn_play_rect, 4, border_radius=2)

    is_playing = audio_engine is not None and audio_engine.stream.active

    if is_playing:
        bar_w = 6
        bar_h = 16
        gap = 4

        pygame.draw.rect(
            screen,
            icon_col,
            (
                btn_play_rect.centerx - gap - bar_w + 2,
                btn_play_rect.centery - bar_h // 2,
                bar_w,
                bar_h,
            ),
        )
        pygame.draw.rect(
            screen,
            icon_col,
            (
                btn_play_rect.centerx + gap - 2,
                btn_play_rect.centery - bar_h // 2,
                bar_w,
                bar_h,
            ),
        )

    else:
        tri_w = 14
        tri_h = 16
        gap = 4

        pts = [
            (btn_play_rect.centerx - 4, btn_play_rect.centery - tri_h // 2),
            (btn_play_rect.centerx - 4, btn_play_rect.centery + tri_h // 2),
            (btn_play_rect.centerx + 8, btn_play_rect.centery),
        ]
        pygame.draw.polygon(screen, icon_col, pts)

    # draw slots
    for i in range(12):
        slot = slots[i]
        cx = 120 + (i % 4) * 200
        cy = 150 + (i // 4) * 250

        dist = (mx - cx) ** 2 + (my - cy) ** 2
        is_hovered = dist <= CIRCLE_RADIUS**2 and not input_blocked

        if slot.empty:
            color = circle_color_empty
            outline_color = darken_color(color)
        else:
            color = stem_colors.get(slot.type, circle_color_default)

            if master_bpm:
                base_outline = darken_color(color)
                bright_outline = lighten_color(color, factor=1.6)
                dynamic_pulse = pulse_val * slot.volume
                outline_color = lerp_color(base_outline, bright_outline, dynamic_pulse)
            else:
                outline_color = darken_color(color)

        if is_hovered:
            outline_color = palette["hover_outline"]

        pygame.draw.circle(screen, color, (cx, cy), CIRCLE_RADIUS)
        pygame.draw.circle(screen, outline_color, (cx, cy), CIRCLE_RADIUS, 5)

        max_text_width = (CIRCLE_RADIUS * 2) - 10
        name = slot.song_name if slot.song_name else "Empty"
        stype = slot.type if slot.type else ""

        mode_label = ""

        if not slot.empty and slot.type != "drums" and master_scale:
            if slot.scale == master_scale:
                mode_label = f"{slot.scale.capitalize()}"
            else:
                mode_label = f"Relative {slot.scale.capitalize()}"
        elif not slot.empty and slot.type == "drums":
            mode_label = "Neutral"

        draw_dynamic_text(
            screen, name, FONT_MEDIUM, cx, cy - 22, max_text_width, palette["text_main"]
        )
        draw_dynamic_text(
            screen, stype, FONT_MEDIUM, cx, cy, max_text_width, palette["text_dim"]
        )
        if mode_label:
            draw_dynamic_text(
                screen,
                mode_label,
                FONT_MEDIUM,
                cx,
                cy + 22,
                max_text_width,
                palette["text_mode_label"],
            )

        off_x, off_y = cx + 30, cy + 30
        off_hover = False
        if (
            off_x <= mx <= off_x + 32
            and off_y <= my <= off_y + 32
            and not input_blocked
        ):
            off_hover = True

        draw_half_offset(screen, off_x, off_y, slot.half == 1, off_hover)

        ms_x, ms_y = cx - 45, cy + 32

        pygame.draw.rect(
            screen, (30, 30, 30), (ms_x - 2, ms_y - 2, 48, 24), border_radius=4
        )
        draw_mute_solo(screen, ms_x, ms_y, slot.mute, slot.solo, mx, my)

        sx = cx - SLIDER_W // 2
        sy = cy + CIRCLE_RADIUS + 15
        draw_slider(sx, sy, SLIDER_W, SLIDER_H, slot.volume)

    # ---------- hud things ----------

    # the text
    if master_bpm is not None:
        display_k = get_display_key(master_key)
        stats_text = f"BPM: {master_bpm:.1f} | KEY: {display_k} {master_scale}"
    else:
        stats_text = "No Tuning Set"

    # rendering
    stats_surf = FONT_LARGE.render(stats_text, True, text_color)
    stats_outline = FONT_LARGE.render(stats_text, True, palette["text_dark"])

    # pos
    stat_x = 19
    stat_y = SCREEN_H - stats_surf.get_height() - 10

    # draw outline
    offsets = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]

    for dx, dy in offsets:
        screen.blit(stats_outline, (stat_x + dx, stat_y + dy))

    # draw text
    screen.blit(stats_surf, (stat_x, stat_y))

    # -------------------- panels --------------------

    # stem select
    if panel_open:
        pygame.draw.rect(screen, palette["input_bg"], (220, 125, 400, 300))
        pygame.draw.rect(screen, palette["input_border"], (220, 125, 400, 300), 2)

        title = FONT_LARGE.render(f"Slot {selected_slot}", True, text_color)
        screen.blit(title, (300, 135))

        screen.blit(FONT_MEDIUM.render("Song:", True, text_color), (240, 175))
        dropdown_song_select.draw(screen)

        screen.blit(FONT_MEDIUM.render("Stem:", True, text_color), (240, 235))
        dropdown_stem_type_select.draw(screen)

        stem_confirm_rect = pygame.Rect(240, 325, 170, 50)
        stem_cancel_rect = pygame.Rect(430, 325, 170, 50)

        # confirm
        if stem_confirm_rect.collidepoint(mx, my):
            pygame.draw.rect(screen, palette["btn_confirm_hl"], stem_confirm_rect)
        else:
            pygame.draw.rect(screen, palette["btn_confirm"], stem_confirm_rect)
        draw_text_centered("CONFIRM", FONT_LARGE, text_color, stem_confirm_rect)

        # cancel
        if stem_cancel_rect.collidepoint(mx, my):
            pygame.draw.rect(screen, palette["btn_cancel_hl"], stem_cancel_rect)
        else:
            pygame.draw.rect(screen, palette["btn_cancel"], stem_cancel_rect)
        draw_text_centered("CANCEL", FONT_LARGE, text_color, stem_cancel_rect)

        # draw lists last
        dropdown_song_select.draw_list(screen)
        dropdown_stem_type_select.draw_list(screen)

    # manual tune
    if manual_override_open:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill(palette["overlay"])
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, palette["input_bg"], (170, 120, 500, 300))
        pygame.draw.rect(screen, palette["input_border"], (170, 120, 500, 300), 2)

        title = FONT_LARGE.render("Manual Tuning Menu", True, text_color)
        screen.blit(title, (280, 135))

        screen.blit(FONT_MEDIUM.render("BPM:", True, text_color), (310, 205))
        input_manual_bpm.draw(screen)

        screen.blit(FONT_MEDIUM.render("Key:", True, text_color), (220, 265))
        dropdown_manual_key.rect.y = 260
        dropdown_manual_key.draw(screen)

        screen.blit(FONT_MEDIUM.render("Mode:", True, text_color), (440, 265))
        dropdown_manual_scale.rect.y = 260
        dropdown_manual_scale.draw(screen)

        tune_confirm_rect = pygame.Rect(230, 340, 180, 50)
        tune_cancel_rect = pygame.Rect(430, 340, 180, 50)

        # confirm
        if tune_confirm_rect.collidepoint(mx, my):
            pygame.draw.rect(screen, palette["btn_confirm_hl"], tune_confirm_rect)
        else:
            pygame.draw.rect(screen, palette["btn_confirm"], tune_confirm_rect)
        draw_text_centered("CONFIRM", FONT_LARGE, text_color, tune_confirm_rect)

        # cancel
        if tune_cancel_rect.collidepoint(mx, my):
            pygame.draw.rect(screen, palette["btn_cancel_hl"], tune_cancel_rect)
        else:
            pygame.draw.rect(screen, palette["btn_cancel"], tune_cancel_rect)
        draw_text_centered("CANCEL", FONT_LARGE, text_color, tune_cancel_rect)

        dropdown_manual_key.draw_list(screen)
        dropdown_manual_scale.draw_list(screen)

    # options
    if options_open:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill(palette["overlay"])
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, palette["input_bg"], (220, 100, 400, 450))
        pygame.draw.rect(screen, palette["input_border"], (220, 100, 400, 450), 2)

        title = FONT_LARGE.render("Options", True, text_color)
        screen.blit(title, (360, 115))

        screen.blit(
            FONT_MEDIUM.render(
                f"Master Vol: {int(audio_engine.master_volume * 100)}%",
                True,
                text_color,
            ),
            (250, 140),
        )
        vol_rect = pygame.Rect(350, 170, 200, 15)

        draw_slider(
            vol_rect.x,
            vol_rect.y,
            vol_rect.width,
            vol_rect.height,
            audio_engine.master_volume,
        )

        screen.blit(FONT_MEDIUM.render("Theme:", True, text_color), (250, 195))
        dropdown_theme.rect.y = 190
        dropdown_theme.draw(screen)

        screen.blit(FONT_MEDIUM.render("Font:", True, text_color), (250, 250))
        dropdown_font.rect.y = 245
        dropdown_font.draw(screen)

        screen.blit(FONT_MEDIUM.render("Notation:", True, text_color), (250, 305))
        btn_notation_toggle.y = 300

        not_col = (
            palette["input_active"] if use_flat_notation else palette["btn_manual"]
        )
        not_text = "Flats (b)" if use_flat_notation else "Sharps (#)"

        pygame.draw.rect(screen, not_col, btn_notation_toggle)
        pygame.draw.rect(screen, palette["text_dark"], btn_notation_toggle, 2)

        draw_text_centered(
            not_text, FONT_MEDIUM, palette["text_main"], btn_notation_toggle
        )

        opt_close_rect = pygame.Rect(335, 480, 170, 50)
        if opt_close_rect.collidepoint(mx, my):
            pygame.draw.rect(screen, palette["btn_confirm_hl"], opt_close_rect)
        else:
            pygame.draw.rect(screen, palette["btn_confirm"], opt_close_rect)

        draw_text_centered("CLOSE", FONT_LARGE, text_color, opt_close_rect)

        dropdown_theme.draw_list(screen)
        dropdown_font.draw_list(screen)

    # -------------------- save and load overlays --------------------

    if saving_mode:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        box_rect = pygame.Rect((SCREEN_W - 400) // 2, (SCREEN_H - 250) // 2, 400, 250)

        pygame.draw.rect(screen, palette["panel_bg"], box_rect)
        pygame.draw.rect(screen, palette["accent"], box_rect, 2)

        draw_text_centered(
            "Save Project As...",
            FONT_LARGE,
            palette["text_main"],
            pygame.Rect(box_rect.x, box_rect.y + 20, 400, 40),
        )

        save_input.rect.center = box_rect.center
        save_input.draw(screen)

        btn_w, btn_h = 120, 40
        gap = 20

        total_w = (btn_w * 2) + gap
        start_x = box_rect.centerx - (total_w // 2)
        btn_y = box_rect.bottom - 60

        save_confirm_rect = pygame.Rect(start_x, btn_y, btn_w, btn_h)
        save_cancel_rect = pygame.Rect(start_x + btn_w + gap, btn_y, btn_w, btn_h)

        # save button
        if save_confirm_rect.collidepoint(mx, my):
            pygame.draw.rect(screen, palette["btn_confirm_hl"], save_confirm_rect)
        else:
            pygame.draw.rect(screen, palette["btn_confirm"], save_confirm_rect)
        draw_text_centered("SAVE", FONT_MEDIUM, text_color, save_confirm_rect)

        # cancel button
        if save_cancel_rect.collidepoint(mx, my):
            pygame.draw.rect(screen, palette["btn_cancel_hl"], save_cancel_rect)
        else:
            pygame.draw.rect(screen, palette["btn_cancel"], save_cancel_rect)
        draw_text_centered("CANCEL", FONT_MEDIUM, text_color, save_cancel_rect)

    if loading_mode:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        box_rect = pygame.Rect((SCREEN_W - 400) // 2, (SCREEN_H - 300) // 2, 400, 300)
        pygame.draw.rect(screen, palette["panel_bg"], box_rect)
        pygame.draw.rect(screen, palette["btn_load"], box_rect, 2)

        draw_text_centered(
            "Select File to Load",
            FONT_LARGE,
            palette["text_main"],
            pygame.Rect(box_rect.x, box_rect.y + 20, 400, 40),
        )

        if dropdown_load_project:
            dropdown_load_project.draw(screen)

        btn_w, btn_h = 120, 40
        gap = 20

        total_w = (btn_w * 2) + gap
        start_x = box_rect.centerx - (total_w // 2)
        btn_y = box_rect.bottom - 60

        load_confirm_rect = pygame.Rect(start_x, btn_y, btn_w, btn_h)
        load_cancel_rect = pygame.Rect(start_x + btn_w + gap, btn_y, btn_w, btn_h)

        # load buttom
        if load_confirm_rect.collidepoint(mx, my):
            pygame.draw.rect(screen, palette["btn_confirm_hl"], load_confirm_rect)
        else:
            pygame.draw.rect(screen, palette["btn_confirm"], load_confirm_rect)
        draw_text_centered("LOAD", FONT_MEDIUM, text_color, load_confirm_rect)

        # cancel button
        if load_cancel_rect.collidepoint(mx, my):
            pygame.draw.rect(screen, palette["btn_cancel_hl"], load_cancel_rect)
        else:
            pygame.draw.rect(screen, palette["btn_cancel"], load_cancel_rect)
        draw_text_centered("CANCEL", FONT_MEDIUM, text_color, load_cancel_rect)

        if dropdown_load_project:
            dropdown_load_project.draw_list(screen)

    # -------------------- input handler GOD THIS SUCKS --------------------

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_config()
            running = False

        mx, my = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEMOTION:
            if dragging_master_vol:
                rel_x = mx - 350
                audio_engine.master_volume = max(0.0, min(1.0, rel_x / 200))

        if event.type == pygame.MOUSEBUTTONUP:
            if dragging_master_vol:
                dragging_master_vol = False
                save_config()
            dragging_slider = None

        if saving_mode:
            if save_input.handle_event(event):
                fname = save_input.text
                if len(fname) > 0:
                    if not fname.endswith(".json"):
                        fname += ".json"
                    save_project(fname)
                    saving_mode = False
                    pygame.key.stop_text_input()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                box_rect = pygame.Rect(
                    (SCREEN_W - 400) // 2, (SCREEN_H - 250) // 2, 400, 250
                )
                btn_w, btn_h = 120, 40
                gap = 20
                total_w = (btn_w * 2) + gap
                start_x = box_rect.centerx - (total_w // 2)
                btn_y = box_rect.bottom - 60

                save_confirm_rect = pygame.Rect(start_x, btn_y, btn_w, btn_h)
                save_cancel_rect = pygame.Rect(
                    start_x + btn_w + gap, btn_y, btn_w, btn_h
                )

                if save_input.rect.collidepoint(mx, my):
                    continue

                if save_confirm_rect.collidepoint(mx, my):
                    fname = save_input.text
                    if len(fname) > 0:
                        if not fname.endswith(".json"):
                            fname += ".json"
                        save_project(fname)
                        saving_mode = False
                        pygame.key.stop_text_input()

                elif save_cancel_rect.collidepoint(mx, my):
                    saving_mode = False
                    pygame.key.stop_text_input()
            continue

        if loading_mode:
            if dropdown_load_project:
                if dropdown_load_project.handle_event(event):
                    continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                box_rect = pygame.Rect(
                    (SCREEN_W - 400) // 2, (SCREEN_H - 300) // 2, 400, 300
                )
                btn_w, btn_h = 120, 40
                gap = 20
                total_w = (btn_w * 2) + gap
                start_x = box_rect.centerx - (total_w // 2)
                btn_y = box_rect.bottom - 60

                load_confirm_rect = pygame.Rect(start_x, btn_y, btn_w, btn_h)
                load_cancel_rect = pygame.Rect(
                    start_x + btn_w + gap, btn_y, btn_w, btn_h
                )

                if load_confirm_rect.collidepoint(mx, my):
                    sel = dropdown_load_project.get_selected()
                    if sel:
                        load_project(sel)

                        if master_bpm:
                            input_manual_bpm.text = str(int(master_bpm))
                            input_manual_bpm.txt_surface = input_manual_bpm.font.render(
                                input_manual_bpm.text, True, palette["text_main"]
                            )
                        if master_key and master_key in dropdown_manual_key.options:
                            dropdown_manual_key.index = (
                                dropdown_manual_key.options.index(master_key)
                            )
                        if (
                            master_scale
                            and master_scale in dropdown_manual_scale.options
                        ):
                            dropdown_manual_scale.index = (
                                dropdown_manual_scale.options.index(master_scale)
                            )
                        loading_mode = False

                elif load_cancel_rect.collidepoint(mx, my):
                    loading_mode = False

            continue

        if options_open:
            if dropdown_theme.handle_event(event):
                sel = dropdown_theme.get_selected()
                if sel:
                    load_theme(sel)
                    save_config()
                continue

            if dropdown_font.handle_event(event):
                sel = dropdown_font.get_selected()
                if sel:
                    update_fonts(sel)
                    input_manual_bpm.font = FONT_MEDIUM
                    input_manual_bpm.txt_surface = input_manual_bpm.font.render(
                        input_manual_bpm.text, True, palette["text_main"]
                    )
                    dropdown_theme.font = FONT_SMALL
                    dropdown_font.font = FONT_SMALL
                    dropdown_song_select.font = FONT_SMALL
                    dropdown_stem_type_select.font = FONT_SMALL
                    dropdown_manual_key.font = FONT_SMALL
                    dropdown_manual_scale.font = FONT_SMALL
                    save_config()
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed()[0]:
                    vol_rect = pygame.Rect(350, 170, 200, 15)
                    if vol_rect.collidepoint(mx, my):
                        dragging_master_vol = True
                        rel_x = mx - 350
                        audio_engine.master_volume = max(0.0, min(1.0, rel_x / 200))

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_notation_toggle.collidepoint(mx, my):
                    use_flat_notation = not use_flat_notation
                    save_config()

                    new_keys = KEYS_FLAT if use_flat_notation else KEYS_SHARP
                    dropdown_manual_key.update_options(new_keys)

                opt_close_rect = pygame.Rect(335, 480, 170, 50)
                if opt_close_rect.collidepoint(mx, my):
                    options_open = False

            continue

        # manual tuning inputs
        if manual_override_open:
            if dropdown_manual_key.handle_event(
                event
            ) or dropdown_manual_scale.handle_event(event):
                continue

            input_manual_bpm.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # hitboxes
                btn_manual_confirm = pygame.Rect(230, 340, 180, 50)
                btn_manual_cancel = pygame.Rect(430, 340, 180, 50)

                # confirm click
                if btn_manual_confirm.collidepoint(mx, my):
                    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                    overlay.fill(palette["overlay"])
                    screen.blit(overlay, (0, 0))

                    wait_w, wait_h = 300, 100
                    wait_rect = pygame.Rect(
                        (SCREEN_W - wait_w) // 2,
                        (SCREEN_H - wait_h) // 2,
                        wait_w,
                        wait_h,
                    )

                    wait_text = FONT_LARGE.render(
                        "Processing...", True, palette["text_main"]
                    )
                    sub_text = FONT_MEDIUM.render(
                        "Please wait...", True, palette["text_dim"]
                    )

                    txt_rect1 = wait_text.get_rect(
                        centerx=wait_rect.centerx, centery=wait_rect.centery - 15
                    )
                    txt_rect2 = sub_text.get_rect(
                        centerx=wait_rect.centerx, centery=wait_rect.centery + 15
                    )

                    pygame.draw.rect(screen, palette["panel_bg"], wait_rect)
                    pygame.draw.rect(screen, palette["slider_fill"], wait_rect, 3)
                    screen.blit(wait_text, txt_rect1)
                    screen.blit(sub_text, txt_rect2)
                    pygame.display.flip()

                    try:
                        master_key = dropdown_manual_key.get_selected()
                        master_scale = dropdown_manual_scale.get_selected()

                        new_bpm = None
                        if input_manual_bpm.text and float(input_manual_bpm.text) > 0:
                            new_bpm = float(input_manual_bpm.text)
                            master_bpm = new_bpm

                        audio_engine.stop()

                        slots_to_reload = []
                        for i, slot in enumerate(slots):
                            if not slot.empty:
                                slots_to_reload.append(
                                    {"id": i, "name": slot.song_name, "type": slot.type}
                                )
                                slot.stem = None

                        audio_engine.max_length = 0

                        for data in slots_to_reload:
                            print(f"Reloading slot {data['id']}...")

                            pygame.draw.rect(screen, palette["panel_bg"], wait_rect)
                            pygame.draw.rect(
                                screen, palette["slider_fill"], wait_rect, 3
                            )

                            screen.blit(wait_text, txt_rect1)
                            screen.blit(sub_text, txt_rect2)

                            pygame.display.flip()

                            if use_relative_mode:
                                expected_scale = (
                                    "minor" if master_scale == "major" else "major"
                                )
                            else:
                                expected_scale = master_scale

                            if data["type"] == "drums":
                                expected_scale = None

                            song_path = None
                            for folder in SONG_FOLDERS:
                                potential_path = os.path.join(folder, data["name"])
                                if os.path.exists(potential_path):
                                    song_path = potential_path
                                    break

                            if song_path:
                                add_stem_to_slot(data["id"], song_path, data["type"])
                            else:
                                print(
                                    f"ERROR: Could not locate song '{data['name']}' in any known folder."
                                )

                        audio_engine.start()

                    except Exception as e:
                        print(f"Manual tuning error: {e}")
                        if (
                            audio_engine.stream is None
                            or not audio_engine.stream.active
                        ):
                            audio_engine.start()

                    manual_override_open = False
                    pygame.key.stop_text_input()

                if btn_manual_cancel.collidepoint(mx, my):
                    manual_override_open = False
                    pygame.key.stop_text_input()

                # cancel click
                if btn_manual_cancel.collidepoint(mx, my):
                    manual_override_open = False
                    pygame.key.stop_text_input()
                continue

        # stem select inputs
        if panel_open:
            if dropdown_song_select.handle_event(
                event
            ) or dropdown_stem_type_select.handle_event(event):
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # hitboxes
                btn_stem_confirm = pygame.Rect(240, 325, 170, 50)
                btn_stem_cancel = pygame.Rect(430, 325, 170, 50)

                # confirm click
                if btn_stem_confirm.collidepoint(mx, my):
                    song_val = dropdown_song_select.get_selected()
                    stem_val = dropdown_stem_type_select.get_selected()
                    if song_val and stem_val:
                        add_stem_to_slot(selected_slot, song_val, stem_val)
                        panel_open = False

                # cancel click
                if btn_stem_cancel.collidepoint(mx, my):
                    panel_open = False

            continue

        # main screen inputs
        if event.type == pygame.MOUSEBUTTONDOWN:

            # expor
            if btn_exp_rect.collidepoint(mx, my) and event.button == 1:
                overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                overlay.fill(palette["overlay"])
                screen.blit(overlay, (0, 0))

                wait_w, wait_h = 300, 100
                wait_rect = pygame.Rect(
                    (SCREEN_W - wait_w) // 2, (SCREEN_H - wait_h) // 2, wait_w, wait_h
                )

                pygame.draw.rect(screen, palette["popup_bg"], wait_rect)
                pygame.draw.rect(screen, palette["popup_border"], wait_rect, 3)
                draw_text_centered(
                    "Rendering WAV...", FONT_LARGE, palette["text_main"], wait_rect
                )

                pygame.display.flip()

                now = datetime.datetime.now()
                timestamp = now.isoformat()[:19].replace(":", "-")
                filename = f"jam_{timestamp}.wav"

                export_mix_to_wav(filename)
                continue

            # pause play restart
            if btn_restart_rect.collidepoint(mx, my) and event.button == 1:
                audio_engine.restart()

            if btn_play_rect.collidepoint(mx, my) and event.button == 1:
                toggle_master_playback()

            # top left manual button
            if 20 <= mx <= 220 and 20 <= my <= 60 and event.button == 1:
                manual_override_open = True

                if master_bpm is not None:
                    bpm_str = str(master_bpm)
                    if bpm_str.endswith(".0"):
                        bpm_str = bpm_str[:-2]
                    input_manual_bpm.text = bpm_str
                else:
                    input_manual_bpm.text = ""

                input_manual_bpm.txt_surface = input_manual_bpm.font.render(
                    input_manual_bpm.text, True, palette["text_main"]
                )

                if master_key and master_key in dropdown_manual_key.options:
                    dropdown_manual_key.index = dropdown_manual_key.options.index(
                        master_key
                    )

                if master_scale and master_scale in dropdown_manual_scale.options:
                    dropdown_manual_scale.index = dropdown_manual_scale.options.index(
                        master_scale
                    )

            if btn_opt_rect.collidepoint(mx, my):
                options_open = True
                available_themes = [
                    f.replace(".json", "")
                    for f in os.listdir("themes")
                    if f.endswith(".json")
                ]
                dropdown_theme.update_options(available_themes)
                continue

            if btn_save_rect.collidepoint(mx, my) and event.button == 1:
                saving_mode = True
                pygame.key.start_text_input()

            if btn_load_rect.collidepoint(mx, my) and event.button == 1:
                loading_mode = True
                files = [f for f in os.listdir("projects") if f.endswith(".json")]
                dropdown_load_project = DropdownMenu(
                    (SCREEN_W - 300) // 2,
                    (SCREEN_H - 300) // 2 + 80,
                    300,
                    35,
                    files,
                    max_display_items=12,
                )
                continue

            # right click clear slot
            if event.button == 3:
                for i in range(12):
                    cx = 120 + (i % 4) * 200
                    cy = 150 + (i // 4) * 250
                    if (mx - cx) ** 2 + (my - cy) ** 2 < CIRCLE_RADIUS**2:
                        clear_slot(i)
                        break

            # left click slider or open panel
            if event.button == 1:
                for slot_index in range(12):

                    slot_button_clicked = False  # this does shit

                    cx = 120 + (slot_index % 4) * 200
                    cy = 150 + (slot_index // 4) * 250

                    off_x, off_y = cx + 30, cy + 30
                    if off_x <= mx <= off_x + 32 and off_y <= my <= off_y + 32:
                        shift_slot(slot_index)
                        slot_button_clicked = True

                    ms_x, ms_y = cx - 45, cy + 32

                    if ms_x <= mx <= ms_x + 20 and ms_y <= my <= ms_y + 20:
                        slots[slot_index].mute = not slots[slot_index].mute
                        slot_button_clicked = True

                    if ms_x + 24 <= mx <= ms_x + 44 and ms_y <= my <= ms_y + 20:
                        slots[slot_index].solo = not slots[slot_index].solo
                        slot_button_clicked = True

                    if not slot_button_clicked:
                        sx = cx - SLIDER_W // 2
                        sy = cy + CIRCLE_RADIUS + 15

                        if sx <= mx <= sx + SLIDER_W and sy <= my <= sy + SLIDER_H:
                            dragging_slider = slot_index
                            rel = mx - sx
                            slots[slot_index].target_volume = max(
                                0.0, min(1.0, rel / SLIDER_W)
                            )
                            break

                        if dragging_slider is None:
                            if (mx - cx) ** 2 + (my - cy) ** 2 < CIRCLE_RADIUS**2:
                                panel_open = True
                                selected_slot = slot_index
                                dropdown_song_select.update_options(get_song_list())
                                break

        if event.type == pygame.MOUSEBUTTONUP:
            if dragging_master_vol:
                dragging_master_vol = False
                save_config()
            dragging_slider = None

        if event.type == pygame.MOUSEMOTION and dragging_slider is not None:
            i = dragging_slider
            cx = 120 + (i % 4) * 200
            sx = cx - SLIDER_W // 2
            rel = mx - sx
            slots[i].target_volume = max(0.0, min(1.0, rel / SLIDER_W))

        if event.type == pygame.MOUSEWHEEL:
            if options_open:
                if dropdown_theme.handle_event(event) or dropdown_font.handle_event(
                    event
                ):
                    continue

            if panel_open and (
                dropdown_song_select.handle_event(event)
                or dropdown_stem_type_select.handle_event(event)
            ):
                continue

            if manual_override_open and (
                dropdown_manual_key.handle_event(event)
                or dropdown_manual_scale.handle_event(event)
            ):
                continue

            if (
                loading_mode
                and dropdown_load_project
                and dropdown_load_project.handle_event(event)
            ):
                continue

            if not input_blocked:
                mx, my = pygame.mouse.get_pos()

                for i in range(12):
                    q, r = divmod(i, 4)
                    cx = 120 + r * 200
                    cy = 150 + q * 250
                    sx = cx - SLIDER_W // 2
                    sy = cy + CIRCLE_RADIUS + 15

                    slider_rect = pygame.Rect(
                        sx - 10, sy - 10, SLIDER_W + 20, SLIDER_H + 20
                    )

                    if slider_rect.collidepoint(mx, my):
                        scroll_amount = event.y * 0.05

                        new_vol = slots[i].target_volume + scroll_amount
                        slots[i].target_volume = max(0.0, min(1.0, new_vol))
                        break

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
audio_engine.stop()
