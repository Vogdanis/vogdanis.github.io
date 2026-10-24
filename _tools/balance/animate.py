"""Balance: a breeze passes through the sculpture and the floating elements spin in place.

Physical model (from Yiannis's description):
  * each element hangs on a fishing line that runs up to a groove at the top of the pole
    and down to its mirror element on the other arm;
  * a magnet in the arm pulls the element's lower tip, so string force and magnetic force are
    collinear: the element is a two-force body whose axis is the line pole-top -> lower tip;
  * a breeze applies a torque, the element spins around that axis, the line's torsion slowly
    winds it back (damped torsional pendulum), and the twist leaks a little to its partner.
The photo is never warped: elements are matted out, the wall is filled in, and each element is
re-projected in 3D around its own axis every frame.
"""
import numpy as np, cv2, sys, os
from PIL import Image

FPS, T = 30, 18.0
OUT = sys.argv[1] if len(sys.argv) > 1 else 'frames'
os.makedirs(OUT, exist_ok=True)

im = np.asarray(Image.open('src.jpg').convert('RGB')).astype(np.float32)
H, W, _ = im.shape
lab = np.load('lab.npy'); yellow = np.load('yellow.npy')
POLE_TOP = np.array([479.0, 155.0])

# ---------- pick the 8 elements (drop the dark underside strips of the arms) ----------
near_y = cv2.dilate(yellow, np.ones((9, 9), np.uint8)) > 0
elems = []
for i in np.load('keep.npy'):
    m = lab == i
    frac = near_y[m].mean()
    if frac < 0.6 and m.sum() > 150:
        elems.append(int(i))
print('elements', elems)

# ---------- background: remove elements, fill wall ----------
mask_all = np.zeros((H, W), np.uint8)
for i in elems:
    mask_all |= (lab == i)
mask_fill = cv2.dilate(mask_all, np.ones((7, 7), np.uint8))
# the arms (yellow + their dark underside strips) must neither be erased nor bleed into the wall
arm = yellow.astype(bool).copy()
for i in np.load('keep.npy'):
    if int(i) not in elems:
        arm |= (lab == i)
arm = cv2.dilate(arm.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
fill = (mask_fill > 0) & ~arm
src8 = im.astype(np.uint8)
wall_only = cv2.inpaint(src8, (fill | cv2.dilate(arm.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)).astype(np.uint8), 7, cv2.INPAINT_TELEA)
bg = np.where(fill[..., None], wall_only, src8).astype(np.float32)
mask_fill = fill.astype(np.uint8)
# put back wall grain so the filled strokes don't read as smudges
rng = np.random.default_rng(7)
grain_src = im[60:560, 40:440] - cv2.GaussianBlur(im[60:560, 40:440], (0, 0), 3)
ys, xs = np.nonzero(mask_fill)
gy = rng.integers(0, grain_src.shape[0], 1); gx = rng.integers(0, grain_src.shape[1], 1)
tile = np.tile(grain_src, (H // grain_src.shape[0] + 2, W // grain_src.shape[1] + 2, 1))[:H, :W]
soft = cv2.GaussianBlur(mask_fill.astype(np.float32), (0, 0), 1.5)[..., None]
bg = bg + tile * soft * 0.9
bg = np.clip(bg, 0, 255)

# ---------- matte each element ----------
S = 3          # supersampling of the render canvas
SUB = 4        # sub-samples per source pixel per axis
parts = []
for i in elems:
    m = (lab == i).astype(np.uint8)
    core = cv2.erode(m, np.ones((3, 3), np.uint8))
    region = cv2.dilate(m, np.ones((5, 5), np.uint8)) > 0
    c = np.median(im[core > 0], axis=0) if core.sum() > 10 else np.median(im[m > 0], axis=0)
    d = bg - c
    a = ((bg - im) * d).sum(2) / np.maximum((d * d).sum(2), 1)
    a = np.clip(a, 0, 1) * region
    a[a < 0.04] = 0
    py, px = np.nonzero(a > 0)
    # lower tip = point nearest the yellow arm (where the magnet holds it)
    ay, ax = np.nonzero(yellow)
    pts = np.stack([px, py], 1).astype(np.float32)
    sel = pts[:: max(1, len(pts) // 400)]
    dmin = np.full(len(sel), 1e9)
    armpts = np.stack([ax, ay], 1)[::7].astype(np.float32)
    for k in range(0, len(armpts), 2000):
        dd = ((sel[:, None, :] - armpts[None, k:k + 2000, :]) ** 2).sum(2).min(1)
        dmin = np.minimum(dmin, dd)
    tip = sel[np.argmin(dmin)]
    # top = where the line is tied: the point of the piece reaching furthest toward the pole top
    up = POLE_TOP - tip; up /= np.linalg.norm(up)
    allp = np.stack([px, py], 1).astype(np.float32)
    top = allp[np.argmax((allp - tip) @ up)]
    # the piece spins about its own axis as it sits in the photo: top and tip never move
    u = top - tip; u /= np.linalg.norm(u)
    n = np.array([-u[1], u[0]])
    cen = np.array([px.mean(), py.mean()])
    # sub-sample grid
    off = (np.arange(SUB) + 0.5) / SUB - 0.5
    ox, oy = np.meshgrid(off, off)
    sx = (px[:, None] + ox.ravel()[None, :]).ravel()
    sy = (py[:, None] + oy.ravel()[None, :]).ravel()
    sa = np.repeat(a[py, px], SUB * SUB)
    rel = np.stack([sx, sy], 1) - tip
    parts.append(dict(id=i, color=c, tip=tip, top=top, u=u, n=n, cen=cen,
                      along=rel @ u, across=rel @ n, alpha=sa,
                      bbox=(px.min(), py.min(), px.max(), py.max())))
print([(p['id'], p['cen'].round().tolist()) for p in parts])

# ---------- physics ----------
# pairs at the same height share one line
left = sorted([p for p in parts if p['cen'][0] < POLE_TOP[0]], key=lambda p: p['cen'][1])
right = sorted([p for p in parts if p['cen'][0] >= POLE_TOP[0]], key=lambda p: p['cen'][1])
pair = {}
for a_, b_ in zip(left, right):
    pair[a_['id']] = b_['id']; pair[b_['id']] = a_['id']
idx = {p['id']: k for k, p in enumerate(parts)}
N = len(parts)
rs = np.random.default_rng(11)
x0 = min(p['cen'][0] for p in parts)
V_GUST = 220.0                       # px/s, a soft draft from the window on the left
delay = np.array([1.2 + (p['cen'][0] - x0) / V_GUST + rs.uniform(0, .4) for p in parts])
Tper = np.array([10.0 + 3.0 * (p['cen'][1] - 700) / 300 + rs.uniform(-.8, .8) for p in parts])  # longer line, softer
k_t = (2 * np.pi / Tper) ** 2
c_d = 2 * rs.uniform(0.38, 0.48, N) * (2 * np.pi / Tper)   # calm, one gentle overshoot
kap = 0.12 * k_t                      # twist shared through the line
reach = np.array([1.0 - 0.6 * (p['cen'][0] - x0) / (W - x0) for p in parts])  # breeze weakens across
turns_target = reach * rs.uniform(0.35, 0.6, N) * np.sign(rs.uniform(-1, 1, N))
GD = 5.0                              # the draft builds and fades over ~5 s

def gust(t):
    x = np.clip(t / GD, 0, 1)
    return np.where((t > 0) & (t < GD), np.sin(np.pi * x) ** 2, 0.0)

def simulate(A, dt=1 / 600):
    steps = int(T / dt) + 1
    th = np.zeros(N); om = np.zeros(N); out = np.zeros((steps, N))
    for s in range(steps):
        t = s * dt
        tau = A * gust(t - delay)
        cpl = np.array([kap[k] * (th[idx[pair[p['id']]]] - th[k]) if p['id'] in pair else 0 for k, p in enumerate(parts)])
        acc = tau - k_t * th - c_d * om + cpl
        om += acc * dt; th += om * dt
        out[s] = th
    return out, dt

unit, dt = simulate(np.ones(N))
peak = np.abs(unit).max(0)
A = turns_target * 2 * np.pi / peak
theta, dt = simulate(A)
# land exactly at rest so the loop is seamless
tt = np.arange(theta.shape[0]) * dt
fade = 1 - np.clip((tt - (T - 3.2)) / 3.0, 0, 1)
fade = fade * fade * (3 - 2 * fade)
theta = theta * fade[:, None]

# ---------- endless version ----------
# A constant soft draft keeps every piece turning, all the time, each at its own pace.
# Every component repeats a whole number of times in T, so frame T == frame 0: a seamless loop.
MAIN = {3: (3, .30), 4: (2, .34), 8: (3, .42), 10: (4, .24), 19: (2, .36), 23: (3, .28), 31: (2, .32), 32: (4, .22)}
rp = np.random.default_rng(23)
w0 = 2 * np.pi / T
theta = np.zeros_like(theta)
for k, p in enumerate(parts):
    n1, a1 = MAIN[p['id']]
    n2 = rp.choice([5, 6, 7]); a2 = rp.uniform(.04, .07)
    a0 = rp.uniform(.06, .12)
    f1, f2, f0 = rp.uniform(0, 2 * np.pi, 3)
    theta[:, k] = 2 * np.pi * 0.78 * (a1 * np.sin(n1 * w0 * tt + f1) + a2 * np.sin(n2 * w0 * tt + f2) + a0 * np.sin(w0 * tt + f0))
fade = np.ones_like(tt)
print('peak turns', (np.abs(theta).max(0) / 2 / np.pi).round(2).tolist())
# slight in-plane sway about the magnet tip, driven by the same breeze
sway_amp = 0.0 * reach  # no sway: the angle of each piece never changes
def sway(t):
    tl = t - delay
    return np.where(tl > 0, sway_amp * np.exp(-tl / 1.1) * np.sin(2 * np.pi * tl / 1.3), 0) * np.interp(t, tt, fade)

F = 2600.0  # focal length in px for a touch of perspective
canvas_shape = (H * S, W * S)

def render(fi):
    t = fi / FPS
    th = theta[min(int(round(t / dt)), theta.shape[0] - 1)]
    sw = sway(t)
    acc = np.zeros(canvas_shape, np.float32)
    col = np.zeros((H, W, 3), np.float32); wsum = np.zeros((H, W), np.float32)
    frame = bg.copy()
    for k, p in enumerate(parts):
        ct, st = np.cos(th[k]), np.sin(th[k])
        b = p['across'] * ct; z = p['across'] * st
        s = F / (F - z)
        a_ = p['along'] * s; b = b * s
        u, n = p['u'], p['n']
        cs, ss = np.cos(sw[k]), np.sin(sw[k])
        u2 = np.array([cs * u[0] - ss * u[1], ss * u[0] + cs * u[1]])
        n2 = np.array([-u2[1], u2[0]])
        X = p['tip'][0] + a_ * u2[0] + b * n2[0]
        Y = p['tip'][1] + a_ * u2[1] + b * n2[1]
        ix = np.clip((X * S).astype(np.int32), 0, W * S - 1)
        iy = np.clip((Y * S).astype(np.int32), 0, H * S - 1)
        layer = np.zeros(canvas_shape, np.float32)
        np.maximum.at(layer, (iy, ix), p['alpha'])
        al = layer.reshape(H, S, W, S).mean((1, 3))
        # a wire seen edge-on is a hair darker (more paint in the line of sight)
        shade = 1.0 - 0.12 * abs(st)
        frame = frame * (1 - al[..., None]) + (p['color'] * shade)[None, None, :] * al[..., None]
    return np.clip(frame, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    nF = int(T * FPS)
    only = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else range(nF)
    Image.fromarray(bg.astype(np.uint8)).save('bg.png')
    for fi in only:
        Image.fromarray(render(fi)[:, :W - (W % 2)]).save(f'{OUT}/{fi:04d}.png')
