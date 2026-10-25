"""Drops: the frozen drop hovers while its ripples keep travelling outward.

A cinemagraph built from the original photograph. The water is warped by a small radial
travelling wave (in the ellipse the rings make in perspective), so the reflections roll
outward the way they would on the tray. The drop itself is never touched. Every wave
completes a whole number of cycles in T, so the loop is seamless.
"""
import numpy as np, cv2, os, sys
from PIL import Image

FPS, T, UP = 30, 6.0, 2
OUT = sys.argv[1] if len(sys.argv) > 1 else 'frames'
os.makedirs(OUT, exist_ok=True)

src = np.asarray(Image.open('src.jpg').convert('RGB')).astype(np.float32)
H0, W0, _ = src.shape
# 2x for a sharper hero: Lanczos + a gentle unsharp mask (water is smooth, it upscales well)
img = cv2.resize(src, (W0 * UP, H0 * UP), interpolation=cv2.INTER_LANCZOS4)
blur = cv2.GaussianBlur(img, (0, 0), 1.4)
img = np.clip(img + 0.45 * (img - blur), 0, 255)
H, W = img.shape[:2]

# geometry (measured on the 516 x 729 original, scaled up)
DROP = np.array([327.0, 412.0]) * UP; DROP_R = 34 * UP          # the hovering drop
C = np.array([327.0, 476.0]) * UP                                 # centre of the rings (dimple)
Q = 0.42                                                          # ellipse squash from perspective
SURF = 150 * UP                                                   # far edge of the water

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
dx, dy = xx - C[0], (yy - C[1]) / Q
r = np.sqrt(dx * dx + dy * dy) + 1e-3
ux, uy = dx / r, dy / r * Q                                       # outward direction on the image

def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

env = smooth(40 * UP, 95 * UP, r) * (1 - 0.55 * smooth(150 * UP, 420 * UP, r))   # rings fade far out
env *= smooth(SURF, SURF + 60 * UP, yy)                                          # calm at the far edge
dd = np.hypot(xx - DROP[0], yy - DROP[1])
env *= smooth(DROP_R + 2 * UP, DROP_R + 14 * UP, dd)                             # ripples never touch the drop
drop_w = 1 - smooth(DROP_R + 1 * UP, DROP_R + 9 * UP, dd)                        # the drop moves as one piece

WAVES = [  # (wavelength px @1x, cycles per loop, amplitude px @1x)
    (68, 4, 3.4),
    (43, 6, 1.5),
    (110, 3, 1.9),
]

def frame(i):
    t = i / (FPS * T)
    d = np.zeros_like(r)
    for lam, n, a in WAVES:
        d += a * UP * np.sin(2 * np.pi * (r / (lam * UP) - n * t))
    d *= env
    # the drop hangs in the air and drifts up and down a hair, twice per loop
    bob = 1.6 * UP * np.sin(2 * np.pi * 2 * t)
    mx = (xx - d * ux).astype(np.float32)
    my = (yy - d * uy - bob * drop_w).astype(np.float32)
    out = cv2.remap(img, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return np.clip(out, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    n = int(FPS * T)
    only = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else range(n)
    for i in only:
        Image.fromarray(frame(i)).save(f'{OUT}/{i:04d}.png')
