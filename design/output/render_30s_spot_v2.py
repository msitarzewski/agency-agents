"""
Telcoin — 30-Second Commercial: "What 6 Percent Costs"
Version 2 — High-quality motion graphics production.

Improvements over v1:
  - 2× supersampling (renders at 3840×2160, downscales to 1920×1080 via LANCZOS)
  - Numpy radial gradient backgrounds per scene
  - Multi-pass Gaussian bloom on all glowing elements
  - Film grain (numpy random noise) per frame
  - Radial vignette (numpy)
  - Much better visual design — cards, typography, phone mockup
  - Better continent polygon data for world map
  - Layered compositing with proper RGBA throughout

Output: design/output/telcoin-30s-v2.mp4
"""

import os, math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.ndimage import gaussian_filter

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
W, H   = 1920, 1080
SCALE  = 2                     # supersampling factor
RW, RH = W * SCALE, H * SCALE # render resolution: 3840 × 2160
FPS    = 24
DURATION = 30.0
N_FRAMES = int(FPS * DURATION)

OUT_DIR  = os.path.dirname(os.path.abspath(__file__))
OUT_FILE = os.path.join(OUT_DIR, "telcoin-30s-v2.mp4")

FONT_DIR  = "/usr/share/fonts/truetype/liberation"
FONT_REG  = os.path.join(FONT_DIR, "LiberationSans-Regular.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "LiberationSans-Bold.ttf")

# ─── BRAND PALETTE ────────────────────────────────────────────────────────────
BG      = np.array([10, 14, 26],    dtype=np.float32)
BLUE    = np.array([0,  71,  255],  dtype=np.float32)
CYAN    = np.array([0,  212, 255],  dtype=np.float32)
WHITE   = np.array([255,255, 255],  dtype=np.float32)
GRAY    = np.array([176,184, 200],  dtype=np.float32)
GOLD    = np.array([201,162,  39],  dtype=np.float32)
GREEN   = np.array([50, 200, 120],  dtype=np.float32)
RED     = np.array([200, 60,  60],  dtype=np.float32)
BLACK   = np.array([0,   0,   0],   dtype=np.float32)

def rgb(arr):
    return tuple(int(v) for v in arr)

# ─── FONT CACHE ───────────────────────────────────────────────────────────────
_fonts = {}
def font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        # Scale font sizes for render resolution
        _fonts[key] = ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size * SCALE)
    return _fonts[key]

# ─── MATH HELPERS ─────────────────────────────────────────────────────────────
def ease_inout(t):
    t = np.clip(t, 0, 1)
    return np.where(t < 0.5, 2*t*t, 1 - (-2*t+2)**2/2)

def ease_out(t):
    t = np.clip(t, 0, 1)
    return 1 - (1 - t)**3

def ease_in(t):
    t = np.clip(t, 0, 1)
    return t**3

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

def progress(t, start, end):
    """Return [0..1] progress of t between start and end."""
    if end <= start:
        return 1.0 if t >= start else 0.0
    return clamp((t - start) / (end - start))

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


# ─── NUMPY IMAGE OPERATIONS ───────────────────────────────────────────────────

def new_buf():
    """Return a float32 RGBA buffer at render resolution, fully transparent."""
    return np.zeros((RH, RW, 4), dtype=np.float32)

def buf_to_pil(buf):
    """Clamp float32 RGBA buffer and convert to PIL RGBA."""
    return Image.fromarray(np.clip(buf, 0, 255).astype(np.uint8), "RGBA")

def pil_to_buf(img):
    return np.array(img.convert("RGBA"), dtype=np.float32)

def composite_over(dst, src):
    """Porter-Duff 'over' composite: src over dst. Both float32 RGBA [0..255]."""
    sa = src[..., 3:4] / 255.0
    da = dst[..., 3:4] / 255.0
    out_a = sa + da * (1 - sa)
    out_c = np.where(out_a > 0,
                     (src[..., :3] * sa + dst[..., :3] * da * (1 - sa)) / np.maximum(out_a, 1e-6),
                     0)
    result = np.zeros_like(dst)
    result[..., :3] = out_c
    result[..., 3:4] = out_a * 255
    return result

def make_gradient_bg(center_col, edge_col, w=RW, h=RH, cx_frac=0.5, cy_frac=0.4):
    """Radial gradient background. center_col, edge_col: np arrays of shape (3,)."""
    ys = np.linspace(0, 1, h)[:, None]
    xs = np.linspace(0, 1, w)[None, :]
    cx, cy = cx_frac, cy_frac
    r = np.sqrt((xs - cx)**2 / 0.8 + (ys - cy)**2 / 0.6)
    r = np.clip(r, 0, 1)
    r = r ** 0.7  # soften falloff
    buf = np.zeros((h, w, 4), dtype=np.float32)
    for i in range(3):
        buf[..., i] = center_col[i] * (1 - r) + edge_col[i] * r
    buf[..., 3] = 255
    return buf

def add_vignette(buf, strength=0.55):
    """Darken edges with a smooth radial vignette."""
    h, w = buf.shape[:2]
    ys = np.linspace(-1, 1, h)[:, None]
    xs = np.linspace(-1, 1, w)[None, :]
    r = np.sqrt(xs**2 * 0.8 + ys**2)
    mask = np.clip(1.0 - r * strength, 0, 1)[..., None]
    buf = buf.copy()
    buf[..., :3] *= mask
    return buf

def add_grain(buf, strength=6.0, seed=None):
    """Add subtle film grain."""
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, strength, buf.shape[:2])
    buf = buf.copy()
    buf[..., :3] += noise[..., None]
    return buf

def gaussian_glow_layer(draw_fn, color, blur_radius, alpha, w=RW, h=RH):
    """
    Create a glow layer: draw elements via draw_fn onto a temp image,
    apply Gaussian blur, return float32 RGBA buf.
    draw_fn(ImageDraw.Draw) → draws into a temp PIL image.
    color: np array (3,)  blur_radius: pixels at render res
    alpha: overall layer opacity [0..1]
    """
    tmp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    draw_fn(d)
    # Gaussian blur each channel separately
    arr = np.array(tmp, dtype=np.float32)
    blurred = np.zeros_like(arr)
    for c in range(4):
        blurred[..., c] = gaussian_filter(arr[..., c], sigma=blur_radius)
    blurred[..., 3] *= alpha
    return blurred

def draw_text_aa(buf, text, x, y, f, color, alpha=1.0, anchor="mm"):
    """Draw text onto buffer with anti-aliasing via Pillow."""
    tmp = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    r, g, b = int(color[0]), int(color[1]), int(color[2])
    d.text((x, y), text, font=f, fill=(r, g, b, int(255 * alpha)), anchor=anchor)
    buf[:] = composite_over(buf, pil_to_buf(tmp))

def draw_rect_aa(buf, x0, y0, x1, y1, r=0, fill=None, outline=None, olw=2, alpha=1.0):
    tmp = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    fc = (int(fill[0]), int(fill[1]), int(fill[2]), int(255 * alpha)) if fill is not None else None
    oc = (int(outline[0]), int(outline[1]), int(outline[2]), int(255 * alpha)) if outline is not None else None
    d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=fc, outline=oc, width=olw)
    buf[:] = composite_over(buf, pil_to_buf(tmp))

def add_glow(buf, draw_fn, blur_r, glow_col, glow_alpha):
    """Add a glowing version of draw_fn's output onto buf."""
    glow = gaussian_glow_layer(draw_fn, glow_col, blur_r, glow_alpha)
    buf[:] = composite_over(buf, glow)

def finalize_frame(buf):
    """Downsample render buffer → output resolution with grain and vignette."""
    buf = add_vignette(buf)
    # Downsample 2× with LANCZOS
    pil = buf_to_pil(buf)
    pil = pil.resize((W, H), Image.LANCZOS).convert("RGB")
    # Add grain at output resolution
    arr = np.array(pil, dtype=np.float32)
    noise = np.random.normal(0, 5.5, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return arr  # numpy RGB array for moviepy


# ─── COORDINATE HELPERS ───────────────────────────────────────────────────────
def s(v):
    """Scale a value from output coords → render coords."""
    return int(v * SCALE)

def sx(v): return s(v)
def sy(v): return s(v)


# ─── WORLD MAP DATA (simplified polygons, lon/lat) ────────────────────────────
# More accurate continent outlines than v1
CONTINENTS = [
    # North America
    [(-165,72),(-140,70),(-110,72),(-85,68),(-65,50),(-55,47),
     (-64,44),(-70,41),(-75,35),(-80,25),(-85,20),(-83,9),(-77,8),
     (-75,10),(-70,12),(-62,10),(-60,6),(-62,4),(-75,2),(-78,4),
     (-80,8),(-84,10),(-90,16),(-92,18),(-95,18),(-97,22),(-105,22),
     (-117,32),(-120,34),(-122,37),(-124,46),(-128,52),(-135,56),
     (-145,60),(-155,59),(-160,57),(-165,60),(-170,64),(-165,72)],
    # South America
    [(-80,12),(-75,11),(-70,12),(-62,12),(-52,4),(-50,2),(-48,0),
     (-49,-4),(-38,-5),(-35,-9),(-35,-14),(-38,-20),(-40,-22),
     (-43,-23),(-44,-28),(-50,-30),(-52,-32),(-54,-34),(-57,-38),
     (-62,-42),(-65,-46),(-66,-50),(-67,-55),(-68,-56),
     (-70,-55),(-73,-50),(-72,-45),(-70,-40),(-72,-30),(-70,-18),
     (-76,-14),(-78,-8),(-80,-2),(-80,5),(-80,12)],
    # Europe
    [(-10,36),(-6,36),(4,36),(14,38),(22,37),(28,38),(30,42),
     (28,45),(30,48),(26,52),(22,55),(18,57),(15,58),(12,58),
     (8,57),(5,56),(3,53),(2,52),(0,50),(-2,48),(-4,44),
     (-8,42),(-9,39),(-8,36),(-5,36),(-10,36)],
    # Scandinavia (separate polygon)
    [(5,58),(8,57),(10,58),(12,62),(14,66),(16,68),(20,70),(26,70),
     (28,68),(28,65),(26,62),(24,60),(22,58),(18,57),(14,58),(10,58),(5,58)],
    # Africa
    [(-18,16),(-15,12),(-14,10),(-10,5),(-5,5),(-2,4),(4,5),
     (8,4),(10,2),(12,0),(14,-4),(16,-6),(20,-10),(24,-16),
     (28,-22),(30,-26),(32,-30),(30,-34),(26,-34),(22,-32),
     (18,-28),(16,-22),(14,-16),(12,-8),(8,-4),(2,2),(-2,4),
     (-2,8),(0,14),(2,18),(4,22),(8,24),(10,22),(14,22),
     (14,18),(16,14),(12,12),(8,14),(4,15),(0,15),(-4,14),
     (-8,14),(-12,14),(-16,14),(-18,16)],
    # Middle East / Arabian Peninsula
    [(36,38),(42,38),(44,36),(48,30),(52,26),(56,22),(58,20),
     (56,16),(52,12),(44,12),(38,12),(36,16),(36,20),(36,24),(36,28),(36,38)],
    # Asia (main body)
    [(26,70),(40,72),(60,70),(80,68),(100,68),(120,68),(140,68),
     (145,58),(145,50),(140,46),(135,42),(130,36),(126,32),(122,28),
     (118,22),(112,18),(105,12),(100,8),(100,2),(104,1),(108,2),
     (112,4),(118,4),(122,6),(125,8),(126,22),(130,32),(134,36),
     (136,38),(132,42),(130,46),(134,50),(136,52),(134,56),(128,60),
     (120,62),(110,66),(100,68),(90,68),(80,68),(70,65),(60,62),
     (50,60),(40,56),(35,50),(30,48),(26,44),(26,40),(28,36),
     (34,36),(36,38),(36,36),(36,32),(38,28),(42,28),(44,28),
     (48,26),(50,26),(52,24),(52,20),(56,16),(52,12),(44,12),
     (36,16),(34,18),(32,22),(30,24),(26,40),(26,70)],
    # India
    [(68,36),(72,34),(76,30),(78,24),(80,16),(80,10),(78,8),(76,8),
     (74,12),(72,16),(68,20),(66,24),(64,28),(66,32),(68,36)],
    # Southeast Asia + Malay Peninsula
    [(100,20),(102,18),(104,14),(102,8),(104,2),(104,0),(106,-2),(106,0),
     (108,2),(110,4),(112,6),(114,4),(116,6),(118,6),(120,4),(118,0),
     (116,-2),(112,-4),(108,-6),(106,-8),(104,-8),(102,-4),(100,-2),
     (100,4),(100,8),(100,12),(100,16),(100,20)],
    # Japan
    [(130,32),(132,34),(134,36),(136,38),(138,38),(140,40),(142,42),
     (144,44),(144,42),(142,40),(140,38),(138,36),(136,34),(134,32),(130,32)],
    # Australia
    [(114,-22),(118,-20),(122,-18),(126,-16),(130,-12),(136,-12),
     (140,-14),(144,-14),(148,-18),(152,-22),(152,-28),(150,-32),
     (148,-36),(146,-38),(142,-38),(138,-36),(136,-34),(132,-34),
     (128,-32),(124,-28),(118,-26),(116,-24),(114,-22)],
    # Greenland
    [(-44,80),(-26,74),(-18,70),(-20,66),(-24,62),(-38,60),(-44,60),
     (-52,64),(-56,68),(-54,74),(-48,78),(-44,80)],
]

# Remittance cities: (label, lon, lat)
CITIES = [
    ("Manila",         121.0, 14.6),
    ("Dhaka",           90.4, 23.7),
    ("Nairobi",         36.8, -1.3),
    ("Karachi",         67.0, 24.9),
    ("Jakarta",        106.8, -6.2),
    ("Guatemala City", -90.5, 14.6),
]
HUB_LON, HUB_LAT = -100.0, 38.0   # US hub

def map_coords(lon, lat, mx, my, mw, mh):
    x = mx + (lon + 180) / 360 * mw
    y = my + (90 - lat) / 180 * mh
    return int(x), int(y)


# ─── SCENE 1: HOOK (0-3s) ────────────────────────────────────────────────────

def scene1(t):
    fade_in = ease_out(progress(t, 0, 0.9))

    # Background: near-black center, darker edges (establishing darkness)
    center = BG * 0.6 + BLACK * 0.4
    buf = make_gradient_bg(center, BLACK * 0.5)
    buf[..., 3] = 255 * fade_in

    # Time stamp — styled like a phone clock
    time_a = ease_out(progress(t, 0.2, 0.9))
    if time_a > 0:
        draw_text_aa(buf, "17:47", sx(960), sy(310),
                     font(96, bold=True), WHITE, alpha=time_a * 0.25, anchor="mm")
        draw_text_aa(buf, "END  OF  SHIFT", sx(960), sy(400),
                     font(18), GRAY, alpha=time_a * 0.4, anchor="mm")

    # Fee card — traditional remittance app
    card_a = ease_out(progress(t, 1.0, 1.8))
    if card_a > 0:
        cx, cy = sx(960), sy(580)
        cw, ch = sx(520), sy(160)

        # Card shadow
        shadow = pil_to_buf(Image.new("RGBA", (RW, RH), (0,0,0,0)))
        draw_rect_aa(shadow, cx - cw//2 + 8, cy - ch//2 + 8,
                     cx + cw//2 + 8, cy + ch//2 + 8,
                     r=s(16), fill=BLACK, alpha=card_a * 0.5)
        buf = composite_over(buf, shadow)

        # Card body
        card_col = lerp(BG, np.array([22, 14, 14]), 0.7)
        draw_rect_aa(buf, cx - cw//2, cy - ch//2, cx + cw//2, cy + ch//2,
                     r=s(16), fill=card_col, outline=lerp(BLACK, RED, 0.3),
                     olw=s(1), alpha=card_a)

        # App label
        draw_text_aa(buf, "Traditional Transfer", sx(960), sy(536),
                     font(16), GRAY, alpha=card_a * 0.7, anchor="mm")

        # Amount
        draw_text_aa(buf, "$200.00  →  ?", sx(960), sy(570),
                     font(22, bold=True), WHITE, alpha=card_a, anchor="mm")

        # Fee — RED, large
        draw_text_aa(buf, "Fee: $12.50", sx(960), sy(612),
                     font(26, bold=True), RED, alpha=card_a, anchor="mm")

        # Glow on fee text
        def draw_fee(d):
            d.text((sx(960), sy(612)), "Fee: $12.50",
                   font=font(26, bold=True), fill=rgb(RED) + (180,), anchor="mm")
        add_glow(buf, draw_fee, blur_r=s(12), glow_col=RED, glow_alpha=card_a * 0.4)

    # Fade out
    fade_out = ease_in(progress(t, 2.5, 3.0))
    if fade_out > 0:
        fade_layer = make_gradient_bg(BLACK, BLACK)
        fade_layer[..., 3] = 255 * fade_out
        buf = composite_over(buf, fade_layer)

    return buf


# ─── SCENE 2: PROBLEM (3-10s) ────────────────────────────────────────────────

def scene2(t):
    # t: 0-7s within scene
    fade_in = ease_out(progress(t, 0, 0.4))

    # Background: dark navy with warm reddish tint (problem palette)
    center = BG + np.array([8, 2, 0])
    buf = make_gradient_bg(center, BLACK * 0.6)
    buf[..., 3] = 255 * fade_in

    # ── Big percentage ──
    pct_progress = ease_out(progress(t, 0, 0.9))
    pct_val = lerp(0.0, 6.3, pct_progress)
    pct_text = f"{pct_val:.1f}%"

    if pct_progress > 0:
        # Main number — large white
        draw_text_aa(buf, pct_text, sx(960), sy(350),
                     font(190, bold=True), WHITE, alpha=pct_progress, anchor="mm")

        # Glow on number
        def draw_pct(d):
            d.text((sx(960), sy(350)), pct_text, font=font(190, bold=True),
                   fill=(255, 255, 255, 60), anchor="mm")
        add_glow(buf, draw_pct, blur_r=s(40), glow_col=WHITE, glow_alpha=pct_progress * 0.15)

        # Animated underline
        ul_p = ease_out(progress(t, 0.5, 1.1))
        if ul_p > 0:
            ul_w = int(sx(340) * ul_p)
            ul_x = sx(960) - ul_w // 2
            ul_y = sy(470)
            tmp = Image.new("RGBA", (RW, RH), (0,0,0,0))
            d = ImageDraw.Draw(tmp)
            d.line([(ul_x, ul_y), (ul_x + ul_w, ul_y)],
                   fill=rgb(CYAN) + (255,), width=s(3))
            buf = composite_over(buf, pil_to_buf(tmp))
            # Glow on line
            def draw_ul(d2):
                d2.line([(ul_x, ul_y), (ul_x + ul_w, ul_y)],
                        fill=rgb(CYAN) + (200,), width=s(3))
            add_glow(buf, draw_ul, blur_r=s(8), glow_col=CYAN, glow_alpha=ul_p * 0.6)

    # Source text
    src_a = ease_out(progress(t, 0.8, 1.4))
    if src_a > 0:
        draw_text_aa(buf, "WORLD BANK GLOBAL AVERAGE — REMITTANCE TRANSFER FEE",
                     sx(960), sy(510), font(16), GRAY, alpha=src_a * 0.65, anchor="mm")

    # ── $19 card ── appears at t=2.5
    card_a = ease_out(progress(t, 2.5, 3.2))
    if card_a > 0:
        cx, cy = sx(960), sy(700)
        cw, ch = sx(760), sy(150)

        # Card shadow
        shad = pil_to_buf(Image.new("RGBA", (RW, RH), (0,0,0,0)))
        draw_rect_aa(shad, cx - cw//2 + 10, cy - ch//2 + 10,
                     cx + cw//2 + 10, cy + ch//2 + 10,
                     r=s(20), fill=BLACK, alpha=card_a * 0.6)
        buf = composite_over(buf, shad)

        # Card body — dark red tint
        card_col = lerp(BG, np.array([30, 10, 10]), 0.7)
        border_col = lerp(BLACK, RED * 0.6, 0.4)
        draw_rect_aa(buf, cx - cw//2, cy - ch//2, cx + cw//2, cy + ch//2,
                     r=s(20), fill=card_col, outline=border_col, olw=s(1), alpha=card_a)

        # Border glow
        def draw_border(d):
            d.rounded_rectangle([cx - cw//2, cy - ch//2, cx + cw//2, cy + ch//2],
                                 radius=s(20), outline=rgb(RED) + (120,), width=s(2))
        add_glow(buf, draw_border, blur_r=s(18), glow_col=RED, glow_alpha=card_a * 0.35)

        # Dollar amount counter
        dollar_p = ease_out(progress(t, 2.5, 3.8))
        dollar_val = lerp(0, 19, dollar_p)
        dollar_text = f"${dollar_val:.0f}"
        draw_text_aa(buf, dollar_text, cx - sx(200), cy,
                     font(80, bold=True), RED, alpha=card_a, anchor="mm")

        # Glow on dollar
        def draw_dollar(d):
            d.text((cx - sx(200), cy), dollar_text, font=font(80, bold=True),
                   fill=rgb(RED) + (150,), anchor="mm")
        add_glow(buf, draw_dollar, blur_r=s(25), glow_col=RED, glow_alpha=card_a * 0.4)

        # Supporting text
        draw_text_aa(buf, "lost on every $300 sent", cx + sx(80), cy - sy(20),
                     font(22, bold=True), WHITE, alpha=card_a, anchor="mm")
        draw_text_aa(buf, "every single month — for years", cx + sx(80), cy + sy(22),
                     font(18), GRAY, alpha=card_a * 0.75, anchor="mm")

    # VO cue text — t > 5
    cue_a = ease_out(progress(t, 5.0, 5.8))
    if cue_a > 0:
        draw_text_aa(buf, "That's groceries. School fees. Rent.",
                     sx(960), sy(870), font(22), GRAY, alpha=cue_a * 0.55, anchor="mm")

    # Fade out
    fade_out = ease_in(progress(t, 6.3, 7.0))
    if fade_out > 0:
        fl = make_gradient_bg(BLACK, BLACK)
        fl[..., 3] = 255 * fade_out
        buf = composite_over(buf, fl)

    return buf


# ─── SCENE 3: SOLUTION (10-22s) ──────────────────────────────────────────────

def scene3(t):
    # t: 0-12s within scene
    fade_in = ease_out(progress(t, 0, 0.5))

    # Background: dark navy with cool blue-green tint (relief palette)
    center = BG + np.array([0, 4, 8])
    buf = make_gradient_bg(center, BLACK * 0.65)
    buf[..., 3] = 255 * fade_in

    # ── Phone mockup ──
    ph_a = ease_out(progress(t, 0, 0.8))
    if ph_a > 0:
        ph_cx, ph_cy = sx(390), sy(540)
        ph_w, ph_h = sx(290), sy(540)
        ph_r = s(38)
        scr_pad = s(12)
        scr_top = s(50)
        scr_bot = s(28)

        # Phone shadow
        shad = pil_to_buf(Image.new("RGBA", (RW, RH), (0,0,0,0)))
        draw_rect_aa(shad, ph_cx - ph_w//2 + s(12), ph_cy - ph_h//2 + s(12),
                     ph_cx + ph_w//2 + s(12), ph_cy + ph_h//2 + s(12),
                     r=ph_r, fill=BLACK, alpha=ph_a * 0.7)
        buf = composite_over(buf, shad)

        # Phone shell (dark metal-like)
        shell = np.array([16, 22, 40])
        draw_rect_aa(buf, ph_cx - ph_w//2, ph_cy - ph_h//2,
                     ph_cx + ph_w//2, ph_cy + ph_h//2,
                     r=ph_r, fill=shell,
                     outline=np.array([38, 55, 90]), olw=s(2), alpha=ph_a)

        # Screen
        screen_col = np.array([6, 9, 22])
        draw_rect_aa(buf, ph_cx - ph_w//2 + scr_pad,
                     ph_cy - ph_h//2 + scr_top,
                     ph_cx + ph_w//2 - scr_pad,
                     ph_cy + ph_h//2 - scr_bot,
                     r=s(26), fill=screen_col, alpha=ph_a)

        # Camera notch
        notch_col = np.array([10, 14, 28])
        draw_rect_aa(buf, sx(375), ph_cy - ph_h//2 + scr_pad,
                     sx(405), ph_cy - ph_h//2 + scr_pad + s(16),
                     r=s(8), fill=notch_col, alpha=ph_a)

        # App header — "Telcoin Wallet" in cyan
        hdr_y = ph_cy - ph_h//2 + scr_top + s(38)
        draw_text_aa(buf, "Telcoin Wallet", ph_cx, hdr_y,
                     font(14, bold=True), CYAN, alpha=ph_a, anchor="mm")

        # Cyan underline under header
        def draw_hdr_ul(d):
            d.line([(ph_cx - s(90), hdr_y + s(12)), (ph_cx + s(90), hdr_y + s(12))],
                   fill=rgb(CYAN) + (180,), width=s(1))
        add_glow(buf, draw_hdr_ul, blur_r=s(4), glow_col=CYAN, glow_alpha=ph_a * 0.5)

        # Amount
        amt_y = hdr_y + s(55)
        draw_text_aa(buf, "$200.00", ph_cx, amt_y,
                     font(34, bold=True), WHITE, alpha=ph_a, anchor="mm")
        draw_text_aa(buf, "Send to Maria — GCash", ph_cx, amt_y + s(28),
                     font(11), GRAY, alpha=ph_a * 0.7, anchor="mm")

        # Divider
        div_y = amt_y + s(50)
        tmp = Image.new("RGBA", (RW, RH), (0,0,0,0))
        dv = ImageDraw.Draw(tmp)
        dv.line([(ph_cx - s(112), div_y), (ph_cx + s(112), div_y)],
                fill=rgb(np.array([28,40,70])) + (180,), width=s(1))
        buf = composite_over(buf, pil_to_buf(tmp))

        # Fee — animated value and color
        fee_y = div_y + s(36)
        if t < 2.0:
            fee_val = 12.50
            fee_col = RED
        elif t < 3.6:
            p = ease_inout(progress(t, 2.0, 3.6))
            fee_val = lerp(12.50, 4.00, p)
            fee_col = lerp(RED, GREEN, p)
        else:
            fee_val = 4.00
            fee_col = GREEN

        draw_text_aa(buf, "Fee", ph_cx - s(90), fee_y,
                     font(12), GRAY, alpha=ph_a, anchor="lm")
        fee_text = f"${fee_val:.2f}"
        draw_text_aa(buf, fee_text, ph_cx + s(90), fee_y,
                     font(16, bold=True), fee_col, alpha=ph_a, anchor="rm")

        # Glow on fee value
        def draw_fee(d):
            d.text((ph_cx + s(90), fee_y), fee_text, font=font(16, bold=True),
                   fill=rgb(fee_col) + (160,), anchor="rm")
        add_glow(buf, draw_fee, blur_r=s(10), glow_col=fee_col, glow_alpha=ph_a * 0.5)

        # Recipient
        rec_y = fee_y + s(28)
        draw_text_aa(buf, "Via", ph_cx - s(90), rec_y,
                     font(12), GRAY, alpha=ph_a, anchor="lm")
        draw_text_aa(buf, "GCash Philippines", ph_cx + s(90), rec_y,
                     font(12), GRAY, alpha=ph_a * 0.8, anchor="rm")

        # Send button
        btn_a = ease_out(progress(t, 3.6, 4.2))
        if btn_a > 0:
            btn_y = ph_cy + ph_h//2 - scr_bot - s(55)
            btn_col = lerp(BLUE, CYAN * 0.7 + BLUE * 0.3, 0.3)
            draw_rect_aa(buf, ph_cx - s(100), btn_y - s(22),
                         ph_cx + s(100), btn_y + s(22),
                         r=s(22), fill=btn_col, alpha=ph_a * btn_a)
            # Button glow
            def draw_btn(d):
                d.rounded_rectangle([ph_cx - s(100), btn_y - s(22),
                                     ph_cx + s(100), btn_y + s(22)],
                                    radius=s(22), fill=rgb(BLUE) + (120,))
            add_glow(buf, draw_btn, blur_r=s(16), glow_col=BLUE, glow_alpha=btn_a * 0.45)
            draw_text_aa(buf, "S E N D", ph_cx, btn_y,
                         font(14, bold=True), WHITE, alpha=ph_a * btn_a, anchor="mm")

        # Confirmation checkmark
        confirm_a = ease_out(progress(t, 5.0, 5.8))
        if confirm_a > 0:
            ck_y = ph_cy + ph_h//2 - scr_bot - s(55)
            # Overwrite button area with checkmark
            draw_rect_aa(buf, ph_cx - s(100), ck_y - s(22),
                         ph_cx + s(100), ck_y + s(22),
                         r=s(22), fill=np.array([8, 30, 18]), alpha=ph_a * confirm_a)
            # Checkmark
            tmp_ck = Image.new("RGBA", (RW, RH), (0,0,0,0))
            d_ck = ImageDraw.Draw(tmp_ck)
            ks = s(10)
            d_ck.line([(ph_cx - ks + s(2), ck_y),
                        (ph_cx - s(2), ck_y + ks - s(3)),
                        (ph_cx + ks, ck_y - ks + s(3))],
                      fill=rgb(GREEN) + (255,), width=s(3))
            buf = composite_over(buf, pil_to_buf(tmp_ck))
            def draw_ck(d):
                d.line([(ph_cx - ks + s(2), ck_y),
                         (ph_cx - s(2), ck_y + ks - s(3)),
                         (ph_cx + ks, ck_y - ks + s(3))],
                        fill=rgb(GREEN) + (180,), width=s(3))
            add_glow(buf, draw_ck, blur_r=s(12), glow_col=GREEN, glow_alpha=confirm_a * 0.7)
            draw_text_aa(buf, "Sent!", ph_cx, ck_y + s(36),
                         font(12, bold=True), GREEN, alpha=ph_a * confirm_a, anchor="mm")

        # Home indicator
        home_col = np.array([38, 55, 90])
        tmp_home = Image.new("RGBA", (RW, RH), (0,0,0,0))
        d_home = ImageDraw.Draw(tmp_home)
        hom_y = ph_cy + ph_h//2 - s(14)
        d_home.line([(ph_cx - s(40), hom_y), (ph_cx + s(40), hom_y)],
                    fill=rgb(home_col) + (int(180 * ph_a),), width=s(4))
        buf = composite_over(buf, pil_to_buf(tmp_home))

    # ── Stat cards — right side ──
    right_cx = sx(1200)

    # Card 1: 16 countries  — t=1.2
    c1_a = ease_out(progress(t, 1.2, 1.9))
    if c1_a > 0:
        cy1 = sy(380)
        cw1, ch1 = sx(680), sy(130)
        _draw_stat_card(buf, right_cx, cy1, cw1, ch1,
                        BLUE, "16  countries", "23+ mobile money platforms",
                        font(40, bold=True), font(20), c1_a)

    # Card 2: 2% fees — t=2.8
    c2_a = ease_out(progress(t, 2.8, 3.5))
    if c2_a > 0:
        cy2 = sy(560)
        cw2, ch2 = sx(680), sy(130)
        _draw_stat_card(buf, right_cx, cy2, cw2, ch2,
                        GREEN, "Fees: 2% or less", "vs. ~6.3% global average",
                        font(40, bold=True), font(20), c2_a, value_col=GREEN)

    # Card 3: Same day — t=5.2
    c3_a = ease_out(progress(t, 5.2, 5.9))
    if c3_a > 0:
        cy3 = sy(740)
        cw3, ch3 = sx(680), sy(110)
        _draw_stat_card(buf, right_cx, cy3, cw3, ch3,
                        CYAN, "Delivered same day", "Direct to mobile money",
                        font(30, bold=True), font(20), c3_a, value_col=CYAN)

    # Credibility line — t=7.5
    cred_a = ease_out(progress(t, 7.5, 8.2))
    if cred_a > 0:
        # Thin line above
        tmp_line = Image.new("RGBA", (RW, RH), (0,0,0,0))
        d_line = ImageDraw.Draw(tmp_line)
        d_line.line([(sx(200), sy(912)), (sx(1720), sy(912))],
                    fill=rgb(GOLD) + (int(80 * cred_a),), width=s(1))
        buf = composite_over(buf, pil_to_buf(tmp_line))

        draw_text_aa(buf, "Validated by GSMA Mobile Network Operators   ·   Telcoin Digital Asset Bank — Nebraska DADI charter",
                     sx(960), sy(940), font(15), GOLD, alpha=cred_a * 0.6, anchor="mm")

    # Fade out
    fade_out = ease_in(progress(t, 10.8, 12.0))
    if fade_out > 0:
        fl = make_gradient_bg(BLACK, BLACK)
        fl[..., 3] = 255 * fade_out
        buf = composite_over(buf, fl)

    return buf


def _draw_stat_card(buf, cx, cy, cw, ch, accent_col, line1, line2,
                    f1, f2, alpha, value_col=None):
    if value_col is None:
        value_col = WHITE

    # Shadow
    shad = pil_to_buf(Image.new("RGBA", (RW, RH), (0,0,0,0)))
    draw_rect_aa(shad, cx - cw//2 + s(8), cy - ch//2 + s(8),
                 cx + cw//2 + s(8), cy + ch//2 + s(8),
                 r=s(18), fill=BLACK, alpha=alpha * 0.55)
    buf[:] = composite_over(buf, shad)

    # Card body — subtle gradient effect via two overlapping rects
    card_bg = lerp(BG, BG * 0.3 + accent_col * 0.07, 0.7)
    draw_rect_aa(buf, cx - cw//2, cy - ch//2, cx + cw//2, cy + ch//2,
                 r=s(18), fill=card_bg,
                 outline=lerp(BLACK, accent_col, 0.3), olw=s(1), alpha=alpha)

    # Border glow
    def draw_bord(d):
        d.rounded_rectangle([cx - cw//2, cy - ch//2, cx + cw//2, cy + ch//2],
                             radius=s(18),
                             outline=rgb(accent_col) + (int(150 * alpha),), width=s(2))
    add_glow(buf, draw_bord, blur_r=s(14), glow_col=accent_col, glow_alpha=alpha * 0.35)

    # Left accent bar
    tmp = Image.new("RGBA", (RW, RH), (0,0,0,0))
    d = ImageDraw.Draw(tmp)
    d.rounded_rectangle([cx - cw//2 + s(1), cy - ch//2 + s(16),
                          cx - cw//2 + s(6), cy + ch//2 - s(16)],
                         radius=s(3), fill=rgb(accent_col) + (int(200 * alpha),))
    buf[:] = composite_over(buf, pil_to_buf(tmp))

    # Value text
    draw_text_aa(buf, line1, cx + s(14), cy - sy(16),
                 f1, value_col, alpha=alpha, anchor="mm")
    draw_text_aa(buf, line2, cx + s(14), cy + sy(20),
                 f2, GRAY, alpha=alpha * 0.7, anchor="mm")


# ─── SCENE 4: WORLD MAP (22-27s) ─────────────────────────────────────────────

def scene4(t):
    # t: 0-5s within scene
    fade_in = ease_out(progress(t, 0, 0.5))

    # Background
    buf = make_gradient_bg(BG * 0.9, BLACK * 0.7)
    buf[..., 3] = 255 * fade_in

    # Map bounds
    MX, MY = sx(60), sy(110)
    MW, MH = RW - sx(120), RH - sy(220)

    # Draw continents
    cont_pil = Image.new("RGBA", (RW, RH), (0,0,0,0))
    d_cont = ImageDraw.Draw(cont_pil)
    for poly in CONTINENTS:
        pts = [map_coords(lon, lat, MX, MY, MW, MH) for lon, lat in poly]
        if len(pts) >= 3:
            fill_col = rgb(lerp(BG, np.array([22, 34, 65]), 0.8)) + (int(220 * fade_in),)
            border_col = rgb(lerp(BG, np.array([32, 50, 100]), 0.9)) + (int(180 * fade_in),)
            d_cont.polygon(pts, fill=fill_col, outline=border_col)
    buf = composite_over(buf, pil_to_buf(cont_pil))

    # Hub position
    hub_x, hub_y = map_coords(HUB_LON, HUB_LAT, MX, MY, MW, MH)

    # Animate cities
    for i, (name, lon, lat) in enumerate(CITIES):
        cx, cy = map_coords(lon, lat, MX, MY, MW, MH)
        city_start = 0.4 + i * 0.45
        city_a = ease_out(progress(t, city_start, city_start + 0.5))
        if city_a <= 0:
            continue

        # Line from city to hub
        line_start = city_start + 0.25
        line_p = ease_out(progress(t, line_start, line_start + 0.9))
        if line_p > 0:
            px = int(cx + (hub_x - cx) * line_p)
            py = int(cy + (hub_y - cy) * line_p)
            # Glow line
            def make_line_draw(x1, y1, x2, y2, a):
                def draw_line(d):
                    d.line([(x1, y1), (x2, y2)],
                           fill=rgb(CYAN) + (int(160 * a),), width=s(1))
                return draw_line
            add_glow(buf, make_line_draw(cx, cy, px, py, city_a),
                     blur_r=s(3), glow_col=CYAN, glow_alpha=city_a * 0.5)

            # Solid line
            tmp = Image.new("RGBA", (RW, RH), (0,0,0,0))
            d = ImageDraw.Draw(tmp)
            d.line([(cx, cy), (px, py)],
                   fill=rgb(CYAN) + (int(100 * city_a),), width=s(1))
            buf = composite_over(buf, pil_to_buf(tmp))

        # City dot with multi-pass glow
        def make_dot_draw(dcx, dcy, da):
            def draw_dot(d):
                r = s(5)
                d.ellipse([dcx - r, dcy - r, dcx + r, dcy + r],
                          fill=rgb(CYAN) + (int(240 * da),))
            return draw_dot

        add_glow(buf, make_dot_draw(cx, cy, city_a), blur_r=s(18),
                 glow_col=CYAN, glow_alpha=city_a * 0.5)
        add_glow(buf, make_dot_draw(cx, cy, city_a), blur_r=s(7),
                 glow_col=CYAN, glow_alpha=city_a * 0.7)

        tmp_dot = Image.new("RGBA", (RW, RH), (0,0,0,0))
        d = ImageDraw.Draw(tmp_dot)
        r = s(5)
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=rgb(CYAN) + (int(255 * city_a),))
        buf = composite_over(buf, pil_to_buf(tmp_dot))

        # Label
        label_a = ease_out(progress(t, city_start + 0.3, city_start + 0.7))
        if label_a > 0:
            offsets = [(s(12), s(-8)), (s(12), s(8)), (s(-90), s(-8)),
                       (s(12), s(8)), (s(12), s(-8)), (s(-110), s(-8))]
            ox, oy = offsets[i]
            draw_text_aa(buf, name, cx + ox, cy + oy,
                         font(14), GRAY, alpha=label_a * 0.8, anchor="la")

    # Hub dot
    hub_a = ease_out(progress(t, 0.3, 0.7))
    if hub_a > 0:
        def draw_hub(d):
            r = s(7)
            d.ellipse([hub_x - r, hub_y - r, hub_x + r, hub_y + r],
                      fill=rgb(BLUE) + (int(240 * hub_a),))
        add_glow(buf, draw_hub, blur_r=s(22), glow_col=BLUE, glow_alpha=hub_a * 0.6)
        add_glow(buf, draw_hub, blur_r=s(8), glow_col=BLUE, glow_alpha=hub_a * 0.8)
        tmp_hub = Image.new("RGBA", (RW, RH), (0,0,0,0))
        d = ImageDraw.Draw(tmp_hub)
        r = s(7)
        d.ellipse([hub_x - r, hub_y - r, hub_x + r, hub_y + r],
                  fill=rgb(BLUE) + (int(255 * hub_a),))
        buf = composite_over(buf, pil_to_buf(tmp_hub))

    # Title
    title_a = ease_out(progress(t, 0.6, 1.2))
    if title_a > 0:
        draw_text_aa(buf, "GSMA MOBILE NETWORK OPERATORS  ·  6 CORRIDORS  ·  16 COUNTRIES",
                     sx(960), sy(58), font(16), GRAY, alpha=title_a * 0.55, anchor="mm")

    # Credential pills
    pill_a = ease_out(progress(t, 2.5, 3.2))
    if pill_a > 0:
        pills = [
            (BLUE,  "GSMA Mobile Network Operator validators"),
            (GOLD,  "Telcoin Digital Asset Bank  ·  Nebraska DADI  ·  November 12, 2025"),
        ]
        for pi, (pcol, ptxt) in enumerate(pills):
            py_ = sy(940) + pi * sy(48)
            # Measure text width
            bbox = font(17).getbbox(ptxt)
            tw = (bbox[2] - bbox[0])
            px_ = sx(960)
            pad = s(22)
            # Pill bg
            draw_rect_aa(buf, px_ - tw//2 - pad, py_ - s(18),
                         px_ + tw//2 + pad, py_ + s(18),
                         r=s(18),
                         fill=lerp(BG, pcol * 0.08, 0.5),
                         outline=lerp(BG, pcol, 0.25), olw=s(1), alpha=pill_a)
            def make_pill_border(bpx, bpy, bw, bh, bc, ba):
                def draw_pill_bord(d):
                    d.rounded_rectangle([bpx - bw//2 - pad, bpy - s(18),
                                         bpx + bw//2 + pad, bpy + s(18)],
                                        radius=s(18),
                                        outline=rgb(bc) + (int(100 * ba),), width=s(1))
                return draw_pill_bord
            add_glow(buf, make_pill_border(px_, py_, tw, 36, pcol, pill_a),
                     blur_r=s(8), glow_col=pcol, glow_alpha=pill_a * 0.3)
            draw_text_aa(buf, ptxt, px_, py_,
                         font(17), pcol if pi == 1 else WHITE,
                         alpha=pill_a, anchor="mm")

    # Fade out
    fade_out = ease_in(progress(t, 4.2, 5.0))
    if fade_out > 0:
        fl = make_gradient_bg(BLACK, BLACK)
        fl[..., 3] = 255 * fade_out
        buf = composite_over(buf, fl)

    return buf


# ─── SCENE 5: CTA (27-30s) ───────────────────────────────────────────────────

def scene5(t):
    # t: 0-3s
    fade_in = ease_out(progress(t, 0, 0.6))

    # Near-black background — confident, minimal
    buf = make_gradient_bg(np.array([6, 8, 16]), BLACK * 0.95)
    buf[..., 3] = 255 * fade_in

    # Thin horizontal rule
    rule_a = ease_out(progress(t, 0.3, 0.8))
    if rule_a > 0:
        rw = int(sx(200) * rule_a)
        tmp_rule = Image.new("RGBA", (RW, RH), (0,0,0,0))
        d = ImageDraw.Draw(tmp_rule)
        d.line([(sx(960) - rw, sy(460)), (sx(960) + rw, sy(460))],
               fill=rgb(CYAN) + (int(60 * rule_a),), width=s(1))
        buf = composite_over(buf, pil_to_buf(tmp_rule))

    # ── Wordmark — manually tracked TELCOIN ──
    word_a = ease_out(progress(t, 0.2, 0.9))
    if word_a > 0:
        letters = "TELCOIN"
        f_wm = font(88, bold=True)
        spacing = s(26)
        # Calculate total width
        widths = [f_wm.getbbox(c)[2] - f_wm.getbbox(c)[0] for c in letters]
        total_w = sum(widths) + spacing * (len(letters) - 1)
        sx_start = sx(960) - total_w // 2
        xpos = sx_start
        wm_y = sy(530)
        for ch, cw in zip(letters, widths):
            draw_text_aa(buf, ch, xpos, wm_y,
                         f_wm, WHITE, alpha=word_a, anchor="lm")
            xpos += cw + spacing

        # Wordmark glow — very subtle
        def draw_wordmark(d):
            xp = sx_start
            for ch2, cw2 in zip(letters, widths):
                d.text((xp, wm_y), ch2, font=f_wm,
                       fill=(255, 255, 255, int(60 * word_a)), anchor="lm")
                xp += cw2 + spacing
        add_glow(buf, draw_wordmark, blur_r=s(22), glow_col=WHITE, glow_alpha=word_a * 0.12)

    # Tagline
    tag_a = ease_out(progress(t, 0.8, 1.3))
    if tag_a > 0:
        draw_text_aa(buf, "Money that moves.", sx(960), sy(586),
                     font(28), GRAY, alpha=tag_a * 0.75, anchor="mm")

    # URL — cyan
    url_a = ease_out(progress(t, 1.3, 1.8))
    if url_a > 0:
        draw_text_aa(buf, "telco.in", sx(960), sy(634),
                     font(22), CYAN, alpha=url_a * 0.9, anchor="mm")
        def draw_url(d):
            d.text((sx(960), sy(634)), "telco.in", font=font(22),
                   fill=rgb(CYAN) + (int(150 * url_a),), anchor="mm")
        add_glow(buf, draw_url, blur_r=s(12), glow_col=CYAN, glow_alpha=url_a * 0.5)

    # Final fade to black
    fade_out = ease_in(progress(t, 2.3, 3.0))
    if fade_out > 0:
        fl = make_gradient_bg(BLACK, BLACK)
        fl[..., 3] = 255 * fade_out
        buf = composite_over(buf, fl)

    # Apply fade-in on top
    fi_layer = make_gradient_bg(BLACK, BLACK)
    fi_layer[..., 3] = 255 * (1 - fade_in)
    buf = composite_over(buf, fi_layer)

    return buf


# ─── FRAME DISPATCH ───────────────────────────────────────────────────────────

def render_frame(global_t):
    if global_t < 3.0:
        buf = scene1(global_t)
    elif global_t < 10.0:
        buf = scene2(global_t - 3.0)
    elif global_t < 22.0:
        buf = scene3(global_t - 10.0)
    elif global_t < 27.0:
        buf = scene4(global_t - 22.0)
    else:
        buf = scene5(global_t - 27.0)

    return finalize_frame(buf)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Telcoin 30s — v2 high-quality render")
    print(f"Render res: {RW}×{RH} → output: {W}×{H}")
    print(f"Frames: {N_FRAMES} at {FPS}fps ({DURATION}s)")
    print(f"Output: {OUT_FILE}\n")

    from moviepy import VideoClip

    def make_frame(t):
        return render_frame(t)

    clip = VideoClip(make_frame, duration=DURATION)
    clip.write_videofile(
        OUT_FILE,
        fps=FPS,
        codec="libx264",
        audio=False,
        preset="slow",
        ffmpeg_params=["-crf", "16", "-pix_fmt", "yuv420p"],
        logger="bar",
    )
    print(f"\nDone: {OUT_FILE}")


if __name__ == "__main__":
    main()
