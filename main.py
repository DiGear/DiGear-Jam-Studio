import os
import json
import math
import numpy as np
import soundfile as sf
import pyrubberband as rb
import sounddevice as sd
import pygame

# -------------------- constants -------------------- 

KEY_TO_INT = {
    "C": 0, "C#": 1, "D": 2, "D#": 3,
    "E": 4, "F": 5, "F#": 6, "G": 7,
    "G#": 8, "A": 9, "A#": 10, "B": 11
}

sample_rate = 44100
BUFFER_SIZE = 2048
CHANNELS = 2

# -------------------- ochame kinous -------------------- 

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

def get_song_list():
    # scan folders
    base = "Songs"
    if not os.path.exists(base):
        os.makedirs(base)
        return []
    return [os.path.join(base, x) for x in os.listdir(base) if os.path.isdir(os.path.join(base, x))]

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
        self.offset = 0
        self.half = 0

# init slots
slots = [Slot() for _ in range(8)]
master_bpm = None
master_key = None
master_scale = None
manual_override_open = False

def reset_master():
    global master_bpm, master_key, master_scale
    master_bpm = None
    master_key = None
    master_scale = None

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
        
            # Make an offset position for the current stem
            offset_pos=(pos+slot.offset) % self.max_length 
            
            if slot.empty or slot.stem is None:
                continue

            audio = slot.stem
            length = len(audio)
            if length == 0:
                continue

            end = offset_pos + frames
            
            # handle wrap around
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

def clear_slot(i):
    slot = slots[i]
    slot.empty = True
    slot.stem = None
    slot.song_name = None
    slot.type = None
    slot.volume = 1.0
    slot.offset = 0
    slot.half = 0
    print(f"slot {i} cleared")
    
def shift_slot(i):
    slot = slots[i]
    if slot.half == 0:
        slot.half = 1
        slot.offset = audio_engine.max_length // 2
    else:
        slot.half = 0
        slot.offset = 0

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

audio_engine = AudioEngine(slots, sample_rate)
audio_engine.start()

# -------------------- DETERMINATION -------------------- 

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
    overlay.fill((0, 0, 0, 180))
    screen_surface.blit(overlay, (0, 0))

    wait_w, wait_h = 300, 100
    wait_rect = pygame.Rect((SCREEN_W - wait_w)//2, (SCREEN_H - wait_h)//2, wait_w, wait_h)
    pygame.draw.rect(screen_surface, (40, 40, 40), wait_rect)
    pygame.draw.rect(screen_surface, (0, 200, 80), wait_rect, 3)

    wait_text = BIGFONT.render("loading project", True, (255, 255, 255))
    screen_surface.blit(wait_text, (wait_rect.centerx - wait_text.get_width()//2, wait_rect.centery - 15))
    pygame.display.flip()

    try:
        with open("project_data.json", "r") as f:
            data = json.load(f)

        audio_engine.stop()

        global master_bpm, master_key, master_scale
        master_bpm = data["master"]["bpm"]
        master_key = data["master"]["key"]
        master_scale = data["master"]["scale"]
        
        for i in range(8):
            clear_slot(i)
        
        audio_engine.max_length = 0

        for slot_data in data["slots"]:
            idx = slot_data["index"]
            song_name = slot_data["song_name"]
            stem_type = slot_data["type"]
            
            song_path = os.path.join("Songs", song_name)
            
            if os.path.exists(song_path):
                add_stem_to_slot(idx, song_path, stem_type)
                
                s = slots[idx]
                s.volume = slot_data["volume"]
                s.half = slot_data["half"]
                
                if s.half == 1 and not s.empty:
                     s.offset = audio_engine.max_length // 2
            else:
                print(f"'{song_name}' not found during load.")

        audio_engine.start()
        print("project loaded successfully")

    except Exception as e:
        print(f"error loading project: {e}")

# -------------------- fuckin pygame STUPID SHIT FUCK I HATE PYGAME AAAAA -------------------- 

pygame.init()
SCREEN_W, SCREEN_H = 840, 550
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("DiGear Jam Studio")
favicon = pygame.image.load("favicon.png")
pygame.display.set_icon(favicon)
FONT = pygame.font.SysFont("Arial", 22)
BIGFONT = pygame.font.SysFont("Arial", 28)

#images
btn_offset_off=pygame.image.load('gui/btn_offset_off.png').convert_alpha()
btn_offset_on=pygame.image.load('gui/btn_offset_on.png').convert_alpha()
btn_offset_hover=pygame.image.load('gui/btn_offset_hover.png').convert_alpha()


# colors
CIRCLE_RADIUS = 60
CIRCLE_COLOR_EMPTY = (60, 60, 60)
CIRCLE_COLOR_DEFAULT = (80, 130, 255)

STEM_COLORS = {
    "vocals": (230, 230, 100),
    "bass": (136, 213, 109),
    "drums": (102, 215, 215),
    "lead": (210, 132, 195)
}

TEXT_COLOR = (255, 255, 255)

SLIDER_W = 120
SLIDER_H = 10
SLIDER_COLOR = (120, 120, 120)
SLIDER_FILL = (0, 200, 80)
SLIDER_TIP = (255, 255, 255)

class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = (60, 60, 60)
        self.color_active = (100, 100, 255)
        self.color = self.color_inactive
        self.text = text
        self.font = pygame.font.SysFont("Arial", 22)
        self.txt_surface = self.font.render(text, True, (255, 255, 255))
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
                self.txt_surface = self.font.render(self.text, True, (255, 255, 255))
        return False

    def draw(self, screen):
        # Draw background
        pygame.draw.rect(screen, (30, 30, 30), self.rect)
        # Draw text
        screen.blit(self.txt_surface, (self.rect.x + 10, self.rect.y + 5))
        # Draw outline
        pygame.draw.rect(screen, self.color, self.rect, 2)

class Dropdown:
    def __init__(self, x, y, w, h, options, default_index=0, max_display_items=5):
        self.rect = pygame.Rect(x, y, w, h)
        self.options = options
        self.index = default_index
        self.is_open = False
        self.font = pygame.font.SysFont("Arial", 20)
        self.active_option_color = (60, 60, 60)
        self.hover_color = (80, 80, 100)
        self.bg_color = (40, 40, 40)
        self.text_color = (255, 255, 255)
        self.border_color = (100, 100, 100)
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
            
            num_items = len(self.options)
            total_height = num_items * self.item_height
            display_count = min(num_items, self.max_display_items)
            display_height = display_count * self.item_height
            
            list_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height, self.rect.width, display_height)
            pygame.draw.rect(screen, self.bg_color, list_rect)
            
            old_clip = screen.get_clip()
            screen.set_clip(list_rect)
            
            start_y = list_rect.y - self.scroll_y
            
            for i, opt in enumerate(self.options):
                opt_y = start_y + (i * self.item_height)
    
                if opt_y + self.item_height < list_rect.y or opt_y > list_rect.bottom:
                    continue
                    
                opt_rect = pygame.Rect(self.rect.x, opt_y, self.rect.width - self.scrollbar_width, self.item_height)
                
                is_hovered = opt_rect.collidepoint(mx, my) and list_rect.collidepoint(mx, my)
                color = self.hover_color if is_hovered else self.active_option_color
                
                pygame.draw.rect(screen, color, opt_rect)
                pygame.draw.rect(screen, self.border_color, opt_rect, 1)
                
                display_text = str(opt)
                if os.path.sep in display_text:
                    display_text = os.path.basename(display_text)
                    
                surf = self.font.render(display_text, True, self.text_color)
                
                text_y = opt_rect.y + (self.item_height - surf.get_height()) // 2
                screen.blit(surf, (opt_rect.x + 10, text_y))
            
            screen.set_clip(old_clip)
            
            pygame.draw.rect(screen, self.border_color, list_rect, 2)
            
            # scrollbar
            if total_height > display_height:
                sb_bg_rect = pygame.Rect(self.rect.right - self.scrollbar_width, list_rect.y, self.scrollbar_width, display_height)
                pygame.draw.rect(screen, (30, 30, 30), sb_bg_rect)
                
                ratio = display_height / total_height
                thumb_h = max(20, display_height * ratio)
                
                max_scroll = total_height - display_height
                scroll_ratio = self.scroll_y / max_scroll
                thumb_y = list_rect.y + scroll_ratio * (display_height - thumb_h)
                
                sb_thumb_rect = pygame.Rect(self.rect.right - self.scrollbar_width + 2, thumb_y, self.scrollbar_width - 4, thumb_h)
                pygame.draw.rect(screen, (100, 100, 100), sb_thumb_rect, border_radius=4)

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL and self.is_open:
            mx, my = pygame.mouse.get_pos()
            
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

dragging_slider = None
panel_open = False
selected_slot = None

# relative/parallel mode shit
use_relative_mode = False

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

# stem select
dd_song = Dropdown(240, 200, 360, 35, get_song_list(), max_display_items=7)
dd_stem = Dropdown(240, 260, 360, 35, ["vocals", "bass", "lead", "drums"], max_display_items=4)

# manual tune
mt_key = Dropdown(220, 235, 180, 35, list(KEY_TO_INT.keys()), max_display_items=6)
mt_scale = Dropdown(440, 235, 180, 35, ["major", "minor"], max_display_items=2)
mt_bpm = InputBox(370, 200, 100, 35)

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
    if x <= mx < x+32 and y <= my < y+32:
        screen.blit(btn_offset_hover, (x,y))

def draw_dynamic_text(surface, text, font, center_x, center_y, max_width, color):
    # draws text with outline and scales if too big
    if not text:
        return

    text_surf = font.render(text, True, color)
    outline_surf = font.render(text, True, (0, 0, 0))

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

# -------------------- main loop -------------------- 

clock = pygame.time.Clock()
running = True

while running:
    # bg
    screen.fill((15, 15, 15))

    # manual tune button
    mt_btn_rect = pygame.Rect(20, 20, 200, 40)
    mt_btn_color = (0, 170, 60)

    pygame.draw.rect(screen, mt_btn_color, mt_btn_rect, border_radius=4)
    pygame.draw.rect(screen, darken_color(mt_btn_color), mt_btn_rect, 4, border_radius=4)
    
    screen.blit(FONT.render("Set Manual Tuning", True, (255, 255, 255)), (30, 28))

    # save and load buttons
    btn_save_rect = pygame.Rect(SCREEN_W - 220, 20, 90, 40, border_radius=4)
    btn_load_rect = pygame.Rect(SCREEN_W - 120, 20, 90, 40, border_radius=4)

    save_col = (230, 120, 40)
    load_col = (60, 120, 210)

    pygame.draw.rect(screen, save_col, btn_save_rect, border_radius=4)
    pygame.draw.rect(screen, darken_color(save_col), btn_save_rect, 4, border_radius=4)

    pygame.draw.rect(screen, load_col, btn_load_rect, border_radius=4)
    pygame.draw.rect(screen, darken_color(load_col), btn_load_rect, 4, border_radius=4)

    screen.blit(FONT.render("Save", True, (255,255,255)), (btn_save_rect.x + 20, btn_save_rect.y + 8))
    screen.blit(FONT.render("Load", True, (255,255,255)), (btn_load_rect.x + 20, btn_load_rect.y + 8))

    # what
    pulse_val = 0.0
    if master_bpm and master_bpm > 0:
        current_time = pygame.time.get_ticks()
        ms_per_beat = 60000 / master_bpm
        
        raw_sin = math.sin((current_time * 2 * math.pi) / ms_per_beat - (math.pi / 2))
        steepness = 3.0
        curved_sin = math.tanh(raw_sin * steepness) # math tuah

        max_val = math.tanh(steepness)
        pulse_val = (curved_sin / max_val + 1) / 2

    # draw slots
    for i in range(8):
        slot = slots[i]
        cx = 120 + (i % 4) * 200
        cy = 150 if i < 4 else 400
        
        if slot.empty:
            color = CIRCLE_COLOR_EMPTY
            outline_color = darken_color(color)
        else:
            color = STEM_COLORS.get(slot.type, CIRCLE_COLOR_DEFAULT)

            if master_bpm:
                base_outline = darken_color(color)
                bright_outline = lighten_color(color, factor=1.4)
                outline_color = lerp_color(base_outline, bright_outline, pulse_val)
            else:
                outline_color = darken_color(color)
            
        pygame.draw.circle(screen, color, (cx, cy), CIRCLE_RADIUS)
        pygame.draw.circle(screen, outline_color, (cx, cy), CIRCLE_RADIUS, 5)
        
        max_text_width = (CIRCLE_RADIUS * 2) - 10
        name = slot.song_name if slot.song_name else "Empty"
        stype = slot.type if slot.type else ""

        mode_label = ""
        mode_color = (200, 255, 200)

        if not slot.empty and slot.type != "drums" and master_scale:
            if slot.scale == master_scale:
                 mode_label = f"{slot.scale.capitalize()} (Parallel)"
            else:
                 mode_label = f"{slot.scale.capitalize()} (Relative)"
        elif not slot.empty and slot.type == "drums":
            mode_label = "Neutral Mode"

        # draw tuah
        draw_dynamic_text(screen, name, FONT, cx, cy - 22, max_text_width, TEXT_COLOR)
        draw_dynamic_text(screen, stype, FONT, cx, cy, max_text_width, (230, 230, 230))
        if mode_label:
            draw_dynamic_text(screen, mode_label, FONT, cx, cy + 22, max_text_width, mode_color)
            
        draw_offset_button(cx+30, cy+30, slot.half == 1)

        sx = cx - SLIDER_W // 2
        sy = cy + CIRCLE_RADIUS + 15
        draw_slider(sx, sy, SLIDER_W, SLIDER_H, slot.volume)

    # -------------------- panels -------------------- 
    
    # stem select
    if panel_open:
        pygame.draw.rect(screen, (30, 30, 30), (220, 125, 400, 300))
        
        title = BIGFONT.render(f"Slot {selected_slot}", True, TEXT_COLOR)
        screen.blit(title, (300, 135))

        screen.blit(FONT.render("Song:", True, TEXT_COLOR), (240, 175))
        dd_song.draw(screen)
        
        screen.blit(FONT.render("Stem:", True, TEXT_COLOR), (240, 235))
        dd_stem.draw(screen)

        # confirm
        pygame.draw.rect(screen, (0, 160, 80), (240, 325, 170, 50))
        screen.blit(BIGFONT.render("Confirm", True, TEXT_COLOR), (275, 335))

        # cancel
        pygame.draw.rect(screen, (160, 60, 60), (430, 325, 170, 50))
        screen.blit(BIGFONT.render("Cancel", True, TEXT_COLOR), (470, 335))
        
        # draw lists last
        dd_song.draw_list(screen)
        dd_stem.draw_list(screen)

    # manual tune
    if manual_override_open:
        pygame.draw.rect(screen, (30, 30, 30), (170, 120, 500, 300))
        
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

        btn_confirm_rect = pygame.Rect(230, 340, 180, 50)
        pygame.draw.rect(screen, (0, 160, 80), btn_confirm_rect)
        screen.blit(BIGFONT.render("CONFIRM", True, TEXT_COLOR), (255, 350))
        
        btn_cancel_rect = pygame.Rect(430, 340, 180, 50)
        pygame.draw.rect(screen, (160, 60, 60), btn_cancel_rect)
        screen.blit(BIGFONT.render("CANCEL", True, TEXT_COLOR), (470, 350))
        
        mt_key.draw_list(screen)
        mt_scale.draw_list(screen)

    # -------------------- the fukin input clicky handler -------------------- 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        mx, my = pygame.mouse.get_pos()

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
                    overlay.fill((0, 0, 0, 180))
                    screen.blit(overlay, (0, 0))

                    wait_w, wait_h = 300, 100
                    wait_rect = pygame.Rect((SCREEN_W - wait_w)//2, (SCREEN_H - wait_h)//2, wait_w, wait_h)
                    pygame.draw.rect(screen, (40, 40, 40), wait_rect)
                    pygame.draw.rect(screen, (0, 200, 80), wait_rect, 3)

                    wait_text = BIGFONT.render("Processing...", True, (255, 255, 255))
                    sub_text = FONT.render("Please Wait", True, (200, 200, 200))
                    
                    screen.blit(wait_text, (wait_rect.centerx - wait_text.get_width()//2, wait_rect.y + 20))
                    screen.blit(sub_text, (wait_rect.centerx - sub_text.get_width()//2, wait_rect.y + 60))
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
                            
                            pygame.draw.rect(screen, (40, 40, 40), wait_rect)
                            pygame.draw.rect(screen, (0, 200, 80), wait_rect, 3)
                            
                            header_text = FONT.render("currently tuning:", True, (200, 200, 200))
                            info_str = f"{data['name']} ({data['type']})"
                            info_text = FONT.render(info_str, True, (255, 255, 255))

                            screen.blit(header_text, (wait_rect.centerx - header_text.get_width()//2, wait_rect.centery - 30))
                            draw_dynamic_text(screen, info_str, FONT, wait_rect.centerx, wait_rect.centery + 5, wait_rect.width - 20, (255, 255, 255))
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
            
            # top left manual button
            if 20 <= mx <= 220 and 20 <= my <= 60 and event.button == 1:
                manual_override_open = True

            btn_save_rect = pygame.Rect(SCREEN_W - 220, 20, 90, 40)
            btn_load_rect = pygame.Rect(SCREEN_W - 120, 20, 90, 40)

            if btn_save_rect.collidepoint(mx, my) and event.button == 1:
                save_project()
            
            if btn_load_rect.collidepoint(mx, my) and event.button == 1:
                load_project(screen)
                if master_bpm:
                    mt_bpm.text = str(int(master_bpm))
                    mt_bpm.txt_surface = mt_bpm.font.render(mt_bpm.text, True, (255, 255, 255))

                # bpm typer
                if master_bpm:
                    mt_bpm.text = str(int(master_bpm))
                    mt_bpm.txt_surface = mt_bpm.font.render(mt_bpm.text, True, (255, 255, 255))
                else:
                    mt_bpm.text = ""
                    mt_bpm.txt_surface = mt_bpm.font.render("", True, (255, 255, 255))
                
                # sync dropdowns
                if master_key and master_key in mt_key.options: 
                    mt_key.index = mt_key.options.index(master_key)
                if master_scale and master_scale in mt_scale.options: 
                    mt_scale.index = mt_scale.options.index(master_scale)
                
                pygame.key.start_text_input()
                continue

            # right click clear slot
            if event.button == 3:
                for i in range(8):
                    cx = 120 + (i % 4) * 200
                    cy = 150 if i < 4 else 400
                    if (mx - cx)**2 + (my - cy)**2 < CIRCLE_RADIUS**2:
                        clear_slot(i)
                        break

            # left click slider or open panel
            if event.button == 1:
                for slot_index in range(8):
                
                    slot_button_clicked = False # used to defuse priority tantrums
                    
                    btn_x=150 + (200 * (slot_index % 4))
                    btn_y=180 + (250 * (slot_index // 4))
                    
                    slot_btn=pygame.Rect(btn_x,btn_y,btn_x+32,btn_y+32)
                    
                    if btn_x <= mx <= btn_x+32 and btn_y <= my <= btn_y+32:

                        shift_slot(slot_index)
                    
                        slot_button_clicked=True
                    
                    if not slot_button_clicked:
                        cx = 120 + (slot_index % 4) * 200
                        cy = 150 if slot_index < 4 else 400
                        sx = cx - SLIDER_W // 2
                        sy = cy + CIRCLE_RADIUS + 15
                        
                        # check slider
                        if sx <= mx <= sx + SLIDER_W and sy <= my <= sy + SLIDER_H:
                            dragging_slider = slot_index
                            rel = mx - sx
                            slots[slot_index].volume = max(0.0, min(1.0, rel / SLIDER_W))
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
            slots[i].volume = max(0.0, min(1.0, rel / SLIDER_W))

    # ---------- text hud element idfk ----------

    # the text
    if master_bpm is not None:
        stats_text = f"BPM: {master_bpm:.1f} | KEY: {master_key} {master_scale}"
    else:
        stats_text = "No Tuning Set"
    
    # rendering
    stats_surf = BIGFONT.render(stats_text, True, TEXT_COLOR)
    stats_outline = BIGFONT.render(stats_text, True, (0, 0, 0))

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