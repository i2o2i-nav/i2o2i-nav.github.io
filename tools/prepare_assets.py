#!/usr/bin/env python3
"""Prepare faithful web copies and result tables from the manuscript repository.

Requires Pillow, pdftoppm, ffmpeg, and ffprobe for asset regeneration.
The website itself has no runtime dependencies or build step.
Existing media outputs are kept; use a fresh output directory to regenerate them.
"""

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def rows_from_tex(path, expected_columns):
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip().endswith("\\\\") or "&" not in line:
            continue
        cells = [part.strip() for part in line.strip()[:-2].split("&")]
        if len(cells) != expected_columns:
            continue
        # Data rows have a numeric metric immediately after the method name.
        plain_number = re.sub(r"\\textbf\{([^{}]+)\}", r"\1", cells[1])
        if not re.fullmatch(r"\d+\.\d+", plain_number):
            continue
        row = []
        for cell in cells:
            plain = re.sub(r"\\textbf\{([^{}]+)\}", r"\1", cell)
            row.append({"value": plain, "bold": "\\textbf" in cell})
        rows.append(row)
    return rows


def table(title, columns, rows, groups=None):
    output = [f'<div class="table-wrap" role="region" aria-label="{html.escape(title)}" tabindex="0"><table>',
              f'<caption>{html.escape(title)}</caption><thead>']
    if groups:
        output.append('<tr><th rowspan="2" scope="col">Method</th>')
        output.extend(f'<th colspan="{count}" scope="colgroup">{html.escape(name)}</th>' for name, count in groups)
        output.append('</tr><tr>')
        names = columns[1:]
    else:
        output.append('<tr>')
        names = columns
    output.extend(f'<th scope="col">{html.escape(name)}</th>' for name in names)
    output.append('</tr></thead><tbody>')
    for row in rows:
        css_class = ' class="agent-row"' if row[0]["value"].startswith("MODULAR-Agent") else ""
        output.append(f'<tr{css_class}>')
        for index, cell in enumerate(row):
            value = html.escape(cell["value"])
            if cell["bold"]:
                value = f'<strong>{value}</strong>'
            output.append(f'<th scope="row">{value}</th>' if index == 0 else f'<td>{value}</td>')
        output.append('</tr>')
    output.append('</tbody></table></div>')
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-root", type=Path, required=True)
    args = parser.parse_args()
    paper = args.paper_root.resolve()
    site = Path(__file__).resolve().parents[1]
    records = []

    def record(source, destination, operation):
        records.append({"source": str(source.relative_to(paper)),
                        "source_sha256": digest(source),
                        "output": str(destination.relative_to(site)),
                        "output_sha256": digest(destination),
                        "operation": operation})

    images = {
        "benchmark-framework": "arxiv/figs/benchmark_framework.png",
        "scene-views-01": "ppt/1_scene_random1.png",
        "scene-views-02": "ppt/1_scene_random2.png",
        "scene-views-03": "ppt/1_scene_random3.png",
        "mesh-geometry": "arxiv/appendix/a_materials/7_mesh.png",
        "region-annotations": "arxiv/appendix/a_materials/4_area_lable.png",
        "object-annotations": "arxiv/appendix/a_materials/5_object_lable_object.png",
        "failure-cases": "arxiv/figs/l1_failed_cases.png",
    }
    pdf_images = {
        "mission-overview": "arxiv/figs/cover.pdf",
        "modular-agent": "arxiv/figs/agent_system.pdf",
    }
    for stem, relative in {**images, **pdf_images}.items():
        source = paper / relative
        output = site / "assets/images" / f"{stem}.webp"
        output.parent.mkdir(parents=True, exist_ok=True)
        if not output.exists():
            if stem in pdf_images:
                rendered = output.with_suffix(".png")
                if not rendered.exists():
                    subprocess.run(["pdftoppm", "-f", "1", "-singlefile", "-scale-to", "2400", "-png", str(source), str(output.with_suffix(""))], check=True)
                image = Image.open(rendered)
            else:
                image = Image.open(source)
            image = image.convert("RGB")
            image.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
            image.save(output, "WEBP", quality=90, method=6)
        record(source, output, "Full frame; proportional resize to at most 2400px; WebP encoding. No content edits.")

    source_video = paper / "ppt/i2o2i_nav_supplementary_v04_submit.mp4"
    video = site / "assets/videos/navigation-demo.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    if not video.exists():
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-n", "-ss", "67", "-i", str(source_video), "-t", "131", "-vf", "scale=1280:-2", "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "29", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video)], check=True)
    record(source_video, video, "Extract [67,198) seconds (complete trajectory-following segment); proportional 1280px encoding; no additional speed change. Original speed badges retained. Not an agent evaluation rollout.")
    poster = site / "assets/images/navigation-poster.jpg"
    if not poster.exists():
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-n", "-ss", "35", "-i", str(video), "-frames:v", "1", "-update", "1", str(poster)], check=True)
    record(source_video, poster, "Full-frame poster at 35s in the extracted video (102s in supplementary video).")

    source_pdf = paper / "arxiv/release_20261012/main_project_page.pdf"
    paper_pdf = site / "assets/papers/i2o2i-nav-project-page.pdf"
    paper_pdf.parent.mkdir(parents=True, exist_ok=True)
    if not paper_pdf.exists():
        shutil.copyfile(source_pdf, paper_pdf)
    record(source_pdf, paper_pdf, "Byte-for-byte copy of the project-page release; no PDF edits.")

    sources = {"l1": "arxiv/table/tab_02_l1_exit_entrance_ovon.tex",
               "l2": "arxiv/table/tab_03_l2_composition.tex",
               "l3": "arxiv/table/tab_04_l3_full_chain.tex"}
    results = {key: rows_from_tex(paper / relative, count)
               for (key, relative), count in zip(sources.items(), [14, 15, 10])}
    assert [len(results[key]) for key in sources] == [4, 2, 2], "Unexpected result table structure"
    panels = []
    for i, key in enumerate(sources, 1):
        hidden = "" if i == 1 else " hidden"
        panels.append(f'<div id="result-panel-{i}" role="tabpanel" aria-labelledby="result-tab-{i}" tabindex="0"{hidden}>')
        if key == "l1":
            panels.append(table("L1 · Exit, Entrance, and OVON", ["Method"] + ["SR ↑", "SPL ↑", "TL (m)"] * 3,
                                [row[:10] for row in results[key]], [("Exit", 3), ("Entrance", 3), ("OVON", 3)]))
            panels.append(table("L1 · OutdoorNav", ["Method", "SR ↑", "SPL ↑", "DCR ↑"], [row[10:] for row in results[key]]))
            panels.append('<p class="table-note">200 episodes per primitive. SR, SPL, and DCR are percentages; TL is in meters. Bold values reproduce the paper’s best-result formatting.</p>')
        elif key == "l2":
            for start, name in [(1, "I2O · Exit → OutdoorNav"), (8, "O2I · OutdoorNav → Entrance")]:
                panels.append(table(name, ["Method", "FSR ↑", "CSR ↑", "SPL ↑", "RC ↑", "DCR ↑", "C₁ ↑", "C₂ ↑"],
                                    [[row[0]] + row[start:start + 7] for row in results[key]]))
            panels.append('<p class="table-note">200 episodes per composition. All values are percentages. C₁ and C₂ are stage-conditional success rates in task order.</p>')
        else:
            panels.append(table("L3 · Exit → OutdoorNav → Entrance → OVON", ["Method", "FSR ↑", "CSR ↑", "SPL ↑", "RC ↑", "DCR ↑", "C₁ ↑", "C₂ ↑", "C₃ ↑", "C₄ ↑"], results[key], [("Full mission", 5), ("Stage-conditional success", 4)]))
            panels.append('<p class="table-note">174 episodes. All values are percentages. C₁–C₄ follow Exit, OutdoorNav, Entrance, and OVON. Full success requires all four stages.</p>')
        panels.append('</div>')
    index = site / "index.html"
    content = index.read_text()
    content = re.sub(r"<!-- BEGIN GENERATED RESULTS -->.*?<!-- END GENERATED RESULTS -->",
                     "<!-- BEGIN GENERATED RESULTS -->\n" + "\n".join(panels) + "\n<!-- END GENERATED RESULTS -->",
                     content, flags=re.S)
    # Reserve each image's true aspect ratio to avoid layout shifts.
    def dimensions(match):
        tag = match.group(0)
        src = re.search(r'src="([^"]+)"', tag)
        if src and (site / src[1]).exists():
            width, height = Image.open(site / src[1]).size
            tag = re.sub(r'\s+(?:width|height)="\d+"', '', tag)
            tag = tag[:-1] + f' width="{width}" height="{height}">'
        return tag
    content = re.sub(r'<img\b[^>]*>', dimensions, content)
    index.write_text(content)
    result_data = site / "assets/results.json"
    result_data.write_text(json.dumps({"sources": sources, "tables": results}, indent=2) + "\n")
    for relative in sources.values():
        record(paper / relative, result_data, "Exact metric strings and bold flags extracted from current arXiv LaTeX tables; static HTML generated without recalculation.")
    (site / "assets/manifest.json").write_text(json.dumps({"assets": records}, indent=2) + "\n")
    print(f"Prepared {len(records)} source records and all 94 numeric result cells in {site}")


if __name__ == "__main__":
    main()
