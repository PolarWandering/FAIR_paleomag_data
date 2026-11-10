"""Platforms figure of the FAIR standard paper: the MagIC database and
Paleomagnetism.org.

Two browser screenshots side by side, each framed as a browser window with its
URL:
    (a) the MagIC home page (earthref.org/MagIC), down to its two latest
        contributions;
    (b) the Paleomagnetism.org 2 data library (paleomagnetism.org/library), down
        to its two latest publications.

The two windows have the same height; the page width left of the panel labels
is shared between them in proportion to the aspect ratios of the screenshots.

The screenshots are taken by capture_platform_screenshots.py (headless Chrome,
narrow windows, device scale factor 2) into screenshots/, already clipped to the
region shown; run it again to update them (the MagIC "Recent Contributions" list
and the library map change with time).

Outputs: platforms.pdf and platforms.png, next to this script.

Usage:
    python make_platforms_figure.py

Requires numpy, matplotlib and Pillow.
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch
from PIL import Image

HERE = Path(__file__).resolve().parent
FIG_DIR = HERE
SHOT_DIR = HERE / "screenshots"
SCALE = 2  # device pixels per CSS pixel in the screenshots

# Each panel: the screenshot, the URL shown in the window bar, and the height
# (CSS px) over which the foot of the screenshot fades to white where the page
# continues below (None for no fade). The MagIC screenshot ends with the title
# line of the third contribution, which is what the fade covers.
PANELS = [
    dict(label="a", file="magic.png", shown_url="earthref.org/MagIC", fade_px=38),
    dict(label="b", file="pmag_library.png", shown_url="paleomagnetism.org/library",
         fade_px=None),
]

FIG_WIDTH = 6.85    # in (174 mm, full page width)
LEFT = 0.2          # in, room for the label of the first panel
GAP = 0.3           # in, between windows, with the label of the second panel
RIGHT = 0.06
TOP = 0.06
BOTTOM = 0.1        # in, room for the drop shadow
BAR = 0.17          # in, height of the window title bar
CORNER = 0.06       # in, corner radius of the windows

BAR_COLOR = "#EEEEF1"
EDGE_COLOR = "#BDBDC4"
URL_COLOR = "#3A3A40"
LIGHTS = ["#FF5F57", "#FEBC2E", "#28C840"]


def load_screenshot(panel):
    """Return the screenshot of a panel as an RGB array."""
    with Image.open(SHOT_DIR / panel["file"]) as im:
        return np.asarray(im.convert("RGB"))


def rounded_box(ax, x, y, w, h, **kwargs):
    """Add a rounded rectangle (inches) to the axes and return it."""
    box = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={CORNER}",
                         **kwargs)
    ax.add_patch(box)
    return box


def draw_window(ax, x, y_top, w, img, panel):
    """Draw a screenshot framed as a browser window.

    Args:
        ax: axes whose data coordinates are inches, origin at the lower left.
        x (float): left edge of the window.
        y_top (float): top edge of the window.
        w (float): window width.
        img (ndarray): the screenshot.
        panel (dict): an entry of PANELS.
    """
    img_h = w * img.shape[0] / img.shape[1]
    h = BAR + img_h
    y = y_top - h

    # soft drop shadow: stacked translucent boxes, each a little larger
    for i in range(1, 7):
        grow = 0.01 * i
        rounded_box(ax, x - grow, y - grow - 0.02, w + 2 * grow, h + 2 * grow,
                    facecolor="black", edgecolor="none", alpha=0.018, zorder=1)

    frame = rounded_box(ax, x, y, w, h, facecolor=BAR_COLOR, edgecolor="none", zorder=2)
    shot = ax.imshow(img, extent=(x, x + w, y, y + img_h), interpolation="none", zorder=3)
    shot.set_clip_path(frame)

    if panel["fade_px"] is not None:
        fade_h = panel["fade_px"] * SCALE * w / img.shape[1]
        fade = np.ones((256, 1, 4))
        fade[:, 0, 3] = np.linspace(0, 1, 256) ** 1.5
        veil = ax.imshow(fade, extent=(x, x + w, y, y + fade_h), interpolation="bilinear",
                         aspect="auto", zorder=4)
        veil.set_clip_path(frame)

    ax.plot([x, x + w], [y + img_h, y + img_h], color=EDGE_COLOR, lw=0.5, zorder=5)
    rounded_box(ax, x, y, w, h, facecolor="none", edgecolor=EDGE_COLOR, lw=0.6, zorder=6)

    bar_mid = y_top - BAR / 2
    for i, color in enumerate(LIGHTS):
        ax.add_patch(Circle((x + 0.1 + 0.085 * i, bar_mid), 0.028, facecolor=color,
                            edgecolor="none", zorder=6))
    url_w = 0.5 * w
    url_x = x + (w - url_w) / 2
    ax.add_patch(FancyBboxPatch((url_x, bar_mid - 0.055), url_w, 0.11,
                                boxstyle="round,pad=0,rounding_size=0.045",
                                facecolor="white", edgecolor="#D4D4DA", lw=0.4, zorder=6))
    ax.text(url_x + url_w / 2, bar_mid, panel["shown_url"], ha="center", va="center",
            fontsize=5.5, color=URL_COLOR, zorder=7)

    ax.text(x - 0.11, y_top - 0.01, panel["label"], ha="center", va="top",
            fontsize=10, fontweight="bold", zorder=7)


def main():
    images = [load_screenshot(p) for p in PANELS]

    # windows of equal height: widths in proportion to the aspect ratios
    aspects = np.array([im.shape[1] / im.shape[0] for im in images])
    widths = (FIG_WIDTH - LEFT - GAP - RIGHT) * aspects / aspects.sum()
    img_height = widths[0] / aspects[0]
    fig_height = TOP + BAR + img_height + BOTTOM

    fig = plt.figure(figsize=(FIG_WIDTH, fig_height))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, FIG_WIDTH)
    ax.set_ylim(0, fig_height)
    ax.axis("off")

    x = LEFT
    for panel, img, width in zip(PANELS, images, widths):
        draw_window(ax, x, fig_height - TOP, width, img, panel)
        print(f"panel {panel['label']}: {width:.2f} in wide, "
              f"{72 * width * SCALE / img.shape[1]:.3f} pt per CSS px")
        x += width + GAP

    for ext, kwargs in [("pdf", {}), ("png", {"dpi": 600})]:
        out = FIG_DIR / f"platforms.{ext}"
        fig.savefig(out, facecolor="white", **kwargs)
        print("wrote", out)


if __name__ == "__main__":
    main()
