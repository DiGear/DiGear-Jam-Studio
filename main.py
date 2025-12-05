import os
import json
import math
import datetime
import numpy as np
import soundfile as sf
import pyrubberband as rb
import sounddevice as sd
import pygame

# -------------------- constants -------------------- 

KEY_TO_INT = {
    "C": 0, 
    "C#": 1, "Db": 1, 
    "D": 2, 
    "D#": 3, "Eb": 3,
    "E": 4, 
    "F": 5, 
    "F#": 6, "Gb": 6, 
    "G": 7, 
    "G#": 8, "Ab": 8, 
    "A": 9, 
    "A#": 10, "Bb": 10, 
    "B": 11
}

KEYS_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
KEYS_FLAT =  ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

USE_FLATS = False 

sample_rate = 44100
BUFFER_SIZE = 2048
CHANNELS = 2
SONG_FOLDERS = ["Songs", "Stock Songs"]

# ----------- squif game -----------

pygame.init()

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

# ---------- graphik ----------

PALETTE = { # we can condense the shit out of thiso now cuz we have the jsons
    "bg_dark": (10, 10, 14), "bg_light": (25, 25, 35), "panel_bg": (20, 20, 25),
    "overlay": (0, 0, 0, 180), "popup_bg": (40, 40, 40), "popup_border": (0, 200, 80),
    "hover_outline": (128, 128, 128), "text_main": (240, 240, 255), "text_dim": (200, 200, 200),
    "text_dark": (0, 0, 0), "text_mode_label": (200, 255, 200),
    "slot_default": (80, 130, 255), "slot_empty": (60, 60, 60), "slot_vocals": (255, 230, 100),
    "slot_bass": (100, 255, 150), "slot_drums": (100, 230, 255), "slot_lead": (255, 120, 200),
    "accent": (80, 130, 255), "input_bg": (30, 30, 30), "input_border": (60, 60, 60),
    "input_active": (100, 100, 255), "scrollbar": (100, 100, 100),
    "slider_track": (120, 120, 120), "slider_fill": (0, 200, 80), "slider_knob": (255, 255, 255),
    "btn_manual": (0, 170, 60), "btn_save": (230, 120, 40), "btn_load": (60, 120, 210),
    "btn_ctrl": (80, 80, 80), "btn_icon": (198, 198, 198), "btn_confirm": (0, 160, 80),
    "btn_confirm_hl": (51, 179, 115), "btn_cancel": (160, 60, 60), "btn_cancel_hl": (179, 99, 99),
}

CIRCLE_COLOR_EMPTY = None
CIRCLE_COLOR_DEFAULT = None
STEM_COLORS = {}
TEXT_COLOR = None
SLIDER_COLOR = None
SLIDER_FILL = None
SLIDER_TIP = None

TYPER = ["Arial", 20, 22, 28] 
SMALLERFONT = None
FONT = None
BIGFONT = None

current_theme_name = "default"

def save_config():
    config = {
        "theme": current_theme_name,
        "font": TYPER[0], 
        "use_flats": USE_FLATS
    }
    try:
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"fuck: {e}")

def update_fonts(font_name=None):
    global SMALLERFONT, FONT, BIGFONT, TYPER
    if font_name:
        TYPER[0] = font_name
    
    try:
        SMALLERFONT = pygame.font.SysFont(TYPER[0], TYPER[1])
        FONT = pygame.font.SysFont(TYPER[0], TYPER[2])
        BIGFONT = pygame.font.SysFont(TYPER[0], TYPER[3])
    except:
        SMALLERFONT = pygame.font.SysFont("Arial", TYPER[1])
        FONT = pygame.font.SysFont("Arial", TYPER[2])
        BIGFONT = pygame.font.SysFont("Arial", TYPER[3])

def update_graphics_constants():
    global CIRCLE_COLOR_EMPTY, CIRCLE_COLOR_DEFAULT, STEM_COLORS, TEXT_COLOR
    global SLIDER_COLOR, SLIDER_FILL, SLIDER_TIP
    
    CIRCLE_COLOR_EMPTY = PALETTE["slot_empty"]
    CIRCLE_COLOR_DEFAULT = PALETTE["slot_default"]

    STEM_COLORS = {
        "vocals": PALETTE["slot_vocals"],
        "bass": PALETTE["slot_bass"],
        "drums": PALETTE["slot_drums"],
        "lead": PALETTE["slot_lead"]
    }

    TEXT_COLOR = PALETTE["text_main"]
    SLIDER_COLOR = PALETTE["slider_track"]
    SLIDER_FILL = PALETTE["slider_fill"]
    SLIDER_TIP = PALETTE["slider_knob"]

def load_theme(theme_name):
    global current_theme_name
    path = os.path.join("themes", theme_name + ".json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                for k, v in data.items():
                    if k in PALETTE:
                        PALETTE[k] = tuple(v)
            update_graphics_constants()
            current_theme_name = theme_name
            print(f"loaded theme: {theme_name}")
        except Exception as e:
            print(f"failed to load theme: {e}")
    else:
        print(f"theme not found: {path}")
    update_graphics_constants()


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
            print("Config loaded.")
    except Exception as e:
        print(f"Error reading config: {e}")

USE_FLATS = init_flats
update_fonts(init_font)
load_theme(init_theme)

SLIDER_W = 120
SLIDER_H = 10
CIRCLE_RADIUS = 60

try:
    btn_offset_off=pygame.image.load('gui/btn_offset_off.png').convert_alpha()
    btn_offset_on=pygame.image.load('gui/btn_offset_on.png').convert_alpha()
    btn_offset_hover=pygame.image.load('gui/btn_offset_hover.png').convert_alpha()
except:
    # this shouldn't happen
    btn_offset_off = pygame.Surface((32,32)); btn_offset_off.fill((100,100,100))
    btn_offset_on = pygame.Surface((32,32)); btn_offset_on.fill((200,200,100))
    btn_offset_hover = pygame.Surface((32,32)); btn_offset_hover.fill((150,150,150))

# -------------------- ochame kinous -------------------- 

def draw_text_centered(text, font, color, target_rect):
    surf = font.render(text, True, color)
    text_rect = surf.get_rect(center=target_rect.center)
    screen.blit(surf, text_rect)

def get_display_key(key_str):
    if not key_str: return "???"
    idx = KEY_TO_INT.get(key_str, 0) 
    return KEYS_FLAT[idx] if USE_FLATS else KEYS_SHARP[idx]

def key_shift_semitones(target_key, source_key):
    # calc semitone diff
    raw = KEY_TO_INT[target_key] - KEY_TO_INT[source_key]
    if raw > 6:
        raw -= 12
    elif raw < -6:
        raw += 12
    return raw

def bpm_with_multipliers(original_bpm, master_bpm):
    # find best bpm match
    candidates = [
            original_bpm * 0.0625,
            original_bpm * 0.125,
            original_bpm * 0.25,
            original_bpm * 0.5,    # half time
            original_bpm,          # og
            original_bpm * 2,      # double time
            original_bpm * 4,
            original_bpm * 8,
            original_bpm * 16
        ]
    return min(candidates, key=lambda b: abs(b - master_bpm))

def darken_color(color, factor=0.6): # one less hard-coded thing
    r, g, b = color
    return (int(r * factor), int(g * factor), int(b * factor))

def lighten_color(color, factor=1.5):
    r, g, b = color
    return (min(255, int(r * factor)), min(255, int(g * factor)), min(255, int(b * factor)))

def lerp_color(c1, c2, t):
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t)
    )

def load_stem_direct(path):
    audio, sr = sf.read(path, dtype='float32')
    if audio.ndim == 1:
        audio = np.stack([audio, audio], axis=1)
    if sr != sample_rate:
        print(f"Warning: samplerate mismatch in {path}")
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak
    return audio

def draw_slider(x, y, w, h, value):
    track_outline_col = darken_color(SLIDER_COLOR, factor=0.4)
    knob_outline_col = darken_color(SLIDER_TIP, factor=0.4)
    pygame.draw.rect(screen, SLIDER_COLOR, (x, y, w, h))
    filled = int(w * value)
    if filled > 0:
        pygame.draw.rect(screen, SLIDER_FILL, (x, y, filled, h))
    pygame.draw.rect(screen, track_outline_col, (x, y, w, h), 2)
    knob_x = x + filled
    knob_y = y + h // 2
    knob_radius = h // 2 + 2
    pygame.draw.circle(screen, SLIDER_TIP, (knob_x, knob_y), knob_radius)
    pygame.draw.circle(screen, knob_outline_col, (knob_x, knob_y), knob_radius, 2)
    
def draw_offset_button(x, y, state):
    mx, my = pygame.mouse.get_pos()

    if state == False:
        screen.blit(btn_offset_off, (x,y))
    else:
        screen.blit(btn_offset_on, (x,y))
        
    #hover highlight
    if x <= mx < x+32 and y <= my < y+32 and not input_blocked:
        screen.blit(btn_offset_hover, (x,y))

def draw_dynamic_text(surface, text, font, center_x, center_y, max_width, color):
    # draws text with outline and scales if too big
    if not text:
        return

    text_surf = font.render(text, True, color)
    outline_surf = font.render(text, True, PALETTE["text_dark"])

    width, height = text_surf.get_size()
    if width > max_width:
        scale_factor = max_width / width
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        text_surf = pygame.transform.smoothscale(text_surf, (new_width, new_height))
        outline_surf = pygame.transform.smoothscale(outline_surf, (new_width, new_height))

    rect = text_surf.get_rect(center=(center_x, center_y))

    # draw outline
    offsets = [
        (-1, -1), (0, -1), (1, -1),
        (-1,  0),          (1,  0),
        (-1,  1), (0,  1), (1,  1)
    ]
    for dx, dy in offsets:
        surface.blit(outline_surf, (rect.x + dx, rect.y + dy))
    surface.blit(text_surf, rect)

# -------------------- classes -------------------- 

class Slot:
    def __init__(self):
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

class AudioEngine:
    def __init__(self, slots, samplerate=44100):
        self.slots = slots
        self.sr = samplerate
        self.position = 0
        self.max_length = 0
        self.stream = None

    def update_max_length(self):
        lengths = [len(s.stem) for s in self.slots if not s.empty and s.stem is not None]
        self.max_length = max(lengths) if lengths else 0

    def audio_callback(self, outdata, frames, time, status):
        if status:
            print("audio callback status:", status)

        self.max_length = max((len(s.stem) for s in self.slots if not s.empty and s.stem is not None), default=0)
        mix = np.zeros((frames, CHANNELS), dtype=np.float32)

        if self.max_length == 0:
            outdata[:] = mix
            return

        # loop it
        if self.position >= self.max_length:
            self.position %= self.max_length

        pos = self.position

        for slot in self.slots:
            
            if slot.empty or slot.stem is None:
                continue

            audio = slot.stem
            length = len(audio)

            if length == 0:
                continue

            current_offset = (length // 2) if slot.half == 1 else 0
            offset_pos = (pos + current_offset) % length

            end = offset_pos + frames
            if end <= length:
                chunk = audio[offset_pos:end]
            else:
                wrap = end - length
                part1 = audio[offset_pos:length]
                part2 = audio[0:wrap]
                chunk = np.vstack((part1, part2))

            # mono to stereo
            if chunk.ndim == 1:
                chunk = np.stack([chunk, chunk], axis=1)

            # fix buffer size if needed
            if chunk.shape[0] != frames:
                if chunk.shape[0] > frames:
                    chunk = chunk[:frames]
                else:
                    pad = frames - chunk.shape[0]
                    chunk = np.vstack((chunk, np.zeros((pad, CHANNELS), dtype=np.float32)))

            mix += chunk * slot.volume

        mix = np.clip(mix, -1.0, 1.0)
        outdata[:] = mix
        self.position += frames
        if self.position >= self.max_length:
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
            dtype='float32',
            callback=self.audio_callback
        )
        self.stream.start()
        print("audio engine started")

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            print("audio engine stopped")

# -------------------- fuckin pygame STUPID SHIT FUCK I HATE PYGAME AAAAA -------------------- 

class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = PALETTE["input_border"]
        self.color_active = PALETTE["input_active"]
        self.color = self.color_inactive
        self.text = text
        self.font = FONT
        self.txt_surface = self.font.render(text, True, PALETTE["text_main"])
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive
            return self.active

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    pass
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    if event.unicode.isnumeric() or (event.unicode == '.' and '.' not in self.text):
                        self.text += event.unicode
                self.txt_surface = self.font.render(self.text, True, PALETTE["text_main"])
        return False

    def draw(self, screen):
        pygame.draw.rect(screen, PALETTE["input_bg"], self.rect)
        screen.blit(self.txt_surface, (self.rect.x + 10, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

class Dropdown:
    def __init__(self, x, y, w, h, options, default_index=0, max_display_items=5):
        self.rect = pygame.Rect(x, y, w, h)
        self.options = options
        self.index = default_index
        self.is_open = False
        self.font = SMALLERFONT
        self.active_option_color = PALETTE["input_border"]
        self.hover_color = PALETTE["accent"]
        self.bg_color = PALETTE["input_bg"]
        self.text_color = PALETTE["text_main"]
        self.border_color = PALETTE["scrollbar"]
        self.scroll_y = 0
        self.max_display_items = max_display_items
        self.item_height = h
        self.scrollbar_width = 15

    def get_selected(self):
        if not self.options: return None
        if 0 <= self.index < len(self.options):
            return self.options[self.index]
        return None

    def update_options(self, new_options):
        self.options = new_options
        if self.index >= len(self.options):
            self.index = 0
        self.scroll_y = 0 

    def draw(self, screen):
        self.bg_color = PALETTE["input_bg"]
        self.text_color = PALETTE["text_main"]
        self.border_color = PALETTE["scrollbar"]
        
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
            
            current_bg = PALETTE["input_bg"]
            current_border = PALETTE["scrollbar"]
            current_text = PALETTE["text_main"]
            current_hover = PALETTE["accent"]
            current_active = PALETTE["input_border"]

            num_items = len(self.options)
            total_height = num_items * self.item_height
            display_count = min(num_items, self.max_display_items)
            display_height = display_count * self.item_height
            
            list_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height, self.rect.width, display_height)
            pygame.draw.rect(screen, current_bg, list_rect)
            
            old_clip = screen.get_clip()
            screen.set_clip(list_rect)
            
            start_y = list_rect.y - self.scroll_y
            
            for i, opt in enumerate(self.options):
                opt_y = start_y + (i * self.item_height)
 
                if opt_y + self.item_height < list_rect.y or opt_y > list_rect.bottom:
                    continue
                    
                opt_rect = pygame.Rect(self.rect.x, opt_y, self.rect.width - self.scrollbar_width, self.item_height)
                
                is_hovered = opt_rect.collidepoint(mx, my) and list_rect.collidepoint(mx, my)
                
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
                sb_bg_rect = pygame.Rect(self.rect.right - self.scrollbar_width, list_rect.y, self.scrollbar_width, display_height)
                pygame.draw.rect(screen, current_bg, sb_bg_rect)
                
                ratio = display_height / total_height
                thumb_h = max(20, display_height * ratio)
                
                max_scroll = total_height - display_height
                scroll_ratio = self.scroll_y / max_scroll
                thumb_y = list_rect.y + scroll_ratio * (display_height - thumb_h)
                
                sb_thumb_rect = pygame.Rect(self.rect.right - self.scrollbar_width + 2, thumb_y, self.scrollbar_width - 4, thumb_h)
                pygame.draw.rect(screen, PALETTE["scrollbar"], sb_thumb_rect, border_radius=4)

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            
            if self.is_open and self.options:
                display_height = min(len(self.options), self.max_display_items) * self.item_height
                list_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height, self.rect.width, display_height)
                
                if list_rect.collidepoint(mx, my):
                    total_height = len(self.options) * self.item_height
                    max_scroll = max(0, total_height - display_height)
                    
                    scroll_speed = 20
                    self.scroll_y -= event.y * scroll_speed
                    
                    if self.scroll_y < 0: self.scroll_y = 0
                    if self.scroll_y > max_scroll: self.scroll_y = max_scroll
                    return True

            elif not self.is_open and self.rect.collidepoint(mx, my):
                if self.options:
                    if event.y > 0:
                        self.index -=1
                    elif event.y < 0:
                        self.index += 1
                    
                    self.index = max(0, min(self.index, len(self.options) -1))
                    return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            
            if self.is_open and self.options:
                display_height = min(len(self.options), self.max_display_items) * self.item_height
                list_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height, self.rect.width, display_height)
                
                if list_rect.collidepoint(mx, my):
                    if mx > self.rect.right - self.scrollbar_width:
                        return True
                    
                    relative_y = my - list_rect.y + self.scroll_y
                    idx = int(relative_y // self.item_height)
                    
                    if 0 <= idx < len(self.options):
                        self.index = idx
                        self.is_open = False
                        return True
                
                if not self.rect.collidepoint(mx, my) and not list_rect.collidepoint(mx, my):
                    self.is_open = False
            

            if self.rect.collidepoint(mx, my):
                self.is_open = not self.is_open
                return True
                
        return False

# -------------------- global state -------------------- 

# init slots
slots = [Slot() for _ in range(12)]
master_bpm = None
master_key = None
master_scale = None
manual_override_open = False

dragging_slider = None
panel_open = False
selected_slot = None

# relative/parallel mode shit
use_relative_mode = False

audio_engine = AudioEngine(slots, sample_rate)
audio_engine.start()

options_open = False
available_themes = [f.replace(".json","") for f in os.listdir("themes") if f.endswith(".json")]
available_fonts = pygame.font.get_fonts()
available_fonts.sort()
if "arial" not in available_fonts and len(available_fonts) > 0:
    available_fonts.insert(0, "arial")

def get_idx(lst, item):
    try:
        return lst.index(item)
    except ValueError:
        return 0

# option s
opt_theme_dd = Dropdown(350, 200, 200, 35, available_themes, default_index=get_idx(available_themes, current_theme_name), max_display_items=15)
opt_font_dd = Dropdown(350, 270, 200, 35, available_fonts, default_index=get_idx(available_fonts, TYPER[0]), max_display_items=14)

opt_notation_btn = pygame.Rect(350, 340, 200, 35)

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

        songs = [os.path.join(folder, x) for x in os.listdir(folder) if os.path.isdir(os.path.join(folder, x))]
        all_songs.extend(songs)
        
    return all_songs

def add_stem_to_slot(slot_id, song_folder, stem_type):
    global master_bpm, master_key, master_scale

    meta_path = os.path.join(song_folder, "meta.json")
    with open(meta_path, "r") as f:
        meta = json.load(f)

    song_key = meta["key"]
    song_bpm = meta["bpm"]

    print(f"\nloading stem '{stem_type}' from {song_folder}")

    # set master if first track
    if master_bpm is None:
        master_bpm = song_bpm
        master_key = song_key
        master_scale = meta.get("scale", "major")
        print(f"Master set to {master_key} {master_scale}")
    
    file_to_load = ""
    loaded_scale = ""
    
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
            fallback_path = os.path.join(song_folder, f"{stem_type}_{fallback_scale}.ogg")
            
            if os.path.exists(fallback_path):
                file_to_load = f"{stem_type}_{fallback_scale}.ogg"
                loaded_scale = fallback_scale
                print(f"no matching mode file found: falling back to the relative mode of {loaded_scale}")
            else:
                print(f"ERROR: No stem files found for {stem_type}")
                return

    # load Audio
    full_path = os.path.join(song_folder, file_to_load)
    stem_audio = load_stem_direct(full_path)

    # time Stretch
    adjusted_bpm = bpm_with_multipliers(song_bpm, master_bpm)
    stretch_ratio = master_bpm / adjusted_bpm
    if stretch_ratio != 1.0:
        print(f"time stretch: {song_bpm} -> {adjusted_bpm} -> {master_bpm}")
        stem_audio = rb.time_stretch(stem_audio, sample_rate, stretch_ratio)

    # pitch shift (now with fallback shit)
    if stem_type != "drums":
        semis = key_shift_semitones(master_key, song_key)
        if loaded_scale == master_scale:
            pass
            
        elif loaded_scale != "neutral":
            print("relative mode third offset haha funny")
            if loaded_scale == "minor" and master_scale == "major":
                semis -= 3
            elif loaded_scale == "major" and master_scale == "minor":
                semis += 3

        if semis != 0:
            print(f"pitch shift {semis:+d} semitones")
            stem_audio = rb.pitch_shift(stem_audio, sample_rate, semis)

    # sync length
    if audio_engine.max_length == 0:
        audio_engine.max_length = len(stem_audio)
    
    master_length = audio_engine.max_length
    cur_len = len(stem_audio)
    
    # micro stretch to align samples exactly
    if cur_len != master_length:
        ratio = master_length / cur_len
        if 0.5 < ratio < 2.0: 
            stem_audio = rb.time_stretch(stem_audio, sample_rate, 1 / ratio)
            if len(stem_audio) > master_length:
                stem_audio = stem_audio[:master_length]
            elif len(stem_audio) < master_length:
                pad = master_length - len(stem_audio)
                stem_audio = np.vstack((stem_audio, np.zeros((pad, stem_audio.shape[1]), dtype=np.float32)))

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

    print("stem loaded")
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
    print(f"slot {i} cleared")
    
def shift_slot(i):
    slot = slots[i]
    slot.half = 1 if slot.half == 0 else 0

def toggle_playback():
    if audio_engine.stream and audio_engine.stream.active:
        audio_engine.stop()
    else:
        audio_engine.start()

# -------------------- DETERMINATION -------------------- 

def export_mix_to_wav(filename="export.wav"):
    print("starting export")

    max_len = audio_engine.max_length
    if max_len == 0:
        print("sorry nothing")
        return
    
    master_mix = np.zeros((max_len, CHANNELS), dtype=np.float32)

    for slot in slots:
        if slot.empty or slot.stem is None:
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
        master_mix +=-processed_audio * slot.volume
    
    master_mix = np.clip(master_mix, -1.0, 1.0)

    try:
        sf.write(filename, master_mix, sample_rate)
        print(f"exported to {filename}")
    except Exception as e:
        print(f"export failed {e}")

def save_project():
    data = {
        "master": {
            "bpm": master_bpm,
            "key": master_key,
            "scale": master_scale
        },
        "slots": []
    }

    for i, slot in enumerate(slots):
        if not slot.empty:
            slot_data = {
                "index": i,
                "song_name": slot.song_name,
                "type": slot.type,
                "volume": slot.volume,
                "half": slot.half,

                # master override is like also a thing tho
                "detected_key": slot.key, 
                "detected_scale": slot.scale
            }
            data["slots"].append(slot_data)
    
    with open("project_data.json", "w") as f:
        json.dump(data, f, indent=4)
    print("project saved to project_data.json")

def load_project(screen_surface):
    if not os.path.exists("project_data.json"):
        print("no SAVE found")
        return

    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill(PALETTE["overlay"])
    screen_surface.blit(overlay, (0, 0))

    wait_w, wait_h = 300, 100
    wait_rect = pygame.Rect((SCREEN_W - wait_w)//2, (SCREEN_H - wait_h)//2, wait_w, wait_h)
    pygame.draw.rect(screen_surface, PALETTE["popup_bg"], wait_rect)
    pygame.draw.rect(screen_surface, PALETTE["popup_border"], wait_rect, 3)

    draw_text_centered("loading project", BIGFONT, PALETTE["text_main"], wait_rect)
    pygame.display.flip()

    try:
        with open("project_data.json", "r") as f:
            data = json.load(f)

        audio_engine.stop()

        global master_bpm, master_key, master_scale
        master_bpm = data["master"]["bpm"]
        master_key = data["master"]["key"]
        master_scale = data["master"]["scale"]
        
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
                s.volume = slot_data["volume"]
                s.target_volume = slot_data["volume"]
                s.half = slot_data["half"]
                
                pass 
            else:
                print(f"'{song_name}' not found during load.")

        audio_engine.start()
        print("project loaded successfully")

    except Exception as e:
        print(f"error loading project: {e}")

# stem select
dd_song = Dropdown(240, 200, 360, 35, get_song_list(), max_display_items=16)
dd_stem = Dropdown(240, 260, 360, 35, ["vocals", "bass", "lead", "drums"], max_display_items=4)

# manual tune
mt_key = Dropdown(220, 235, 180, 35, KEYS_FLAT if USE_FLATS else KEYS_SHARP, max_display_items=12)
mt_scale = Dropdown(440, 235, 180, 35, ["major", "minor"], max_display_items=2)
mt_bpm = InputBox(370, 200, 100, 35)

# -------------------- main loop -------------------- 

clock = pygame.time.Clock()
running = True
pulse_timer = 0

while running:
    # bg
    screen.fill(PALETTE["bg_dark"])
    
    # grid
    grid_size = 40
    for x in range(0, SCREEN_W, grid_size):
        pygame.draw.line(screen, PALETTE["bg_light"], (x, 0), (x, SCREEN_H))
    for y in range(0, SCREEN_H, grid_size):
        pygame.draw.line(screen, PALETTE["bg_light"], (0, y), (SCREEN_W, y))

    mx, my = pygame.mouse.get_pos() 

    input_blocked = panel_open or manual_override_open or options_open

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
    mt_btn_color = PALETTE["btn_manual"]

    if mt_btn_rect.collidepoint(mx, my) and not input_blocked:
        mt_outline_col = lighten_color(mt_btn_color, factor=1.2)
    else:
        mt_outline_col = darken_color(mt_btn_color)

    pygame.draw.rect(screen, mt_btn_color, mt_btn_rect, border_radius=4)
    pygame.draw.rect(screen, mt_outline_col, mt_btn_rect, 4, border_radius=4)
    
    draw_text_centered("Set Manual Tuning", FONT, PALETTE["text_main"], mt_btn_rect)

    # export WAV button
    btn_exp_w = 140
    btn_exp_h = 40
    btn_exp_rect = pygame.Rect(SCREEN_W - btn_exp_w - 20, SCREEN_H - btn_exp_h - 20, btn_exp_w, btn_exp_h)

    exp_col = PALETTE["accent"]

    if btn_exp_rect.collidepoint(mx, my) and not input_blocked:
        exp_outline = lighten_color(exp_col, 1.2)
    else:
        exp_outline = darken_color(exp_col)

    pygame.draw.rect(screen, exp_col, btn_exp_rect, border_radius=4)
    pygame.draw.rect(screen, exp_outline, btn_exp_rect, 4, border_radius=4)

    draw_text_centered("Export WAV", FONT, PALETTE["text_main"], btn_exp_rect)

    # save and load buttons
    btn_save_rect = pygame.Rect(SCREEN_W - 320, 20, 90, 40)
    btn_load_rect = pygame.Rect(SCREEN_W - 220, 20, 90, 40)

    save_col = PALETTE["btn_save"]
    load_col = PALETTE["btn_load"]

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

    draw_text_centered("Save", FONT, PALETTE["text_main"], btn_save_rect)
    draw_text_centered("Load", FONT, PALETTE["text_main"], btn_load_rect)

    # option button
    btn_opt_rect = pygame.Rect(SCREEN_W - 120, 20, 90, 40)
    
    if btn_opt_rect.collidepoint(mx, my) and not input_blocked:
        opt_outline = lighten_color(PALETTE["btn_ctrl"], 1.2)
    else:
        opt_outline = darken_color(PALETTE["btn_ctrl"])
        
    pygame.draw.rect(screen, PALETTE["btn_ctrl"], btn_opt_rect, border_radius=4)
    pygame.draw.rect(screen, opt_outline, btn_opt_rect, 4, border_radius=4)
    draw_text_centered("Options", FONT, PALETTE["text_main"], btn_opt_rect)

    # what
    pulse_val = 0.0
    if audio_engine.stream and audio_engine.stream.active:
        pulse_timer += clock.get_time()

    if master_bpm and master_bpm > 0:
        ms_per_beat = 60000 / master_bpm
        
        raw_sin = math.sin((pulse_timer * 2 * math.pi) / ms_per_beat - (math.pi / 2))
        
        steepness = 3.0
        curved_sin = math.tanh(raw_sin * steepness) # math tuah

        max_val = math.tanh(steepness)
        pulse_val = (curved_sin / max_val + 1) / 2

    # pause play restart button
    ctrl_btn_w = 60
    ctrl_btn_h = 40
    ctrl_gap = 12
    ctrl_y = 20
    total_ctrl_w = (ctrl_btn_w * 2) + ctrl_gap
    ctrl_start_x = (SCREEN_W // 2) - (total_ctrl_w // 2)

    
    btn_restart_rect = pygame.Rect(ctrl_start_x, ctrl_y, ctrl_btn_w, ctrl_btn_h)
    btn_play_rect = pygame.Rect(ctrl_start_x + ctrl_btn_w + ctrl_gap, ctrl_y, ctrl_btn_w, ctrl_btn_h)

    btn_ctrl_col = PALETTE["btn_ctrl"]
    icon_col = PALETTE["btn_icon"]

    # restart button
    if btn_restart_rect.collidepoint(mx, my) and not input_blocked:
        restart_outline = lighten_color(btn_ctrl_col, 1.2)
    else:
        restart_outline = darken_color(btn_ctrl_col)

    pygame.draw.rect(screen, btn_ctrl_col, btn_restart_rect, border_radius=2)
    pygame.draw.rect(screen, restart_outline, btn_restart_rect, 4, border_radius=2)

    pygame.draw.rect(screen, icon_col, (btn_restart_rect.centerx - 10, btn_restart_rect.centery - 8, 4, 16))
    pts_restart = [
        (btn_restart_rect.centerx - 5, btn_restart_rect.centery),
        (btn_restart_rect.centerx + 9, btn_restart_rect.centery - 8),
        (btn_restart_rect.centerx + 9, btn_restart_rect.centery + 8)
    ]
    pygame.draw.polygon(screen, icon_col, pts_restart)

    #pause button
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
        
        pygame.draw.rect(screen, icon_col, (btn_play_rect.centerx - gap - bar_w + 2, btn_play_rect.centery - bar_h//2, bar_w, bar_h))
        pygame.draw.rect(screen, icon_col, (btn_play_rect.centerx + gap - 2, btn_play_rect.centery - bar_h//2, bar_w, bar_h))
        
    else:
        tri_w = 14
        tri_h = 16
        gap = 4

        pts = [
            (btn_play_rect.centerx - 4, btn_play_rect.centery - tri_h//2),
            (btn_play_rect.centerx - 4, btn_play_rect.centery + tri_h//2),
            (btn_play_rect.centerx + 8, btn_play_rect.centery)
        ]
        pygame.draw.polygon(screen, icon_col, pts)

    # draw slots
    for i in range(12):
        slot = slots[i]
        cx = 120 + (i % 4) * 200
        cy = 150 + (i // 4) * 250
        
        dist = (mx - cx)**2 + (my - cy)**2
        is_hovered = dist <= CIRCLE_RADIUS**2 and not input_blocked

        if slot.empty:
            color = CIRCLE_COLOR_EMPTY
            outline_color = darken_color(color)
        else:
            color = STEM_COLORS.get(slot.type, CIRCLE_COLOR_DEFAULT)

            if master_bpm:
                base_outline = darken_color(color)
                bright_outline = lighten_color(color, factor=1.6)
                dynamic_pulse = pulse_val * slot.volume
                outline_color = lerp_color(base_outline, bright_outline, dynamic_pulse)
            else:
                outline_color = darken_color(color)

        if is_hovered:
            outline_color = PALETTE["hover_outline"]
            
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

        draw_dynamic_text(screen, name, FONT, cx, cy - 22, max_text_width, PALETTE["text_main"])
        draw_dynamic_text(screen, stype, FONT, cx, cy, max_text_width, PALETTE["text_dim"])
        if mode_label:
            draw_dynamic_text(screen, mode_label, FONT, cx, cy + 22, max_text_width, PALETTE["text_mode_label"])
            
        draw_offset_button(cx+30, cy+30, slot.half == 1)

        sx = cx - SLIDER_W // 2
        sy = cy + CIRCLE_RADIUS + 15
        draw_slider(sx, sy, SLIDER_W, SLIDER_H, slot.volume)

    # -------------------- panels -------------------- 
    
    # stem select
    if panel_open:
        pygame.draw.rect(screen, PALETTE["input_bg"], (220, 125, 400, 300))
        pygame.draw.rect(screen, PALETTE["input_border"], (220, 125, 400, 300), 2)
        
        title = BIGFONT.render(f"Slot {selected_slot}", True, TEXT_COLOR)
        screen.blit(title, (300, 135))

        screen.blit(FONT.render("Song:", True, TEXT_COLOR), (240, 175))
        dd_song.draw(screen)
        
        screen.blit(FONT.render("Stem:", True, TEXT_COLOR), (240, 235))
        dd_stem.draw(screen)

        stem_confirm_rect =  pygame.Rect(240, 325, 170, 50)
        stem_cancel_rect = pygame.Rect(430, 325, 170, 50)

        # confirm
        if stem_confirm_rect.collidepoint(mx, my):
            pygame.draw.rect(screen, PALETTE["btn_confirm_hl"], stem_confirm_rect)
        else:
            pygame.draw.rect(screen, PALETTE["btn_confirm"], stem_confirm_rect)
        draw_text_centered("CONFIRM", BIGFONT, TEXT_COLOR, stem_confirm_rect)

        # cancel
        if stem_cancel_rect.collidepoint(mx, my):
            pygame.draw.rect(screen, PALETTE["btn_cancel_hl"], stem_cancel_rect)
        else:
            pygame.draw.rect(screen, PALETTE["btn_cancel"], stem_cancel_rect)
        draw_text_centered("CANCEL", BIGFONT, TEXT_COLOR, stem_cancel_rect)
        
        # draw lists last
        dd_song.draw_list(screen)
        dd_stem.draw_list(screen)

    # manual tune
    if manual_override_open:
        pygame.draw.rect(screen, PALETTE["input_bg"], (170, 120, 500, 300))
        pygame.draw.rect(screen, PALETTE["input_border"], (170, 120, 500, 300), 2)
        
        title = BIGFONT.render("Manual Tuning Menu", True, TEXT_COLOR)
        screen.blit(title, (280, 135))
        
        screen.blit(FONT.render("BPM:", True, TEXT_COLOR), (310, 205))
        mt_bpm.draw(screen)

        screen.blit(FONT.render("Key:", True, TEXT_COLOR), (220, 265))
        mt_key.rect.y = 260 
        mt_key.draw(screen)

        screen.blit(FONT.render("Mode:", True, TEXT_COLOR), (440, 265))
        mt_scale.rect.y = 260
        mt_scale.draw(screen)

        tune_confirm_rect =  pygame.Rect(230, 340, 180, 50)
        tune_cancel_rect = pygame.Rect(430, 340, 180, 50)

        # confirm
        if tune_confirm_rect.collidepoint(mx, my):
            pygame.draw.rect(screen, PALETTE["btn_confirm_hl"], tune_confirm_rect)
        else:
            pygame.draw.rect(screen,  PALETTE["btn_confirm"], tune_confirm_rect)
        draw_text_centered("CONFIRM", BIGFONT, TEXT_COLOR, tune_confirm_rect)

        # cancel
        if tune_cancel_rect.collidepoint(mx, my):
            pygame.draw.rect(screen,  PALETTE["btn_cancel_hl"], tune_cancel_rect)
        else:
            pygame.draw.rect(screen, PALETTE["btn_cancel"], tune_cancel_rect)
        draw_text_centered("CANCEL", BIGFONT, TEXT_COLOR, tune_cancel_rect)
        
        mt_key.draw_list(screen)
        mt_scale.draw_list(screen)

    # options
    if options_open:
        pygame.draw.rect(screen, PALETTE["input_bg"], (220, 100, 400, 450))
        pygame.draw.rect(screen, PALETTE["input_border"], (220, 100, 400, 450), 2)
        
        title = BIGFONT.render("Options", True, TEXT_COLOR)
        screen.blit(title, (360, 115))
        
        screen.blit(FONT.render("Theme:", True, TEXT_COLOR), (250, 205))
        opt_theme_dd.draw(screen)
        
        screen.blit(FONT.render("Font:", True, TEXT_COLOR), (250, 275))
        opt_font_dd.draw(screen)
        
        screen.blit(FONT.render("Notation:", True, TEXT_COLOR), (250, 345))
        
        not_col = PALETTE["input_active"] if USE_FLATS else PALETTE["btn_manual"]
        not_text = "Flats (b)" if USE_FLATS else "Sharps (#)"
        
        pygame.draw.rect(screen, not_col, opt_notation_btn)
        pygame.draw.rect(screen, PALETTE["text_dark"], opt_notation_btn, 2)
        
        draw_text_centered(not_text, FONT, PALETTE["text_main"], opt_notation_btn)

        opt_close_rect = pygame.Rect(335, 480, 170, 50)
        if opt_close_rect.collidepoint(mx, my):
             pygame.draw.rect(screen, PALETTE["btn_confirm_hl"], opt_close_rect)
        else:
             pygame.draw.rect(screen, PALETTE["btn_confirm"], opt_close_rect)
        
        draw_text_centered("CLOSE", BIGFONT, TEXT_COLOR, opt_close_rect)

        opt_theme_dd.draw_list(screen)
        opt_font_dd.draw_list(screen)

    # -------------------- the fukin input clicky handler -------------------- 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        mx, my = pygame.mouse.get_pos()
        
        if options_open:
            if opt_theme_dd.handle_event(event):
                sel = opt_theme_dd.get_selected()
                if sel: 
                    load_theme(sel)
                    save_config()
                continue
                
            if opt_font_dd.handle_event(event):
                sel = opt_font_dd.get_selected()
                if sel: 
                    update_fonts(sel)
                    mt_bpm.font = FONT
                    mt_bpm.txt_surface = mt_bpm.font.render(mt_bpm.text, True, PALETTE["text_main"])
                    opt_theme_dd.font = SMALLERFONT
                    opt_font_dd.font = SMALLERFONT
                    dd_song.font = SMALLERFONT
                    dd_stem.font = SMALLERFONT
                    mt_key.font = SMALLERFONT
                    mt_scale.font = SMALLERFONT

                    save_config()
                continue

        if event.type == pygame.MOUSEWHEEL:
            if options_open:
                if opt_theme_dd.handle_event(event) or opt_font_dd.handle_event(event):
                    continue
            
            if panel_open:
                if dd_song.handle_event(event) or dd_stem.handle_event(event):
                    continue
            
            if manual_override_open:
                if mt_key.handle_event(event) or mt_scale.handle_event(event):
                    continue

            if not input_blocked:
                mx, my = pygame.mouse.get_pos()
                
                for i in range(12):
                    cx = 120 + (i % 4) * 200
                    cy = 150 + (i // 4) * 250
                    sx = cx - SLIDER_W // 2
                    sy = cy + CIRCLE_RADIUS + 15
                    
                    slider_rect = pygame.Rect(sx - 10, sy - 10, SLIDER_W + 20, SLIDER_H + 20)
                    
                    if slider_rect.collidepoint(mx, my):
                        scroll_amount = event.y * 0.05
                        
                        new_vol = slots[i].target_volume + scroll_amount
                        slots[i].target_volume = max(0.0, min(1.0, new_vol))
                        break
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if opt_notation_btn.collidepoint(mx, my):
                    USE_FLATS = not USE_FLATS
                    save_config()

                    new_keys = KEYS_FLAT if USE_FLATS else KEYS_SHARP
                    mt_key.update_options(new_keys)
                
                opt_close_rect = pygame.Rect(335, 480, 170, 50)
                if opt_close_rect.collidepoint(mx, my):
                    options_open = False
            
            continue

        # manual tuning inputs
        if manual_override_open:
            if mt_key.handle_event(event) or mt_scale.handle_event(event):
                continue

            mt_bpm.handle_event(event)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # hitboxes
                btn_manual_confirm = pygame.Rect(230, 340, 180, 50)
                btn_manual_cancel  = pygame.Rect(430, 340, 180, 50)
                
                # confirm click
                if btn_manual_confirm.collidepoint(mx, my):
                    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                    overlay.fill(PALETTE["overlay"])
                    screen.blit(overlay, (0, 0))

                    wait_w, wait_h = 300, 100
                    wait_rect = pygame.Rect((SCREEN_W - wait_w)//2, (SCREEN_H - wait_h)//2, wait_w, wait_h)
                    
                    wait_text = BIGFONT.render("processing...", True, PALETTE["text_main"])
                    sub_text = FONT.render("please Wait", True, PALETTE["text_dim"])

                    txt_rect1 = wait_text.get_rect(centerx=wait_rect.centerx, centery=wait_rect.centery - 15)
                    txt_rect2 = sub_text.get_rect(centerx=wait_rect.centerx, centery=wait_rect.centery + 15)

                    pygame.draw.rect(screen, PALETTE["panel_bg"], wait_rect)
                    pygame.draw.rect(screen, PALETTE["slider_fill"], wait_rect, 3)
                    screen.blit(wait_text, txt_rect1)
                    screen.blit(sub_text, txt_rect2)
                    pygame.display.flip()

                    try:
                        master_key = mt_key.get_selected()
                        master_scale = mt_scale.get_selected()
                        
                        new_bpm = None
                        if mt_bpm.text and float(mt_bpm.text) > 0:
                            new_bpm = float(mt_bpm.text)
                            master_bpm = new_bpm
                        
                        audio_engine.stop()
                        
                        slots_to_reload = []
                        for i, slot in enumerate(slots):
                            if not slot.empty:
                                slots_to_reload.append({
                                    "id": i,
                                    "name": slot.song_name,
                                    "type": slot.type
                                })
                                slot.stem = None 

                        audio_engine.max_length = 0
                        
                        for data in slots_to_reload:
                            print(f"reloading slot {data['id']}")
                            
                            pygame.draw.rect(screen, PALETTE["panel_bg"], wait_rect)
                            pygame.draw.rect(screen, PALETTE["slider_fill"], wait_rect, 3)
                            
                            screen.blit(wait_text, txt_rect1)
                            screen.blit(sub_text, txt_rect2)
                            
                            pygame.display.flip()

                            if use_relative_mode:
                                expected_scale = "minor" if master_scale == "major" else "major"
                            else:
                                expected_scale = master_scale 

                            if data['type'] == 'drums':
                                expected_scale = None 

                            song_path = os.path.join("Songs", data["name"])
                            add_stem_to_slot(data["id"], song_path, data["type"])
                        
                        audio_engine.start()

                    except Exception as e:
                        print(f"manual tuning error: {e}")
                        if audio_engine.stream is None or not audio_engine.stream.active:
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
            if dd_song.handle_event(event) or dd_stem.handle_event(event):
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # hitboxes
                btn_stem_confirm = pygame.Rect(240, 325, 170, 50)
                btn_stem_cancel  = pygame.Rect(430, 325, 170, 50)

                # confirm click
                if btn_stem_confirm.collidepoint(mx, my):
                    song_val = dd_song.get_selected()
                    stem_val = dd_stem.get_selected()
                    if song_val and stem_val:
                        add_stem_to_slot(selected_slot, song_val, stem_val)
                        panel_open = False
                
                # cancel click
                if btn_stem_cancel.collidepoint(mx, my):
                    panel_open = False
            
            continue

        # main screen inputs
        if event.type == pygame.MOUSEBUTTONDOWN:

            #expor
            if btn_exp_rect.collidepoint(mx, my) and  event.button == 1:
                overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                overlay.fill(PALETTE["overlay"])
                screen.blit(overlay, (0, 0))

                wait_w, wait_h = 300, 100
                wait_rect = pygame.Rect((SCREEN_W - wait_w)//2, (SCREEN_H - wait_h)//2, wait_w, wait_h)

                pygame.draw.rect(screen, PALETTE["popup_bg"], wait_rect)
                pygame.draw.rect(screen, PALETTE["popup_border"], wait_rect, 3)
                draw_text_centered("Rendering WAV...", BIGFONT, PALETTE["text_main"], wait_rect)

                pygame.display.flip()

                now = datetime.datetime.now()
                timestamp = now.isoformat()[:19].replace(":", "-")
                filename = f"jam_{timestamp}.wav"

                export_mix_to_wav(filename)
                continue

            #pause play restart
            if btn_restart_rect.collidepoint(mx, my) and event.button == 1:
                audio_engine.restart()

            if btn_play_rect.collidepoint(mx, my) and event.button == 1:
                toggle_playback()
            
            # top left manual button
            if 20 <= mx <= 220 and 20 <= my <= 60 and event.button == 1:
                manual_override_open = True

                if master_bpm is not None:
                    bpm_str = str(master_bpm)
                    if bpm_str.endswith(".0"):
                        bpm_str = bpm_str[:-2]
                    mt_bpm.text = bpm_str
                else:
                    mt_bpm.text = ""

                mt_bpm.txt_surface = mt_bpm.font.render(mt_bpm.text, True, PALETTE["text_main"])

                if master_key and master_key in mt_key.options:
                    mt_key.index = mt_key.options.index(master_key)

                if master_scale and master_scale in mt_scale.options:
                    mt_scale.index = mt_scale.options.index(master_scale)

            if btn_opt_rect.collidepoint(mx, my):
                options_open = True
                available_themes = [f.replace(".json","") for f in os.listdir("themes") if f.endswith(".json")]
                opt_theme_dd.update_options(available_themes)
                continue

            if btn_save_rect.collidepoint(mx, my) and event.button == 1:
                save_project()
            
            if btn_load_rect.collidepoint(mx, my) and event.button == 1:
                load_project(screen)
                if master_bpm:
                    mt_bpm.text = str(int(master_bpm))
                    mt_bpm.txt_surface = mt_bpm.font.render(mt_bpm.text, True, PALETTE["text_main"])

                # bpm typer
                if master_bpm:
                    mt_bpm.text = str(int(master_bpm))
                    mt_bpm.txt_surface = mt_bpm.font.render(mt_bpm.text, True, PALETTE["text_main"])
                else:
                    mt_bpm.text = ""
                    mt_bpm.txt_surface = mt_bpm.font.render("", True, PALETTE["text_main"])
                
                # sync dropdowns
                if master_key and master_key in mt_key.options: 
                    mt_key.index = mt_key.options.index(master_key)
                if master_scale and master_scale in mt_scale.options: 
                    mt_scale.index = mt_scale.options.index(master_scale)
                
                pygame.key.start_text_input()
                continue

            # right click clear slot
            if event.button == 3:
                for i in range(12):
                    cx = 120 + (i % 4) * 200
                    cy = 150 + (i // 4) * 250
                    if (mx - cx)**2 + (my - cy)**2 < CIRCLE_RADIUS**2:
                        clear_slot(i)
                        break

            # left click slider or open panel
            if event.button == 1:
                for slot_index in range(12):
                
                    slot_button_clicked = False # used to defuse priority tantrums
                    
                    btn_x=150 + (200 * (slot_index % 4))
                    btn_y=180 + (250 * (slot_index // 4))
                    
                    slot_btn=pygame.Rect(btn_x,btn_y,btn_x+32,btn_y+32)
                    
                    if btn_x <= mx <= btn_x+32 and btn_y <= my <= btn_y+32:

                        shift_slot(slot_index)
                    
                        slot_button_clicked=True
                    
                    if not slot_button_clicked:
                        cx = 120 + (slot_index % 4) * 200
                        cy = 150 + (slot_index // 4) * 250
                        sx = cx - SLIDER_W // 2
                        sy = cy + CIRCLE_RADIUS + 15
                        
                        # check slider
                        if sx <= mx <= sx + SLIDER_W and sy <= my <= sy + SLIDER_H:
                            dragging_slider = slot_index
                            rel = mx - sx
                            slots[slot_index].target_volume = max(0.0, min(1.0, rel / SLIDER_W))
                            break
                        
                        # check circle click
                        if dragging_slider is None:
                            if (mx - cx)**2 + (my - cy)**2 < CIRCLE_RADIUS**2:
                                panel_open = True
                                selected_slot = slot_index
                                dd_song.update_options(get_song_list()) 
                                break
                            
            

        if event.type == pygame.MOUSEBUTTONUP:
            dragging_slider = None

        if event.type == pygame.MOUSEMOTION and dragging_slider is not None:
            i = dragging_slider
            cx = 120 + (i % 4) * 200
            sx = cx - SLIDER_W // 2
            rel = mx - sx
            slots[i].target_volume = max(0.0, min(1.0, rel / SLIDER_W))

    # ---------- text hud element idfk ----------

    # the text
    if master_bpm is not None:
        display_k = get_display_key(master_key)
        stats_text = f"BPM: {master_bpm:.1f} | KEY: {display_k} {master_scale}"
    else:
        stats_text = "No Tuning Set"
    
    # rendering
    stats_surf = BIGFONT.render(stats_text, True, TEXT_COLOR)
    stats_outline = BIGFONT.render(stats_text, True, PALETTE["text_dark"])

    # pos
    stat_x = 19
    stat_y = SCREEN_H - stats_surf.get_height() - 10

    # draw outline
    offsets = [
        (-1, -1), (0, -1), (1, -1),
        (-1,  0),          (1,  0),
        (-1,  1), (0,  1), (1,  1)
    ]

    for dx, dy in offsets:
        screen.blit(stats_outline, (stat_x + dx, stat_y + dy))

    # draw text
    screen.blit(stats_surf, (stat_x, stat_y))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
audio_engine.stop()