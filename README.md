# vogdanis.com

Personal site of Yiannis Vogdanis. It's a Jekyll site that GitHub Pages builds automatically on every push to `master`. You don't need a build step on your computer.

## Where things live

| What | File |
|---|---|
| A project (title, text, images, video, YouTube) | `_projects/<name>.md` |
| Press & publications list | `_data/press.yml` |
| CV: exhibitions, education, experience, toolchain | `_data/cv.yml` |
| BinaryCeramics collections (home + /binaryceramics/) | `_data/collections.yml` |
| Home page | `index.html` |
| About page | `about/index.html` |
| BinaryCeramics page | `binaryceramics/index.html` |
| Design (colours, type, layout) | `assets/css/site.css` |
| Generative hero (the printing vessel) | `assets/js/toolpath.js` |
| Site settings, email, socials, UTM tag | `_config.yml` |

## Add or edit a project

1. Put the original photos anywhere under `img/` (originals are never modified). Anything in `img/portfolio/<project>/` is picked up automatically as `pf/<project>/<first 3 characters of the filename>`.
2. Register each photo in `_tools/build_media.py` → `IMAGES` with a short key, e.g. `"newproject/1": "img/projects/newproject/IMG_001.jpg"`.
3. Run `python3 _tools/build_media.py`. This writes resized WebP files to `media/` and updates `_data/media.yml`.
4. Copy an existing file in `_projects/` (e.g. `playball.md`) and edit the front matter:
   - `featured: true` shows the project in **Selected work**. Leave it out to put it in the **Archive**.
   - `order` sets the position. `idx` is the binary index shown on the site.
   - `hero` is the image key. `hero_video` is optional (a file in `media/video/`), and `ai_motion: true` adds the "AI motion study" note.
   - `films` is a list of `[YouTube video ID, caption]`. The first one is shown large, the rest in a grid below it. `gallery` is a list of `[image key, caption]`.
5. Write the text below the second `---`.
6. Commit and push. GitHub Pages rebuilds in about a minute.

## Notes

- Outbound links to binaryceramics.com carry `?utm_source=vogdanis.com…` (set in `_config.yml`) so Shopify analytics can attribute traffic from this site.
- The email address is assembled in JavaScript to keep it away from scrapers.
- Videos marked as AI motion studies were generated with Higgsfield (Kling 3.0) from original photographs. The originals are in your Higgsfield library, and `_tools/higgsfield/` (git-ignored) is where to drop them if you ever need to re-encode.
- Old URLs (`/home`, `/cv/`, `/contact/`, `/bird/`) redirect to the new pages. Old image paths under `/img/` still work.
- Preview locally (optional): `gem install jekyll -v 3.10.0 && jekyll serve`, then open http://localhost:4000.
