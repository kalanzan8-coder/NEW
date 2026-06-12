#!/usr/bin/env python3
"""
15s promo video for a digital product agency.

Storyboard
  0.0 - 4.6s   3D floating phone on black, Stripe payment notifications pop in
  4.6 - 5.3s   screen slides to a pricing page, camera zooms in
  5.3 - 8.8s   $99 vs $297 plans, touch cursor taps $297, payment confirmed
  8.8 - 9.5s   camera pulls back, screen slides to lock screen
  9.5 - 12.4s  rapid Stripe notifications + revenue counter ticking up
 12.4 - 15.0s  phone fades, end text card

Output: 1080x1920 (9:16) @ 30fps, H.264 mp4.
Edit the strings in CONFIG below to customize the copy.
"""

import math
import os
import random
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ----------------------------------------------------------------- CONFIG ---
AGENCY_NAME = "YOURAGENCY"
END_LINE_1 = "Build. Launch."
END_LINE_2 = "Get paid."
END_TAGLINE = "Digital products that sell."

W, H = 1080, 1920
FPS = 30
DUR = 15.0
N_FRAMES = int(DUR * FPS)

HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(HERE, "frames")
OUT_MP4 = os.path.join(HERE, "agency_promo.mp4")
FONT_DIR = os.path.join(HERE, "assets")

PURPLE = (99, 91, 255)        # stripe-ish #635BFF
PURPLE_LT = (139, 133, 255)
GREEN = (34, 197, 94)
BG = (5, 5, 8)

# phone geometry (its own canvas, before 3D projection)
SCW, SCH = 700, 1520          # screen content size
BEZ = 16                      # bezel
PW, PH = SCW + 2 * BEZ, SCH + 2 * BEZ

# ------------------------------------------------------------------ fonts ---


def F(name, size):
    key = (name, size)
    if key not in F.cache:
        path = os.path.join(FONT_DIR, f"Poppins-{name}.ttf")
        if not os.path.exists(path):
            path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        F.cache[key] = ImageFont.truetype(path, size)
    return F.cache[key]


F.cache = {}

# ---------------------------------------------------------------- easings ---


def clamp01(x):
    return max(0.0, min(1.0, x))


def ease_out(u):
    return 1 - (1 - u) ** 3


def ease_io(u):
    return u * u * (3 - 2 * u)


def spring(u):
    if u <= 0:
        return 0.0
    s = 1 - math.exp(-6 * u) * math.cos(12 * u)
    return 1 + (s - 1) * 0.45


def ez(t0, t1, t, fn=ease_out):
    if t1 == t0:
        return 1.0 if t >= t1 else 0.0
    return fn(clamp01((t - t0) / (t1 - t0)))


def lerp(a, b, u):
    return a + (b - a) * u

# ------------------------------------------------------------ small utils ---


def grad_v(w, h, c1, c2):
    """vertical linear gradient image"""
    col = np.linspace(0, 1, h)[:, None]
    arr = np.zeros((h, w, 3), np.uint8)
    for i in range(3):
        arr[:, :, i] = (c1[i] + (c2[i] - c1[i]) * col).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def text_w(draw, txt, font):
    b = draw.textbbox((0, 0), txt, font=font)
    return b[2] - b[0]


def spaced_text(draw, xy, txt, font, fill, spacing, anchor_center=False):
    """letterspaced caps text"""
    widths = [text_w(draw, c, font) for c in txt]
    total = sum(widths) + spacing * (len(txt) - 1)
    x, y = xy
    if anchor_center:
        x -= total / 2
    for c, cw in zip(txt, widths):
        draw.text((x, y), c, font=font, fill=fill)
        x += cw + spacing

# ------------------------------------------------- notification card (UI) ---


CARD_W, CARD_H, CARD_GAP = SCW - 56, 148, 16


def notif_card(body):
    key = body
    if key not in notif_card.cache:
        img = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, CARD_W - 1, CARD_H - 1], radius=34,
                            fill=(30, 30, 38, 242), outline=(62, 62, 74, 255), width=2)
        # stripe app icon
        d.rounded_rectangle([22, 32, 22 + 84, 32 + 84], radius=22, fill=PURPLE)
        d.text((22 + 42, 32 + 40), "S", font=F("Bold", 54), fill="white", anchor="mm")
        d.text((128, 30), "Stripe", font=F("SemiBold", 30), fill=(245, 245, 250))
        d.text((CARD_W - 24, 36), "now", font=F("Regular", 24),
               fill=(150, 150, 160), anchor="ra")
        d.text((128, 72), body, font=F("Regular", 27), fill=(190, 190, 200))
        notif_card.cache[key] = img
    return notif_card.cache[key]


notif_card.cache = {}


def status_bar(d):
    d.text((54, 26), "9:41", font=F("SemiBold", 30), fill="white")
    # battery
    d.rounded_rectangle([SCW - 96, 34, SCW - 46, 58], radius=7,
                        outline=(220, 220, 230), width=3)
    d.rounded_rectangle([SCW - 92, 38, SCW - 58, 54], radius=4, fill=(220, 220, 230))
    d.rounded_rectangle([SCW - 43, 41, SCW - 39, 51], radius=2, fill=(220, 220, 230))
    # signal bars
    for i in range(4):
        bh = 10 + i * 7
        d.rounded_rectangle([SCW - 180 + i * 14, 58 - bh, SCW - 180 + i * 14 + 9, 58],
                            radius=3, fill=(220, 220, 230))


def dynamic_island(d):
    d.rounded_rectangle([SCW / 2 - 110, 18, SCW / 2 + 110, 18 + 62],
                        radius=31, fill=(0, 0, 0, 255), outline=(28, 28, 34), width=2)

# -------------------------------------------------------- lock screen base ---


def lock_base(show_clock=True):
    key = show_clock
    if key not in lock_base.cache:
        img = grad_v(SCW, SCH, (16, 14, 26), (6, 6, 10)).convert("RGBA")
        d = ImageDraw.Draw(img)
        dynamic_island(d)
        status_bar(d)
        if show_clock:
            d.text((SCW / 2, 188), "Thursday, June 12", font=F("Medium", 30),
                   fill=(190, 188, 205), anchor="mm")
            d.text((SCW / 2, 300), "9:41", font=F("Bold", 150),
                   fill=(240, 240, 248), anchor="mm")
        lock_base.cache[key] = img
    return lock_base.cache[key].copy()


lock_base.cache = {}


def notif_stack(screen, t, events, top_y):
    """events: list of (spawn_time, body). newest stacks on top."""
    live = [(s, b) for s, b in events if t >= s]
    live.sort(key=lambda e: -e[0])               # newest first
    for idx, (s, body) in enumerate(live):
        # push-down offset from newer cards above
        y = top_y
        for s2, _ in live[:idx]:
            y += (CARD_H + CARD_GAP) * ez(s2, s2 + 0.4, t)
        u = clamp01((t - s) / 0.55)
        a = ez(s, s + 0.3, t)
        sc = spring(u)
        card = notif_card(body)
        cw, ch = int(CARD_W * sc), int(CARD_H * sc)
        if cw < 2 or ch < 2:
            continue
        c = card.resize((cw, ch), Image.Resampling.BILINEAR)
        if a < 1:
            alpha = c.getchannel("A").point(lambda p: int(p * a))
            c.putalpha(alpha)
        slide = (1 - ease_out(u)) * -80
        screen.alpha_composite(
            c, (int(SCW / 2 - cw / 2), int(y + slide + (CARD_H - ch) / 2)))

# ------------------------------------------------------------- scene A / C ---


EVENTS_A = [
    (1.00, "You received a payment of $129.00"),
    (2.05, "You received a payment of $297.00"),
    (3.15, "You received a payment of $89.00"),
]

EVENTS_C = [(9.85 + i * 0.42, "You received a payment of $297.00") for i in range(6)]


def screen_lock_a(t):
    img = lock_base(True)
    notif_stack(img, t, EVENTS_A, 430)
    return img


def screen_lock_c(t):
    img = lock_base(True)
    # revenue counter card
    arrived = [s for s, _ in EVENTS_C if t >= s]
    total = 0.0
    for s in arrived:
        total += 297 * ez(s, s + 0.30, t)
    pulse = 1.0
    if arrived:
        pulse = 1 + 0.06 * math.exp(-(t - arrived[-1]) * 6)
    d = ImageDraw.Draw(img)
    cy = 470
    d.rounded_rectangle([60, cy, SCW - 60, cy + 130], radius=30,
                        fill=(24, 22, 40, 235), outline=(99, 91, 255, 200), width=2)
    d.text((SCW / 2, cy + 34), "TODAY'S REVENUE", font=F("Medium", 22),
           fill=(160, 156, 200), anchor="mm")
    fnt = F("Bold", int(52 * pulse))
    d.text((SCW / 2, cy + 86), f"${total:,.0f}", font=fnt,
           fill=(245, 245, 252), anchor="mm")
    notif_stack(img, t, EVENTS_C, cy + 170)
    return img

# ---------------------------------------------------------- pricing screen ---


PRO_BOX = (50, 730, SCW - 50, 730 + 470)        # pro card rect
STARTER_BOX = (50, 330, SCW - 50, 330 + 360)
T_CLICK = 7.4


def pricing_base():
    if pricing_base.img is None:
        img = grad_v(SCW, SCH, (14, 13, 22), (7, 7, 11)).convert("RGBA")
        d = ImageDraw.Draw(img)
        dynamic_island(d)
        status_bar(d)
        d.text((SCW / 2, 170), "Choose your plan", font=F("SemiBold", 46),
               fill=(242, 242, 248), anchor="mm")
        d.text((SCW / 2, 228), "One-time payment. Lifetime access.",
               font=F("Regular", 27), fill=(150, 150, 162), anchor="mm")

        # starter card
        x0, y0, x1, y1 = STARTER_BOX
        d.rounded_rectangle([x0, y0, x1, y1], radius=34, fill=(22, 22, 30, 255),
                            outline=(58, 58, 70), width=2)
        d.text((x0 + 40, y0 + 36), "Starter", font=F("SemiBold", 32),
               fill=(210, 210, 220))
        d.text((x0 + 40, y0 + 84), "$99", font=F("Bold", 76), fill=(235, 235, 242))
        for i, feat in enumerate(["Landing page", "Basic copywriting", "1 revision"]):
            fy = y0 + 210 + i * 46
            d.ellipse([x0 + 42, fy + 8, x0 + 58, fy + 24], outline=(120, 120, 135),
                      width=3)
            d.text((x0 + 74, fy), feat, font=F("Regular", 26), fill=(165, 165, 178))
        # radio
        d.ellipse([x1 - 80, y0 + 38, x1 - 40, y0 + 78], outline=(110, 110, 125),
                  width=3)

        pricing_base.img = img
    return pricing_base.img.copy()


pricing_base.img = None


def draw_check(d, cx, cy, r, prog, width=10, color="white"):
    pts = [(cx - r * 0.52, cy + r * 0.02), (cx - r * 0.12, cy + r * 0.42),
           (cx + r * 0.55, cy - r * 0.38)]
    segs = [(pts[0], pts[1]), (pts[1], pts[2])]
    lens = [math.dist(*s) for s in segs]
    total = sum(lens)
    drawn = total * clamp01(prog)
    for (p0, p1), L in zip(segs, lens):
        if drawn <= 0:
            break
        f = clamp01(drawn / L)
        q = (lerp(p0[0], p1[0], f), lerp(p0[1], p1[1], f))
        d.line([p0, q], fill=color, width=width, joint="curve")
        drawn -= L


def screen_pricing(t):
    img = pricing_base()
    x0, y0, x1, y1 = PRO_BOX
    clicked = t >= T_CLICK
    glow = 0.45 + 0.55 * ez(T_CLICK, T_CLICK + 0.25, t)

    # pro card (drawn on its own layer so it can dip-scale on click)
    dip = 1 - 0.035 * math.exp(-((t - T_CLICK) * 7) ** 2) if t > T_CLICK - 0.4 else 1.0
    layer = Image.new("RGBA", (SCW, SCH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bcol = tuple(int(c * glow + 40 * (1 - glow)) for c in PURPLE)
    d.rounded_rectangle([x0, y0, x1, y1], radius=34, fill=(28, 26, 46, 255),
                        outline=bcol, width=4)
    d.rounded_rectangle([x1 - 250, y0 - 18, x1 - 30, y0 + 22], radius=20, fill=PURPLE)
    d.text((x1 - 140, y0 + 2), "MOST POPULAR", font=F("SemiBold", 20),
           fill="white", anchor="mm")
    d.text((x0 + 40, y0 + 36), "Pro", font=F("SemiBold", 32), fill=(228, 226, 248))
    d.text((x0 + 40, y0 + 84), "$297", font=F("Bold", 84), fill=(250, 250, 255))
    feats = ["Full product build", "Conversion copy",
             "Unlimited revisions", "7-day delivery"]
    for i, feat in enumerate(feats):
        fy = y0 + 226 + i * 50
        d.ellipse([x0 + 42, fy + 6, x0 + 62, fy + 26], fill=PURPLE)
        dd = ImageDraw.Draw(layer)
        draw_check(dd, x0 + 52, fy + 16, 11, 1.0, width=3)
        d.text((x0 + 80, fy), feat, font=F("Regular", 26), fill=(195, 193, 215))
    # radio
    if clicked:
        d.ellipse([x1 - 80, y0 + 38, x1 - 40, y0 + 78], fill=PURPLE)
        draw_check(d, x1 - 60, y0 + 58, 14, ez(T_CLICK, T_CLICK + 0.35, t), width=4)
    else:
        d.ellipse([x1 - 80, y0 + 38, x1 - 40, y0 + 78], outline=PURPLE_LT, width=3)

    if dip != 1.0:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        sw, sh = int(SCW * dip), int(SCH * dip)
        layer = layer.resize((sw, sh), Image.Resampling.BILINEAR)
        pad = Image.new("RGBA", (SCW, SCH), (0, 0, 0, 0))
        pad.alpha_composite(layer, (int(cx - cx * dip), int(cy - cy * dip)))
        layer = pad
    img.alpha_composite(layer)
    d = ImageDraw.Draw(img)

    # CTA button
    by = SCH - 200
    bcol2 = PURPLE if not clicked else (78, 72, 210)
    d.rounded_rectangle([50, by, SCW - 50, by + 104], radius=52, fill=bcol2)
    if t < T_CLICK + 0.45:
        d.text((SCW / 2, by + 52), "Continue", font=F("SemiBold", 36),
               fill="white", anchor="mm")
    elif t < T_CLICK + 1.0:
        dots = "." * (1 + int((t * 4) % 3))
        d.text((SCW / 2, by + 52), "Processing" + dots, font=F("SemiBold", 36),
               fill="white", anchor="mm")
    else:
        d.rounded_rectangle([50, by, SCW - 50, by + 104], radius=52, fill=GREEN)
        d.text((SCW / 2 + 26, by + 52), "Payment confirmed", font=F("SemiBold", 34),
               fill="white", anchor="mm")
        draw_check(d, 116, by + 52, 22, ez(T_CLICK + 1.0, T_CLICK + 1.3, t), width=6)

    # ripple on click
    if T_CLICK <= t < T_CLICK + 0.55:
        u = (t - T_CLICK) / 0.55
        r = 30 + 240 * ease_out(u)
        a = int(140 * (1 - u))
        rip = Image.new("RGBA", (SCW, SCH), (0, 0, 0, 0))
        ImageDraw.Draw(rip).ellipse(
            [tx_click - r, ty_click - r, tx_click + r, ty_click + r],
            outline=(255, 255, 255, a), width=8)
        img.alpha_composite(rip)

    # touch cursor: flies in along a curve, hovers, taps
    if 5.9 <= t < T_CLICK + 0.5:
        u = ez(5.9, 6.9, t, ease_io)
        # bezier from bottom-right to pro card
        p0, p1, p2 = (SCW + 80, SCH - 60), (SCW - 120, SCH - 600), (tx_click, ty_click)
        bx = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u ** 2 * p2[0]
        by2 = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u ** 2 * p2[1]
        press = 1 - 0.25 * math.exp(-((t - T_CLICK) * 9) ** 2)
        r = 34 * press
        fade = 1.0 if t < T_CLICK + 0.2 else 1 - clamp01((t - T_CLICK - 0.2) / 0.3)
        cur = Image.new("RGBA", (SCW, SCH), (0, 0, 0, 0))
        dc = ImageDraw.Draw(cur)
        dc.ellipse([bx - r, by2 - r, bx + r, by2 + r],
                   fill=(255, 255, 255, int(70 * fade)),
                   outline=(255, 255, 255, int(200 * fade)), width=4)
        img.alpha_composite(cur)
    return img


tx_click, ty_click = (PRO_BOX[0] + PRO_BOX[2]) / 2, (PRO_BOX[1] + PRO_BOX[3]) / 2 + 60

# ----------------------------------------------------- screen compositing ---


def screen_at(t):
    """final screen content incl. slide transitions"""
    img = Image.new("RGBA", (SCW, SCH), (0, 0, 0, 255))
    if t < 4.6:
        img.alpha_composite(screen_lock_a(t))
    elif t < 5.3:
        u = ez(4.6, 5.3, t, ease_io)
        img.alpha_composite(screen_lock_a(t), (int(-SCW * u), 0))
        img.alpha_composite(screen_pricing(5.3), (int(SCW * (1 - u)), 0))
    elif t < 8.8:
        img.alpha_composite(screen_pricing(t))
    elif t < 9.5:
        u = ez(8.8, 9.5, t, ease_io)
        img.alpha_composite(screen_pricing(8.8), (int(SCW * u), 0))
        img.alpha_composite(screen_lock_c(t), (int(-SCW * (1 - u)), 0))
    else:
        img.alpha_composite(screen_lock_c(t))
    return img

# -------------------------------------------------------------- 3D phone ----


def phone_image(t):
    img = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, PW - 1, PH - 1], radius=92, fill=(22, 22, 28, 255),
                        outline=(70, 70, 84, 255), width=3)
    scr = screen_at(t)
    mask = Image.new("L", (SCW, SCH), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, SCW - 1, SCH - 1], radius=76,
                                           fill=255)
    img.paste(scr, (BEZ, BEZ), mask)
    # glossy diagonal reflection, drifts with time for a 3D feel
    gl = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    off = int(200 * math.sin(t * 0.5))
    ImageDraw.Draw(gl).polygon(
        [(PW * 0.1 + off, -50), (PW * 0.55 + off, -50),
         (PW * 0.05 + off, PH + 50), (-PW * 0.4 + off, PH + 50)],
        fill=(255, 255, 255, 9))
    img.alpha_composite(gl)
    return img


def phone_params(t):
    """returns yaw, pitch, roll (deg), scale, cx, cy, alpha"""
    bob = 14 * math.sin(t * 1.4)
    if t < 4.6:
        u = t / 4.6
        return (-15 + 7 * math.sin(t * 0.8), 6, -2.5,
                lerp(0.60, 0.64, u), W / 2, H / 2 + bob, 1.0)
    if t < 5.3:
        u = ez(4.6, 5.3, t, ease_io)
        return (lerp(-11, -4, u), lerp(6, 3, u), lerp(-2.5, 0, u),
                lerp(0.64, 0.80, u), W / 2, H / 2 + bob * (1 - u), 1.0)
    if t < 8.8:
        return (-4 + 1.5 * math.sin(t * 0.9), 3, 0, 0.80, W / 2, H / 2, 1.0)
    if t < 9.5:
        u = ez(8.8, 9.5, t, ease_io)
        return (lerp(-4, 12, u), lerp(3, 6, u), lerp(0, 2, u),
                lerp(0.80, 0.62, u), W / 2, H / 2 + bob * u, 1.0)
    if t < 12.4:
        return (12 - 3 * (t - 9.5) / 2.9, 6, 2, 0.62, W / 2, H / 2 + bob, 1.0)
    u = ez(12.4, 13.3, t, ease_io)
    return (12 * (1 - u) + 0, 6, 2 * (1 - u), lerp(0.62, 0.42, u),
            W / 2, H / 2 - 420 * u + bob * (1 - u), 1 - u)


def project(yaw, pitch, roll, scale, cx, cy):
    """project phone plane corners to frame coords"""
    ya, pa, ra = map(math.radians, (yaw, pitch, roll))
    pts = []
    f = 3000.0
    for x, y in [(-PW / 2, -PH / 2), (PW / 2, -PH / 2),
                 (PW / 2, PH / 2), (-PW / 2, PH / 2)]:
        z = 0.0
        # roll (z), pitch (x), yaw (y)
        x, y = x * math.cos(ra) - y * math.sin(ra), x * math.sin(ra) + y * math.cos(ra)
        y, z = y * math.cos(pa) - z * math.sin(pa), y * math.sin(pa) + z * math.cos(pa)
        x, z = x * math.cos(ya) + z * math.sin(ya), -x * math.sin(ya) + z * math.cos(ya)
        k = f / (f + z)
        pts.append((cx + x * k * scale, cy + y * k * scale))
    return pts


def persp_coeffs(src, dst):
    A, B = [], []
    for (xs, ys), (xd, yd) in zip(src, dst):
        A.append([xd, yd, 1, 0, 0, 0, -xs * xd, -xs * yd]); B.append(xs)
        A.append([0, 0, 0, xd, yd, 1, -ys * xd, -ys * yd]); B.append(ys)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def composite_phone(frame, t):
    yaw, pitch, roll, scale, cx, cy, alpha = phone_params(t)
    if alpha <= 0.01:
        return
    quad = project(yaw, pitch, roll, scale, cx, cy)
    xs, ys = [p[0] for p in quad], [p[1] for p in quad]
    pad = 6
    bx0, by0 = int(min(xs)) - pad, int(min(ys)) - pad
    bx1, by1 = int(max(xs)) + pad, int(max(ys)) + pad
    bw, bh = bx1 - bx0, by1 - by0
    SS = 2  # supersample for clean edges
    local = [((x - bx0) * SS, (y - by0) * SS) for x, y in quad]
    src = [(0, 0), (PW, 0), (PW, PH), (0, PH)]
    coeffs = persp_coeffs(src, local)
    ph = phone_image(t)
    warped = ph.transform((bw * SS, bh * SS), Image.Transform.PERSPECTIVE, coeffs,
                          resample=Image.Resampling.BICUBIC)
    warped = warped.resize((bw, bh), Image.Resampling.LANCZOS)

    # soft drop shadow from silhouette (low-res blur, padded so it isn't clipped)
    pp = 26
    sw, shh = bw // 6, bh // 6
    sil = Image.new("L", (sw + 2 * pp, shh + 2 * pp), 0)
    sil.paste(warped.getchannel("A").resize((sw, shh)), (pp, pp))
    sil = sil.filter(ImageFilter.GaussianBlur(8))
    sil = sil.resize(((sw + 2 * pp) * 6, (shh + 2 * pp) * 6))
    sh = Image.new("RGBA", sil.size, (0, 0, 0, 0))
    sh.putalpha(sil.point(lambda p: int(p * 0.55 * alpha)))
    frame.alpha_composite(sh, (bx0 + 18 - pp * 6, by0 + 34 - pp * 6))

    if alpha < 1:
        a = warped.getchannel("A").point(lambda p: int(p * alpha))
        warped.putalpha(a)
    frame.alpha_composite(warped, (bx0, by0))

# ----------------------------------------------------- background & extras ---


def glow_bg(t):
    """low-res ambient glow, upscaled"""
    gw, gh = 135, 240
    g = Image.new("RGB", (gw, gh), BG)
    d = ImageDraw.Draw(g)
    boost = 1.0
    for s, _ in EVENTS_A + EVENTS_C:
        if 0 <= t - s < 0.8:
            boost = max(boost, 1 + 0.5 * (1 - (t - s) / 0.8))
    x1 = gw * (0.30 + 0.10 * math.sin(t * 0.35))
    y1 = gh * (0.30 + 0.06 * math.cos(t * 0.28))
    x2 = gw * (0.72 + 0.08 * math.cos(t * 0.30))
    y2 = gh * (0.74 + 0.05 * math.sin(t * 0.40))
    d.ellipse([x1 - 46, y1 - 46, x1 + 46, y1 + 46],
              fill=tuple(int(c * 0.22 * boost) for c in PURPLE))
    d.ellipse([x2 - 52, y2 - 52, x2 + 52, y2 + 52],
              fill=tuple(int(c * 0.18 * boost) for c in (60, 80, 220)))
    g = g.filter(ImageFilter.GaussianBlur(22))
    return g.resize((W, H), Image.Resampling.BICUBIC).convert("RGBA")


random.seed(7)
PARTICLES = [(random.uniform(0, W), random.uniform(0, H),
              random.uniform(1.5, 4.5), random.uniform(12, 55),
              random.uniform(0.2, 1.0)) for _ in range(46)]


def draw_particles(frame, t):
    d = ImageDraw.Draw(frame)
    for x, y0, r, spd, depth in PARTICLES:
        y = (y0 - spd * t) % (H + 60) - 30
        a = int(60 * depth * (0.6 + 0.4 * math.sin(t * 2 + x)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(180, 175, 255, max(0, a)))


def make_vignette():
    yy, xx = np.mgrid[0:H, 0:W]
    dx = (xx - W / 2) / (W / 2)
    dy = (yy - H / 2) / (H / 2)
    dist = np.sqrt(dx * dx + dy * dy)
    a = np.clip((dist - 0.55) / 0.9, 0, 1) ** 2 * 160
    v = np.zeros((H, W, 4), np.uint8)
    v[:, :, 3] = a.astype(np.uint8)
    return Image.fromarray(v, "RGBA")


VIGNETTE = make_vignette()

# ----------------------------------------------------------- end text card ---


def draw_end_text(frame, t):
    if t < 12.7:
        return
    d = ImageDraw.Draw(frame)
    cy = H / 2 - 140

    def reveal(txt, y, font, fill, t0):
        u = ez(t0, t0 + 0.55, t)
        if u <= 0:
            return
        a = int(255 * u)
        dy = (1 - u) * 60
        if isinstance(fill, tuple):
            fill = fill + (a,)
        else:
            fill = (255, 255, 255, a)
        d.text((W / 2, y + dy), txt, font=font, fill=fill, anchor="mm")

    reveal(END_LINE_1, cy, F("Bold", 110), (245, 245, 250), 12.75)
    reveal(END_LINE_2, cy + 140, F("Bold", 110), PURPLE_LT, 12.95)
    u = ez(13.35, 13.9, t)
    if u > 0:
        a = int(255 * u)
        d.line([(W / 2 - 70, cy + 268), (W / 2 + 70, cy + 268)],
               fill=PURPLE + (a,), width=4)
        spaced_text(d, (W / 2, cy + 308), AGENCY_NAME, F("SemiBold", 40),
                    (235, 235, 242, a), 14, anchor_center=True)
        d.text((W / 2, cy + 388), END_TAGLINE, font=F("Regular", 32),
               fill=(150, 150, 165, a), anchor="mm")

# ------------------------------------------------------------------ frame ---


def render_frame(t):
    frame = glow_bg(t)
    draw_particles(frame, t)
    composite_phone(frame, t)
    draw_end_text(frame, t)
    frame.alpha_composite(VIGNETTE)
    # fade in / out
    fade = min(ez(0.0, 0.5, t), 1 - ez(DUR - 0.45, DUR, t, ease_io))
    if fade < 1:
        black = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - fade))))
        frame.alpha_composite(black)
    return frame.convert("RGB")


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    import time
    t0 = time.time()
    for i in range(N_FRAMES):
        t = i / FPS
        render_frame(t).save(os.path.join(FRAMES_DIR, f"f_{i:04d}.png"))
        if i % 60 == 0:
            print(f"frame {i}/{N_FRAMES}  ({time.time() - t0:.0f}s)", flush=True)
    print(f"rendered {N_FRAMES} frames in {time.time() - t0:.0f}s")

    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([
        ff, "-y", "-framerate", str(FPS),
        "-i", os.path.join(FRAMES_DIR, "f_%04d.png"),
        "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT_MP4,
    ], check=True)
    print("wrote", OUT_MP4)


if __name__ == "__main__":
    main()
