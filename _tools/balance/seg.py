import numpy as np, cv2
from PIL import Image
im = np.asarray(Image.open('src.jpg').convert('RGB')).astype(np.float32)
H, W, _ = im.shape
hsv = cv2.cvtColor(im.astype(np.uint8), cv2.COLOR_RGB2HSV)
lum = im.mean(2)
yellow = (hsv[..., 1] > 90) & (hsv[..., 0] > 20) & (hsv[..., 0] < 45) & (lum > 90)
yellow = cv2.morphologyEx(yellow.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
yellow_d = cv2.dilate(yellow, np.ones((3, 3), np.uint8))
dark = (lum < 95)
region = np.zeros_like(dark); region[640:1000, :] = True
region[:, 462:492] = False  # pole
m = (dark & region & (yellow_d == 0)).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
n, lab, stats, cents = cv2.connectedComponentsWithStats(m, 8)
keep = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] > 80]
print(len(keep))
for i in keep: print(i, stats[i].tolist(), cents[i].round(1).tolist())
vis = im.copy().astype(np.uint8)
cols = [(255,0,0),(0,160,0),(0,0,255),(255,0,255),(0,200,200),(255,128,0),(128,0,255),(0,0,0),(120,60,0),(255,0,128)]
for k, i in enumerate(keep):
    vis[lab == i] = cols[k % len(cols)]
    x, y = cents[i].astype(int); cv2.putText(vis, str(i), (x+12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, cols[k % len(cols)], 2)
Image.fromarray(vis[600:1060]).save('seg_vis.png')
np.save('lab.npy', lab); np.save('keep.npy', np.array(keep)); np.save('yellow.npy', yellow)
