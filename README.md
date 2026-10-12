# I2O2I-Nav project website

Static academic project page inspired by the layout of [UrbanVerse](https://urbanverseproject.github.io/). HTML, CSS, and JavaScript are written for this project; UrbanVerse code, images, and videos are not bundled. All scientific content and media come from the I2O2I-Nav manuscript repository.

## Local preview

No package installation or build step is required:

```bash
cd /home/shu22/navigation/agentvln/i2o2i-nav.github.io
python3 -m http.server 8000 --bind 127.0.0.1
```

Open <http://localhost:8000>. If using a remote IDE, forward port 8000 and open its forwarded URL. Press Ctrl+C to stop the server.

## Files

- `index.html`: title, authors, text, figures, accessible scene tabs, vertically stacked result tables, and citation.
- `style.css`: responsive layout, typography, desktop contents, and mobile styles.
- `script.js`: tab keyboard controls, BibTeX copying, and contents highlighting.
- `assets/images/`: proportionally resized full-frame WebP copies of existing figures, plus a video poster.
- `assets/videos/navigation-demo.mp4`: the 131-second trajectory-following segment from the existing supplementary video.
- `assets/papers/i2o2i-nav-arxiv.pdf`: an unchanged copy of the current `arxiv/main.pdf`, with Lingxin Jiang as the fourth author and affiliation 5 (Independent Researcher). Older PDF copies are retained.
- `assets/results.json`: exact result strings extracted from the three current arXiv tables.
- `assets/manifest.json`: media sources, transformations, and SHA-256 hashes.

The demonstration illustrates the environment and task stages. It is not a MODULAR-Agent evaluation rollout. Existing speed labels and the source segment's speed changes are retained. No new speed changes, crops, or scientific annotations were added.

## Editing

Edit prose and author information directly in `index.html`; adjust styles in `style.css`. The `arXiv` resource button is intentionally disabled until the official URL is available. Replace it with an anchor when that URL is provided; retain the separate `Paper PDF` download. Also update the BibTeX record with the official identifier then. No arXiv identifier or conference acceptance is assumed in this version.

The code button points to <https://github.com/i2o2i-nav/i2o2i_nav>.

Result HTML is generated between `BEGIN GENERATED RESULTS` and `END GENERATED RESULTS`. To refresh it and prepare missing media, run:

```bash
python3 tools/prepare_assets.py \
  --paper-root /home/shu22/navigation/agentvln/i2o2i_paper
```

Asset preparation requires Pillow, Poppler (`pdftoppm`), and FFmpeg (`ffmpeg`, `ffprobe`); visitors and local preview do not require these tools. The script preserves existing media outputs. For a complete media refresh, prepare a new checkout/output directory rather than overwriting original research artifacts. The script updates the generated HTML, result JSON, and manifest.

## GitHub Pages

1. Commit and push the reviewed website files to `main`.
2. In **Settings → Pages**, choose **Deploy from a branch**.
3. Choose **main** and **/ (root)**, then save.
4. After deployment completes, open <https://i2o2i-nav.github.io/>.

`.nojekyll` keeps this as a buildless static site. Local historical backups remain excluded from Git. This update adds the current paper PDF without deleting existing PDF assets.
