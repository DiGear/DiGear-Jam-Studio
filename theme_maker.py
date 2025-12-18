import pygame
import json
import os
import math

APP_W, APP_H = 840, 825
EDITOR_W = 400
SCREEN_W = APP_W + EDITOR_W
SCREEN_H = APP_H

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("DiGear Jam Studio Theme Studio")

pygame.key.set_repeat(400, 30)

try:
    favicon = pygame.image.load("favicon.png")
    pygame.display.set_icon(favicon)
except:
    pass

if not os.path.exists("themes"):
    os.makedirs("themes")

try:
    FONT_MAIN = pygame.font.SysFont("Arial", 18)
    FONT_TITLE = pygame.font.SysFont("Arial", 24, bold=True)
    FONT_SMALL = pygame.font.SysFont("Arial", 14)
    FONT_MEDIUM_APP = pygame.font.SysFont("Arial", 22)
    FONT_LARGE_APP = pygame.font.SysFont("Arial", 28)
except:
    FONT_MAIN = pygame.font.Font(None, 24)
    FONT_TITLE = pygame.font.Font(None, 32)
    FONT_SMALL = pygame.font.Font(None, 20)
    FONT_MEDIUM_APP = pygame.font.Font(None, 26)
    FONT_LARGE_APP = pygame.font.Font(None, 34)

default_palette = {
    "bg_dark": (18, 18, 18),
    "bg_light": (45, 45, 45),
    "panel_bg": (30, 30, 30),
    "overlay": (0, 0, 0, 160),
    "popup_bg": (35, 35, 35),
    "popup_border": (60, 140, 220),
    "hover_outline": (200, 200, 200),
    "text_main": (230, 230, 230),
    "text_dim": (150, 150, 150),
    "text_dark": (20, 20, 20),
    "text_mode_label": (160, 210, 160),
    "slot_default": (100, 100, 100),
    "slot_empty": (50, 50, 50),
    "slot_vocals": (255, 200, 80),
    "slot_bass": (80, 220, 140),
    "slot_drums": (80, 180, 240),
    "slot_lead": (240, 100, 160),
    "accent": (60, 140, 220),
    "input_bg": (40, 40, 40),
    "input_border": (70, 70, 70),
    "input_active": (60, 140, 220),
    "scrollbar": (80, 80, 80),
    "slider_track": (60, 60, 60),
    "slider_fill": (60, 140, 220),
    "slider_knob": (240, 240, 240),
    "btn_manual": (140, 80, 180),
    "btn_save": (50, 160, 80),
    "btn_load": (60, 140, 220),
    "btn_ctrl": (50, 50, 50),
    "btn_icon": (200, 200, 200),
    "btn_confirm": (50, 160, 80),
    "btn_cancel": (180, 60, 60),
    "btn_mute_active": (220, 140, 40),
    "btn_solo_active": (60, 140, 220),
    "btn_half_active": (200, 80, 200),
    "btn_inactive": (50, 50, 50),
}

current_palette = default_palette.copy()
selected_key = "bg_dark"
theme_name_input = "default"
save_message = ""
save_message_timer = 0


def darken_color(color, factor=0.8):
    if len(color) == 4:
        r, g, b, a = color
        return (int(r * factor), int(g * factor), int(b * factor), a)
    r, g, b = color
    return (int(r * factor), int(g * factor), int(b * factor))


def lighten_color(color, factor=1.3):
    if len(color) == 4:
        r, g, b, a = color
        return (
            min(255, int(r * factor)),
            min(255, int(g * factor)),
            min(255, int(b * factor)),
            a,
        )
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


def draw_dynamic_text(surface, text, font, center_x, center_y, max_width, color):
    if not text:
        return

    text_surf = font.render(text, True, color)
    outline_surf = font.render(text, True, current_palette["text_dark"])

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
    offsets = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
    for dx, dy in offsets:
        surface.blit(outline_surf, (rect.x + dx, rect.y + dy))
    surface.blit(text_surf, rect)


def draw_action_button(surface, text, rect, base_color):
    r, g, b = base_color[:3]
    brightness = r * 0.299 + g * 0.587 + b * 0.114
    text_col = (
        current_palette["text_dark"]
        if brightness > 140
        else current_palette["text_main"]
    )
    pygame.draw.rect(surface, base_color, rect, border_radius=4)
    border_col = darken_color(base_color, 0.8)

    pygame.draw.rect(surface, border_col, rect, 4, border_radius=4)

    txt_surf = FONT_MEDIUM_APP.render(text, True, text_col)
    txt_rect = txt_surf.get_rect(center=rect.center)
    surface.blit(txt_surf, txt_rect)


def draw_text_centered_simple(surf, text, font, color, target_rect):
    txt = font.render(text, True, color)
    rect = txt.get_rect(center=target_rect.center)
    surf.blit(txt, rect)


def draw_dummy_app(surface):
    surface.fill(current_palette["bg_dark"])
    grid_size = 40
    for x in range(0, APP_W, grid_size):
        pygame.draw.line(surface, current_palette["bg_light"], (x, 0), (x, APP_H))
    for y in range(0, APP_H, grid_size):
        pygame.draw.line(surface, current_palette["bg_light"], (0, y), (APP_W, y))

    btn_defs = [
        ("Manual Tuning", (20, 20, 160, 40), current_palette["btn_manual"]),
        ("Reset", (190, 20, 90, 40), current_palette["btn_cancel"]),
        ("Save", (APP_W - 320, 20, 90, 40), current_palette["btn_save"]),
        ("Load", (APP_W - 220, 20, 90, 40), current_palette["btn_load"]),
        ("Options", (APP_W - 120, 20, 90, 40), current_palette["btn_ctrl"]),
    ]
    for text, rect_t, col in btn_defs:
        draw_action_button(surface, text, pygame.Rect(rect_t), col)

    mid_x = APP_W // 2
    ctrl_y = 20
    ctrl_w = 60
    ctrl_h = 40

    r_rect = pygame.Rect(mid_x - 65, ctrl_y, ctrl_w, ctrl_h)
    pygame.draw.rect(surface, current_palette["btn_ctrl"], r_rect, border_radius=2)
    pygame.draw.rect(
        surface, darken_color(current_palette["btn_ctrl"]), r_rect, 4, border_radius=2
    )
    icon_col = current_palette["btn_icon"]
    pygame.draw.rect(
        surface, icon_col, (r_rect.centerx - 10, r_rect.centery - 8, 4, 16)
    )
    pygame.draw.polygon(
        surface,
        icon_col,
        [
            (r_rect.centerx - 5, r_rect.centery),
            (r_rect.centerx + 9, r_rect.centery - 8),
            (r_rect.centerx + 9, r_rect.centery + 8),
        ],
    )

    p_rect = pygame.Rect(mid_x + 5, ctrl_y, ctrl_w, ctrl_h)
    pygame.draw.rect(surface, current_palette["btn_ctrl"], p_rect, border_radius=2)
    pygame.draw.rect(
        surface, darken_color(current_palette["btn_ctrl"]), p_rect, 4, border_radius=2
    )
    pygame.draw.polygon(
        surface,
        icon_col,
        [
            (p_rect.centerx - 4, p_rect.centery - 8),
            (p_rect.centerx - 4, p_rect.centery + 8),
            (p_rect.centerx + 8, p_rect.centery),
        ],
    )

    slot_defs = [
        (0, 0, "vocals", "Vocals", False, False, False, True, "Major"),
        (1, 0, "bass", "Bass", False, False, True, True, "Relative Minor"),
        (2, 0, "drums", "Drums", False, False, False, True, "Neutral"),
        (3, 0, "lead", "Lead", False, False, False, True, "Major"),
        (0, 1, "multi_mute", "", True, False, False, False, ""),
        (1, 1, "multi_solo", "", False, True, False, True, ""),
        (2, 1, "multi_dim", "", False, False, False, False, ""),
        (3, 1, None, "", False, False, False, False, ""),
    ]

    for (
        col,
        row,
        stype,
        name,
        is_mute,
        is_solo,
        is_half,
        force_pulse,
        mode_label,
    ) in slot_defs:
        cx = 120 + col * 200
        cy = 130 + row * 230

        pulse_val = (math.sin(pygame.time.get_ticks() / 150) + 1) / 2
        if stype and stype.startswith("multi"):
            base_cols = [
                current_palette["slot_vocals"],
                current_palette["slot_bass"],
                current_palette["slot_drums"],
                current_palette["slot_lead"],
            ]

            fill_cols = []
            outline_cols = []

            for c in base_cols:
                fill_c = c
                out_c = c

                if stype == "multi_mute":
                    fill_c = darken_color(c, 0.5)
                    out_c = darken_color(fill_c, 0.8)
                elif stype == "multi_dim":
                    fill_c = darken_color(c, 0.3)
                    out_c = darken_color(fill_c, 0.8)
                elif stype == "multi_solo":
                    base_out = darken_color(c)
                    bright_out = lighten_color(c, 1.6)
                    out_c = lerp_color(base_out, bright_out, pulse_val)

                fill_cols.append(fill_c)
                outline_cols.append(out_c)

            original_clip = surface.get_clip()
            r = 60
            rects = [
                pygame.Rect(cx - r, cy - r, r, r),
                pygame.Rect(cx, cy - r, r, r),
                pygame.Rect(cx - r, cy, r, r),
                pygame.Rect(cx, cy, r, r),
            ]

            for i in range(4):
                surface.set_clip(rects[i])
                pygame.draw.circle(surface, fill_cols[i], (cx, cy), r)
                pygame.draw.circle(surface, outline_cols[i], (cx, cy), r, 5)

            surface.set_clip(original_clip)

        else:
            if stype is None:
                color = current_palette["slot_empty"]
            else:
                stem_cols = {
                    "vocals": current_palette["slot_vocals"],
                    "bass": current_palette["slot_bass"],
                    "drums": current_palette["slot_drums"],
                    "lead": current_palette["slot_lead"],
                }
                color = stem_cols.get(stype, current_palette["slot_default"])

            if force_pulse:
                base_outline = darken_color(color)
                bright_outline = lighten_color(color, 1.6)
                outline = lerp_color(base_outline, bright_outline, pulse_val)
            else:
                outline = darken_color(color)

            pygame.draw.circle(surface, color, (cx, cy), 60)
            pygame.draw.circle(surface, outline, (cx, cy), 60, 5)

        if row == 0:
            draw_dynamic_text(
                surface,
                name,
                FONT_MEDIUM_APP,
                cx,
                cy - 22,
                110,
                current_palette["text_main"],
            )
            stype_txt = stype.capitalize() if stype else "Empty"
            draw_dynamic_text(
                surface,
                stype_txt,
                FONT_MEDIUM_APP,
                cx,
                cy,
                110,
                current_palette["text_dim"],
            )
            draw_dynamic_text(
                surface,
                mode_label,
                FONT_MEDIUM_APP,
                cx,
                cy + 22,
                110,
                current_palette["text_mode_label"],
            )

        if stype and not stype.startswith("multi") and row == 0:
            hx, hy = cx + 30, cy + 30
            h_col = (
                current_palette["btn_half_active"]
                if is_half
                else current_palette["btn_inactive"]
            )
            pygame.draw.rect(surface, h_col, (hx, hy, 32, 32), border_radius=4)
            pygame.draw.rect(
                surface,
                current_palette["input_border"],
                (hx, hy, 32, 32),
                2,
                border_radius=4,
            )
            draw_dynamic_text(
                surface, "1/2", FONT_SMALL, hx + 16, hy + 16, 30, (255, 255, 255)
            )

        m_col = (
            current_palette["btn_mute_active"]
            if is_mute
            else current_palette["btn_inactive"]
        )
        s_col = (
            current_palette["btn_solo_active"]
            if is_solo
            else current_palette["btn_inactive"]
        )

        mx, my = cx - 45, cy + 32
        m_rect = pygame.Rect(mx, my, 20, 20)
        s_rect = pygame.Rect(mx + 24, my, 20, 20)

        pygame.draw.rect(surface, m_col, m_rect, border_radius=3)
        pygame.draw.rect(
            surface, current_palette["input_border"], m_rect, 1, border_radius=3
        )
        ts_m = FONT_SMALL.render("M", True, (255, 255, 255))
        surface.blit(ts_m, ts_m.get_rect(center=m_rect.center))

        pygame.draw.rect(surface, s_col, s_rect, border_radius=3)
        pygame.draw.rect(
            surface, current_palette["input_border"], s_rect, 1, border_radius=3
        )
        ts_s = FONT_SMALL.render("S", True, (255, 255, 255))
        surface.blit(ts_s, ts_s.get_rect(center=s_rect.center))

        if stype and not stype.startswith("multi"):
            sx, sy = cx - 60, cy + 75

            col_track = current_palette["slider_track"]
            col_fill = current_palette["slider_fill"]
            col_knob = current_palette["slider_knob"]

            out_track = darken_color(col_track, 0.4)
            out_knob = darken_color(col_knob, 0.4)

            pygame.draw.rect(surface, col_track, (sx, sy, 120, 10))
            pygame.draw.rect(surface, col_fill, (sx, sy, 80, 10))
            pygame.draw.rect(surface, out_track, (sx, sy, 120, 10), 2)

            kx, ky = sx + 80, sy + 5
            pygame.draw.circle(surface, col_knob, (kx, ky), 7)
            pygame.draw.circle(surface, out_knob, (kx, ky), 7, 2)

    exp_rect = pygame.Rect(APP_W - 160, APP_H - 60, 140, 40)
    draw_action_button(surface, "Export WAV", exp_rect, current_palette["accent"])

    hud_text = "BPM: 128.0 | KEY: F# Minor"
    hud_surf_out = FONT_LARGE_APP.render(hud_text, True, current_palette["text_dark"])
    hud_surf = FONT_LARGE_APP.render(hud_text, True, current_palette["text_main"])

    hud_x, hud_y = 20, APP_H - 50
    offsets = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
    for dx, dy in offsets:
        surface.blit(hud_surf_out, (hud_x + dx, hud_y + dy))
    surface.blit(hud_surf, (hud_x, hud_y))

    overlay_s = pygame.Surface((APP_W, APP_H), pygame.SRCALPHA)
    overlay_s.fill(current_palette["overlay"])
    surface.blit(overlay_s, (0, 520))

    panel_rect_l = pygame.Rect(40, 540, 360, 240)
    pygame.draw.rect(surface, current_palette["panel_bg"], panel_rect_l)
    pygame.draw.rect(surface, current_palette["input_border"], panel_rect_l, 2)

    draw_dynamic_text(
        surface,
        "Input Box Test",
        FONT_LARGE_APP,
        panel_rect_l.centerx,
        570,
        300,
        current_palette["text_main"],
    )

    in_rect = pygame.Rect(panel_rect_l.x + 30, 600, 300, 35)
    pygame.draw.rect(surface, current_palette["input_bg"], in_rect)
    pygame.draw.rect(surface, current_palette["input_active"], in_rect, 2)
    in_txt = FONT_MEDIUM_APP.render("input lmao", True, current_palette["text_main"])
    surface.blit(in_txt, (in_rect.x + 10, in_rect.y + 8))

    btn_w, btn_h = 100, 40
    c_rect = pygame.Rect(panel_rect_l.centerx - btn_w - 10, 670, btn_w, btn_h)
    x_rect = pygame.Rect(panel_rect_l.centerx + 10, 670, btn_w, btn_h)

    draw_action_button(surface, "CONFIRM", c_rect, current_palette["btn_confirm"])
    draw_action_button(surface, "CANCEL", x_rect, current_palette["btn_cancel"])

    panel_rect_r = pygame.Rect(420, 540, 360, 240)
    pygame.draw.rect(surface, current_palette["popup_bg"], panel_rect_r)
    pygame.draw.rect(surface, current_palette["popup_border"], panel_rect_r, 3)

    draw_dynamic_text(
        surface,
        "Dropdown Test",
        FONT_LARGE_APP,
        panel_rect_r.centerx,
        570,
        300,
        current_palette["text_main"],
    )

    dd_rect = pygame.Rect(panel_rect_r.x + 30, 600, 300, 35)
    pygame.draw.rect(surface, current_palette["input_bg"], dd_rect)
    pygame.draw.rect(surface, current_palette["scrollbar"], dd_rect, 2)
    dd_txt = FONT_MEDIUM_APP.render("Select...", True, current_palette["text_main"])
    surface.blit(dd_txt, (dd_rect.x + 10, dd_rect.y + 8))

    list_h = 110
    list_rect_d = pygame.Rect(dd_rect.x, dd_rect.bottom, dd_rect.width, list_h)
    pygame.draw.rect(surface, current_palette["input_bg"], list_rect_d)
    pygame.draw.rect(surface, current_palette["scrollbar"], list_rect_d, 2)

    items = ["1", "2", "Oatmeal"]
    for i, item in enumerate(items):
        iy = list_rect_d.y + (i * 35)
        if iy + 35 > list_rect_d.bottom:
            break
        i_rect = pygame.Rect(list_rect_d.x, iy, list_rect_d.width - 15, 35)
        if i == 1:
            pygame.draw.rect(surface, current_palette["accent"], i_rect)
            pygame.draw.rect(surface, current_palette["scrollbar"], i_rect, 1)
        it_txt = FONT_MEDIUM_APP.render(item, True, current_palette["text_main"])
        surface.blit(it_txt, (i_rect.x + 10, i_rect.y + 8))

    sb_bg = pygame.Rect(list_rect_d.right - 15, list_rect_d.y, 15, list_h)
    sb_th = pygame.Rect(list_rect_d.right - 13, list_rect_d.y + 20, 11, 40)
    pygame.draw.rect(surface, current_palette["input_bg"], sb_bg)
    pygame.draw.rect(surface, current_palette["scrollbar"], sb_th, border_radius=4)


class SliderRGB:
    def __init__(self, x, y, w, h, label, color_comp_index):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.index = color_comp_index
        self.dragging = False

    def draw(self, surf, current_rgb):
        if self.index >= len(current_rgb):
            return
        val = current_rgb[self.index]
        lbl = FONT_SMALL.render(f"{self.label}: {val}", True, (200, 200, 200))
        surf.blit(lbl, (self.rect.x, self.rect.y - 18))
        pygame.draw.rect(surf, (60, 60, 60), self.rect, border_radius=4)

        fill_w = int((val / 255) * self.rect.width)
        fill_col = [50, 50, 50]
        if self.index < 3:
            fill_col[self.index] = 200
        else:
            fill_col = [150, 150, 150]

        pygame.draw.rect(
            surf,
            fill_col,
            (self.rect.x, self.rect.y, fill_w, self.rect.height),
            border_radius=4,
        )
        kx = self.rect.x + fill_w
        pygame.draw.circle(surf, (255, 255, 255), (kx, self.rect.centery), 8)

    def handle_event(self, event, current_rgb):
        updated = False
        if self.index >= len(current_rgb):
            return current_rgb, False
        val = list(current_rgb)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos) or (
                event.pos[0] >= self.rect.x
                and event.pos[0] <= self.rect.right
                and abs(event.pos[1] - self.rect.centery) < 15
            ):
                self.dragging = True
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        if self.dragging:
            mx, _ = pygame.mouse.get_pos()
            rel = mx - self.rect.x
            norm = max(0, min(1, rel / self.rect.width))
            val[self.index] = int(norm * 255)
            updated = True
        return tuple(val), updated


list_scroll_y = 0
list_item_h = 30
list_rect = pygame.Rect(APP_W + 20, 100, EDITOR_W - 40, 400)

sliders = [
    SliderRGB(APP_W + 20, 550, 250, 15, "Red", 0),
    SliderRGB(APP_W + 20, 600, 250, 15, "Green", 1),
    SliderRGB(APP_W + 20, 650, 250, 15, "Blue", 2),
    SliderRGB(APP_W + 20, 700, 250, 15, "Alpha", 3),
]

text_input_active = False

clock = pygame.time.Clock()
running = True

while running:
    screen.fill((20, 20, 20))

    dummy_surf = pygame.Surface((APP_W, APP_H))
    draw_dummy_app(dummy_surf)
    screen.blit(dummy_surf, (0, 0))

    panel_x = APP_W
    title = FONT_TITLE.render("Theme Editor", True, (255, 255, 255))
    screen.blit(title, (panel_x + 20, 20))
    sub = FONT_SMALL.render("Select a color to edit:", True, (150, 150, 150))
    screen.blit(sub, (panel_x + 20, 60))

    pygame.draw.rect(screen, (30, 30, 30), list_rect)
    pygame.draw.rect(screen, (100, 100, 100), list_rect, 1)

    old_clip = screen.get_clip()
    screen.set_clip(list_rect)

    keys = list(current_palette.keys())
    mx, my = pygame.mouse.get_pos()
    total_h = len(keys) * list_item_h
    start_y = list_rect.y - list_scroll_y

    for i, key in enumerate(keys):
        y_pos = start_y + i * list_item_h
        item_r = pygame.Rect(list_rect.x, y_pos, list_rect.width, list_item_h)
        is_selected = key == selected_key
        bg_col = (60, 60, 80) if is_selected else (30, 30, 30)

        if item_r.collidepoint(mx, my) and list_rect.collidepoint(mx, my):
            bg_col = (50, 50, 50)

        pygame.draw.rect(screen, bg_col, item_r)

        swatch_col = current_palette[key]
        if len(swatch_col) == 4:
            swatch_col = swatch_col[:3]
        pygame.draw.rect(screen, swatch_col, (item_r.x + 10, item_r.y + 5, 20, 20))
        pygame.draw.rect(
            screen, (200, 200, 200), (item_r.x + 10, item_r.y + 5, 20, 20), 1
        )

        txt = FONT_SMALL.render(key, True, (230, 230, 230))
        screen.blit(txt, (item_r.x + 40, item_r.y + 7))
        pygame.draw.line(
            screen,
            (40, 40, 40),
            (item_r.x, item_r.bottom - 1),
            (item_r.right, item_r.bottom - 1),
        )

    screen.set_clip(old_clip)

    current_col = list(current_palette[selected_key])
    for slider in sliders:
        slider.draw(screen, current_col)

    prev_rect = pygame.Rect(APP_W + 290, 550, 80, 80)
    pygame.draw.rect(screen, current_col[:3], prev_rect)
    pygame.draw.rect(screen, (255, 255, 255), prev_rect, 2)
    lbl_prev = FONT_SMALL.render("Preview", True, (150, 150, 150))
    screen.blit(lbl_prev, (prev_rect.x, prev_rect.y - 20))

    save_y = 740
    lbl_name = FONT_SMALL.render("Theme Name:", True, (200, 200, 200))
    screen.blit(lbl_name, (APP_W + 20, save_y))

    input_rect = pygame.Rect(APP_W + 20, save_y + 20, 200, 30)
    col_input = (60, 60, 60) if text_input_active else (40, 40, 40)
    pygame.draw.rect(screen, col_input, input_rect)
    pygame.draw.rect(screen, (100, 100, 100), input_rect, 1)

    txt_surf = FONT_MAIN.render(theme_name_input, True, (255, 255, 255))
    screen.blit(txt_surf, (input_rect.x + 5, input_rect.y + 5))

    btn_save_rect = pygame.Rect(APP_W + 240, save_y + 20, 100, 30)
    if btn_save_rect.collidepoint(mx, my):
        pygame.draw.rect(screen, (70, 180, 100), btn_save_rect)
    else:
        pygame.draw.rect(screen, (50, 160, 80), btn_save_rect)
    draw_text_centered_simple(
        screen, "SAVE JSON", FONT_SMALL, (255, 255, 255), btn_save_rect
    )

    if save_message_timer > 0:
        msg_surf = FONT_SMALL.render(save_message, True, (100, 255, 100))
        screen.blit(msg_surf, (APP_W + 20, save_y + 60))
        save_message_timer -= 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        for slider in sliders:
            new_val_t, updated = slider.handle_event(event, current_col)
            if updated:
                current_palette[selected_key] = new_val_t

        if event.type == pygame.MOUSEWHEEL:
            if list_rect.collidepoint(mx, my):
                list_scroll_y -= event.y * 20
                max_scroll = max(0, total_h - list_rect.height)
                list_scroll_y = max(0, min(list_scroll_y, max_scroll))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if list_rect.collidepoint(mx, my):
                rel_y = (my - list_rect.y) + list_scroll_y
                idx = int(rel_y // list_item_h)
                if 0 <= idx < len(keys):
                    selected_key = keys[idx]
                    text_input_active = False
            elif input_rect.collidepoint(mx, my):
                text_input_active = True
            elif btn_save_rect.collidepoint(mx, my):
                fname = theme_name_input.strip()
                if fname:
                    if not fname.endswith(".json"):
                        fname += ".json"
                    path = os.path.join("themes", fname)
                    with open(path, "w") as f:
                        json.dump(current_palette, f, indent=4)
                    save_message = f"Saved to themes/{fname}"
                    save_message_timer = 180
                text_input_active = False
            else:
                text_input_active = False

        if event.type == pygame.KEYDOWN and text_input_active:
            if event.key == pygame.K_BACKSPACE:
                theme_name_input = theme_name_input[:-1]
            elif event.key == pygame.K_RETURN:
                text_input_active = False
            else:
                if len(theme_name_input) < 20 and (
                    event.unicode.isalnum() or event.unicode in "_-"
                ):
                    theme_name_input += event.unicode

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
