#!/usr/bin/env python3
"""
Build optimized web media for vogdanis.com.

  python3 _tools/build_media.py            # images only (fast, skips existing)
  python3 _tools/build_media.py --force    # rebuild everything
  python3 _tools/build_media.py --video    # also (re)encode videos

Reads originals from img/ (never modified) and writes:
  media/<key>-<width>.webp   responsive image variants
  media/video/<name>.mp4     H.264 loops (+ <name>.webp poster)
  _data/media.yml            sizes + average colour for every key (used by _includes/img.html)

To add an image: put the original somewhere under img/, add a line to IMAGES below
("key": "img/path.jpg"), run the script, then reference the key in a project's front matter.
Requires: Pillow, ffmpeg (for --video).
"""
import json, os, subprocess, sys
from PIL import Image, ImageOps, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "media")
WIDTHS = [480, 960, 1600, 2400]
FORCE = "--force" in sys.argv
VIDEO = "--video" in sys.argv

P = "img/projects/"
BC = "img/binaryceramics/"

IMAGES = {
    # ---- BinaryCeramics -------------------------------------------------
    "bc/hero-lattice": BC + "untitled_12_of_21.jpg",
    "bc/hero-lines": BC + "untitled_32_of_87.jpg",
    "bc/tornado-detail": BC + "Tornado_Collection.jpg",
    "bc/tornado": BC + "Tornado_Group.jpg",
    "bc/wave": BC + "WaveCollection.jpg",
    "bc/dash": BC + "Dash_Group.jpg",
    "bc/intersect": BC + "Intersect_Group.jpg",
    "bc/intersect-detail": BC + "Intersect_Banner.jpg",
    "bc/frequency": BC + "Frequency_Collection.jpg",
    "bc/sea-urchin": BC + "untitled_38_of_56.jpg",
    "bc/lathe": BC + "20221214-IMG_1619.jpg",
    "bc/extruder-parts": BC + "77.jpg",
    "bc/extruder-hand": BC + "IMG_1639.jpg",
    "bc/bench": BC + "IMG_1130.jpg",
    "bc/delta-printer": BC + "48.jpg",
    "bc/studio-batch": BC + "DSCF3999.jpg",
    "bc/studio-pour": BC + "DSCF4012.jpg",
    "bc/studio-weld": BC + "DSCF3524.jpg",
    "bc/studio-glaze": BC + "DSCF5855.jpg",
    "about/portrait": BC + "Portrait-BW-portrait.jpg",
    "about/portrait-2019": "img/vogdanis2.png",
    "about/studio-2019": "img/MyStudio.jpg",
    # ---- Clay ---------------------------------------------------------
    "clay/lattice": P + "clay/3.jpg",
    "clay/spikes": P + "clay/2.jpg",
    "clay/tube": P + "clay/1.jpg",
    "clay/top": P + "clay/6.jpg",
    "clay/layers": P + "clay/5.jpg",
    "clay/cactus": P + "clay/cactus.jpg",
    "clay/texture": P + "clay/texture-banner.jpg",
    "clay/extruder": P + "clay/Extruder.jpg",
    "clay/ram-extruder": P + "clay/RamExtruder.png",
    "clay/pcb": P + "clay/pcb.jpg",
    "clay/wire": P + "clay/view2.png",
    # ---- Playball -----------------------------------------------------
    "playball/cloud": P + "playball/6.jpg",
    "playball/violet": P + "playball/7.jpg",
    "playball/spheres": P + "playball/8.jpg",
    "playball/rig": P + "playball/9.jpg",
    "playball/warm": P + "playball/5.jpg",
    "playball/module": P + "playball/3.jpg",
    "playball/pcbs": P + "playball/1.jpg",
    "playball/bench": P + "playball/2.jpg",
    "playball/visitors": "img/banner/_4.jpg",
    "playball/reach": "img/banner/3.jpg",
    "playball/pink": P + "playball/playball.jpg",
    # ---- Eyes ---------------------------------------------------------
    "eyes/disk": P + "eyes/IMG_8282.jpg",
    "eyes/table": P + "eyes/IMG_1945.jpg",
    "eyes/workbench": P + "eyes/IMG_4812.jpg",
    "eyes/iris": P + "eyes/mati.png",
    "eyes/strip": P + "eyes/eye-banner-1.png",
    # ---- Dystopian Places ---------------------------------------------
    "dystopian/mask": P + "dystopian/Mask-trans2.png",
    "dystopian/render": P + "dystopian/RenderKS1.4.jpg",
    "dystopian/photo": P + "dystopian/dystopian.jpg",
    "dystopian/map": P + "dystopian/Screen Shot 2018-10-29 at 8.37.59 PM.png",
    "dystopian/map-detail": P + "dystopian/map1.png",
    "dystopian/wire": P + "dystopian/Inverted.png",
    # ---- Plotter ------------------------------------------------------
    "plotter/design": P + "plotter/PlotterDesign.png",
    "plotter/rail": P + "rail/rail.jpg",
    # ---- pyDrum -------------------------------------------------------
    "drum/front": P + "drum/1.jpg",
    "drum/angle": P + "drum/2.jpg",
    # ---- Obsession ----------------------------------------------------
    "obsession/lit": P + "obsession/2.jpg",
    "obsession/build": P + "obsession/1.jpg",
    "obsession/sketch": P + "obsession/3.jpg",
    "obsession/black": P + "obsession/4.jpg",
    # ---- Archive ------------------------------------------------------
    "bronze/1": P + "bronze/Gallery/1.jpg",
    "bronze/2": P + "bronze/Gallery/2.jpg",
    "bronze/3": P + "bronze/Gallery/3.jpg",
    "bronze/4": P + "bronze/Gallery/4.jpg",
    "bronze/5": P + "bronze/Gallery/5.jpg",
    "balance/1": P + "balance/Gallery/1.jpg",
    "balance/2": P + "balance/Gallery/2.jpg",
    "balance/3": P + "balance/Gallery/3.jpg",
    "bird/1": P + "bird/bird.jpg",
    "bird/drawing": P + "bird/bird-drawing.jpg",
    "modules/1": P + "modules/4.jpg",
    "modules/2": P + "modules/1.jpg",
    "modules/3": P + "modules/2.jpg",
    "modules/4": P + "modules/3.jpg",
    "modules/5": P + "modules/5.jpg",
    "modules/6": P + "modules/6.jpg",
    "modules/7": P + "modules/7.jpg",
    "modules/8": P + "modules/8.jpg",
    "wheel/1": P + "wheel/10.jpg",
    "wheel/2": P + "wheel/1.jpg",
    "wheel/3": P + "wheel/2.jpg",
    "wheel/4": P + "wheel/5.jpg",
    "wheel/5": P + "wheel/7.jpg",
    "small/1": P + "small/1.jpg",
    "small/2": P + "small/2.jpg",
    "small/3": P + "small/3.jpg",
    "small/4": P + "small/4.jpg",
    "drops/1": P + "drops/Gallery/7.jpg",
    "drops/2": P + "drops/Gallery/10.jpg",
    "drops/3": P + "drops/Gallery/2.jpg",
    "drops/4": P + "drops/Gallery/3.jpg",
    "drops/5": P + "drops/Gallery/5.jpg",
    "drops/6": P + "drops/Gallery/8.jpg",
    "drops/7": P + "drops/Gallery/9.jpg",
    "drops/8": P + "drops/Gallery/6.jpg",
    "inks/1": P + "inks/0-3.jpg",
    "inks/2": P + "inks/1.jpg",
    "inks/3": P + "inks/0-1.jpg",
    "inks/4": P + "inks/3.jpg",
    "inks/5": P + "inks/5.jpg",
    "inks/6": P + "inks/6.jpg",
    "inks/7": P + "inks/0-4.jpg",
    "inks/8": P + "inks/7.jpg",
    "inks/9": P + "inks/2.jpg",
    "exsnia/1": P + "exsnia/Gallery/0-2.jpg",
    "exsnia/2": P + "exsnia/Gallery/1.jpg",
    "exsnia/3": P + "exsnia/Gallery/4.jpg",
    "exsnia/4": P + "exsnia/Gallery/6.jpg",
    "exsnia/5": P + "exsnia/Gallery/0-1.jpg",
    "exsnia/6": P + "exsnia/Gallery/9.jpg",
    "exsnia/7": P + "exsnia/Gallery/5.jpg",
    "exsnia/8": P + "exsnia/Gallery/2.jpg",
    "exsnia/9": P + "exsnia/Gallery/7.jpg",
    "exsnia/10": P + "exsnia/Gallery/0-3.jpg",
    "yosemite/1": P + "yosemite/1.jpg",
    "yosemite/2": P + "yosemite/6.jpg",
    "yosemite/3": P + "yosemite/0-3.jpg",
    "yosemite/4": P + "yosemite/7.jpg",
    "yosemite/5": P + "yosemite/3.jpg",
    "yosemite/6": P + "yosemite/2.jpg",
    "yosemite/7": P + "yosemite/9.jpg",
    "yosemite/8": P + "yosemite/0-4.jpg",
    # ---- Line drawings (white on black, used as archive glyphs) --------
    "glyph/balance": P + "balance/balance.png",
    "glyph/bird": P + "bird/bird.png",
    "glyph/bronze": P + "bronze/bronze.png",
    "glyph/drops": P + "drops/dropsBW.png",
    "glyph/drum": P + "drum/drum.png",
    "glyph/dystopian": P + "dystopian/dystopianBW.png",
    "glyph/exsnia": P + "exsnia/exsniaBW.png",
    "glyph/eyes": P + "eyes/eyes.png",
    "glyph/inks": P + "inks/inksBW.png",
    "glyph/modules": P + "modules/modules.png",
    "glyph/obsession": P + "obsession/obsession.png",
    "glyph/playball": P + "playball/playball.png",
    "glyph/plotter": P + "plotter/PlotterDesign.png",
    "glyph/small": P + "small/small.png",
    "glyph/wheel": P + "wheel/wheel.png",
    "glyph/yosemite": P + "yosemite/yosemiteBW.png",
    "glyph/clay": P + "clay/view1-1300px.png",
}

# Originals from the Universities/Portfolio folder (exported at max 2400px) -> keys "pf/<project>/<nnn>"
import glob as _glob
for _f in sorted(_glob.glob(os.path.join(ROOT, "img/portfolio/*/*.jpg"))):
    _proj = os.path.basename(os.path.dirname(_f))
    _n = os.path.basename(_f)[:3]
    IMAGES[f"pf/{_proj}/{_n}"] = os.path.relpath(_f, ROOT)

# name: (source, max width, is_gif, start, duration)
VIDEOS = {
    "eyes-pov": (P + "eyes/hddCol1.gif", 1600, True, 0, None),
    "eyes-pov-2": (P + "eyes/hddCol.gif", 1280, True, 0, None),
    "clay-lattice": ("_tools/higgsfield/clay_lattice.mp4", 1280, False, 0, None),
    "playball-drift": ("_tools/higgsfield/playball.mp4", 1280, False, 0, None),
    "inks-bloom": ("_tools/higgsfield/inks.mp4", 1280, False, 0, None),
    "wheel-light": ("_tools/higgsfield/wheel.mp4", 1080, False, 0, None),
    "modules-orbit": ("_tools/higgsfield/modules.mp4", 1280, False, 0, None),
    "drum-light": ("_tools/higgsfield/drum.mp4", 1280, False, 0, None),
    "bc-tornado": ("_tools/higgsfield/bc_tornado.mp4", 1080, False, 0, None),
}


def avg_color(im):
    small = im.convert("RGB").resize((1, 1), Image.LANCZOS)
    r, g, b = small.getpixel((0, 0))
    return "#%02x%02x%02x" % (r, g, b)


def build_glyph(key, src):
    """Line drawings: thicken strokes, then store as white lines on transparency."""
    im = Image.open(os.path.join(ROOT, src)).convert("L")
    bbox = im.point(lambda v: 255 if v > 60 else 0).getbbox()
    if bbox:
        pad = 40
        im = im.crop((max(0, bbox[0]-pad), max(0, bbox[1]-pad), min(im.width, bbox[2]+pad), min(im.height, bbox[3]+pad)))
    side = max(im.size)
    sq = Image.new("L", (side, side), 0); sq.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
    k = max(3, (side // 90) | 1)
    sq = sq.filter(ImageFilter.MaxFilter(k)).resize((192, 192), Image.LANCZOS)
    out = Image.new("RGBA", sq.size, (236, 231, 222, 0)); out.putalpha(sq.point(lambda v: min(255, v * 2)))
    os.makedirs(os.path.dirname(os.path.join(OUT, key)), exist_ok=True)
    out.save(os.path.join(OUT, f"{key}-192.webp"), "WEBP", quality=90, method=6)
    return {"w": [192], "width": 192, "height": 192, "color": "transparent", "alpha": True}


def build_image(key, src):
    if key.startswith("glyph/"):
        return build_glyph(key, src)
    path = os.path.join(ROOT, src)
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
    im = im.convert("RGBA" if has_alpha else "RGB")
    w, h = im.size
    widths = [x for x in WIDTHS if x < w] + [min(w, WIDTHS[-1])]
    widths = sorted(set(widths))
    os.makedirs(os.path.dirname(os.path.join(OUT, key)), exist_ok=True)
    for tw in widths:
        dst = os.path.join(OUT, f"{key}-{tw}.webp")
        if os.path.exists(dst) and not FORCE:
            continue
        th = round(h * tw / w)
        out = im if tw == w else im.resize((tw, th), Image.LANCZOS)
        q = 80 if tw <= 960 else 76
        out.save(dst, "WEBP", quality=q, method=6)
    return {"w": widths, "width": w, "height": h, "color": avg_color(im), "alpha": has_alpha}


def build_video(name, src, maxw, is_gif, start, dur):
    os.makedirs(os.path.join(OUT, "video"), exist_ok=True)
    dst = os.path.join(OUT, "video", f"{name}.mp4")
    poster = os.path.join(OUT, "video", f"{name}.webp")
    if not VIDEO and os.path.exists(dst):
        return
    vf = f"scale='min({maxw},iw)':-2:flags=lanczos,format=yuv420p"
    if not is_gif:
        # crush near-black noise a touch so loops sit cleanly on the dark page
        vf = "curves=all='0/0 0.06/0.03 1/1'," + vf
    cmd = ["ffmpeg", "-v", "error", "-y"]
    if start:
        cmd += ["-ss", str(start)]
    cmd += ["-i", os.path.join(ROOT, src)]
    if dur:
        cmd += ["-t", str(dur)]
    cmd += ["-an", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "24",
            "-movflags", "+faststart", "-pix_fmt", "yuv420p", dst]
    subprocess.run(cmd, check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", dst, "-frames:v", "1",
                    "-c:v", "libwebp", "-quality", "75", poster], check=True)


def main():
    data = {}
    for key, src in IMAGES.items():
        data[key] = build_image(key, src)
    for name, args in VIDEOS.items():
        if os.path.exists(os.path.join(ROOT, args[0])):
            build_video(name, *args)
    # _data/media.yml (JSON is valid YAML)
    with open(os.path.join(ROOT, "_data", "media.yml"), "w") as f:
        f.write("# Generated by _tools/build_media.py. Do not edit by hand.\n")
        for key, v in data.items():
            f.write(f'"{key}": {json.dumps(v)}\n')
    print(f"{len(data)} images, media/ ready")


if __name__ == "__main__":
    main()
