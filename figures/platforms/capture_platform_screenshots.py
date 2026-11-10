"""Screenshots of MagIC and Paleomagnetism.org for the platforms figure
(make_platforms_figure.py).

Drives headless Google Chrome over the DevTools protocol, so that each capture
waits in real time for the page to finish loading:
    - MagIC (earthref.org/MagIC): the "Recent Contributions" plot thumbnails
      load after the page, one request each. Each thumbnail box holds a
      "Loading" dimmer that stays in the page underneath the thumbnail, so the
      capture waits until every such box holds a loaded image (a contribution
      without plots has no dimmer, and reads "No Plots Available"). The
      screenshot is clipped to the page content, from the page title down to
      the two latest contributions.
    - Paleomagnetism.org data library: a "new version" dialog opens on the first
      visit (localStorage "__VERSION__" differs from the site version). The
      version is stored and the page reloaded, so the dialog does not open.
      The page opens its Leaflet map at zoom 1, where the map is about 2.5
      world widths wide and the continents repeat. The map is reset to a
      fractional zoom at which it is one world width wide (lon -170 to 190), its
      height cut to the latitudes of the markers, and its tiles loaded at
      retina resolution. The screenshot is clipped to the map, its heading, its
      caption and the two latest publications in the table.

The two panels of the figure are side by side, so both pages are loaded in
narrow windows, at the narrowest width that keeps the layout of a desktop
browser: 1000 px for MagIC (below 992 px the globes and plot thumbnails of the
contributions are dropped) and 800 px for the library (below 768 px the last
columns of the publication table are cut off).

Screenshots are written at a device scale factor of 2 to screenshots/, next to
this script.

Usage:
    python capture_platform_screenshots.py

Requires websocket-client and Google Chrome.
"""

import base64
import json
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import websocket

HERE = Path(__file__).resolve().parent
SHOT_DIR = HERE / "screenshots"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = 9333
SCALE = 2

# One world width across the map, centred on CENTER_LON so that the map runs
# from 170 W to 190 E and the New Zealand marker is not cut by the edge; height
# from the northernmost marker (plus the 41 px height of a pin) to the
# southernmost. The zoom buttons are hidden. `map` is the page's global Leaflet
# map (library/js/index.js in Jollyfant/PMAG2).
CENTER_LON = 10
PMAG_MAP_JS = """(() => {
  const CENTER_LON = %d;""" % CENTER_LON + """
  map.options.zoomSnap = 0;
  map.eachLayer(layer => { if (layer instanceof L.TileLayer) map.removeLayer(layer); });
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
              {detectRetina: true}).addTo(map);
  const div = map.getContainer();
  const width = div.clientWidth;
  const zoom = Math.log2(width / 256);
  const lats = [];
  map.eachLayer(layer => { if (layer instanceof L.Marker) lats.push(layer.getLatLng().lat); });
  const yTop = map.project([Math.max(...lats), 0], zoom).y - 55;
  const yBottom = map.project([Math.min(...lats), 0], zoom).y + 20;
  div.style.height = Math.round(yBottom - yTop) + "px";
  map.invalidateSize();
  const center = map.unproject([width / 2, (yTop + yBottom) / 2], zoom);
  map.setView([center.lat, CENTER_LON], zoom, {animate: false});
  document.querySelector('.leaflet-control-zoom').style.display = 'none';
  return [lats.length, zoom, yBottom - yTop];
})()"""

# Number of latest MagIC contributions, and of latest library publications,
# kept in the screenshots.
N_LATEST = 2

# Region kept: the map heading down to the N_LATEST latest publications in the
# table, as the MagIC panel shows its latest contributions.
PMAG_CLIP_JS = """(() => {
  const N_LATEST = %d;""" % N_LATEST + """
  const top = [...document.querySelectorAll('h5')]
    .find(h => h.textContent.includes('Available Publications')).getBoundingClientRect();
  const map = document.getElementById('map').getBoundingClientRect();
  const lastRow = [...document.querySelectorAll('#publication-table tr')]
    .filter(row => row.querySelector('td'))[N_LATEST - 1].getBoundingClientRect();
  const margin = 14;
  return {x: map.left - margin, y: top.top + window.scrollY - margin,
          width: map.width + 2 * margin,
          height: lastRow.bottom - top.top + margin};
})()"""

# Region kept: the page content (without the EarthRef menu bar above it), from
# the page title down to the title line of contribution N_LATEST + 1, which the
# figure fades out to show that the list continues.
MAGIC_CLIP_JS = """(() => {
  const N_LATEST = %d;""" % N_LATEST + """
  const page = document.querySelector('.layout-content.container').getBoundingClientRect();
  const title = document.querySelector('h1.page-title').getBoundingClientRect();
  const next = document.querySelectorAll('.search-summaries-list-item')[N_LATEST]
    .getBoundingClientRect();
  const margin = 10;
  const top = title.top + window.scrollY - 6;
  return {x: page.left - margin, y: top, width: page.width + 2 * margin,
          height: next.top + window.scrollY + 22 - top};
})()"""

# The MagIC page is ready when the contributions are listed, every plot
# thumbnail box (the parent of a "Loading" dimmer) holds a loaded image, and no
# other image of the page is still loading.
MAGIC_READY_JS = """(() => {
  const loaded = img => img.complete && img.naturalWidth > 0;
  const boxes = [...document.querySelectorAll('.ui.text.loader')]
    .map(loader => loader.closest('.dimmer').parentElement);
  return document.body.innerText.includes('MagIC Contribution Link')
    && boxes.every(box => [...box.querySelectorAll('img')].some(loaded))
    && [...document.images].every(img => img.complete);
})()"""

PAGES = [
    dict(url="https://earthref.org/MagIC/", window=(1000, 1300), file="magic.png",
         ready=MAGIC_READY_JS, clip=MAGIC_CLIP_JS),
    dict(url="https://www.paleomagnetism.org/library/", window=(800, 1500),
         file="pmag_library.png", skip_version_dialog=True,
         ready="document.querySelectorAll('.leaflet-marker-icon').length > 0",
         prepare=PMAG_MAP_JS,
         tiles_ready="document.querySelectorAll('.leaflet-tile:not(.leaflet-tile-loaded)')"
                     ".length === 0",
         clip=PMAG_CLIP_JS),
]


class DevTools:
    """Minimal DevTools-protocol client for one page target."""

    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=60)
        self.msg_id = 0

    def call(self, method, **params):
        self.msg_id += 1
        self.ws.send(json.dumps({"id": self.msg_id, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.msg_id:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    def evaluate(self, expression):
        result = self.call("Runtime.evaluate", expression=expression, returnByValue=True)
        return result["result"].get("value")

    def wait_for(self, ready, timeout=120):
        """Wait until the page has loaded and the JS expression ready is true."""
        start = time.time()
        while not (self.evaluate("document.readyState") == "complete" and self.evaluate(ready)):
            if time.time() - start > timeout:
                raise TimeoutError(f"page not ready after {timeout} s: {ready}")
            time.sleep(1)
        time.sleep(3)  # let images and fonts paint

    def load(self, url, ready):
        """Navigate to url and wait until the JS expression ready is true."""
        self.call("Page.navigate", url=url)
        time.sleep(2)
        self.wait_for(ready)


def page_target():
    """Return the websocket URL of Chrome's first page target, waiting for Chrome."""
    for _ in range(30):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json") as resp:
                targets = json.load(resp)
            return next(t["webSocketDebuggerUrl"] for t in targets if t["type"] == "page")
        except (OSError, StopIteration):
            time.sleep(0.5)
    raise RuntimeError("Chrome DevTools endpoint did not come up")


def main():
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as profile_dir:
        chrome = subprocess.Popen(
            [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             f"--remote-debugging-port={PORT}", f"--remote-allow-origins=http://127.0.0.1:{PORT}",
             f"--user-data-dir={profile_dir}",
             "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            tab = DevTools(page_target())
            tab.call("Page.enable")
            for page in PAGES:
                width, height = page["window"]
                tab.call("Emulation.setDeviceMetricsOverride", width=width, height=height,
                         deviceScaleFactor=SCALE, mobile=False)
                tab.load(page["url"], page["ready"])
                if page.get("skip_version_dialog"):
                    tab.evaluate("localStorage.setItem('__VERSION__', __VERSION__)")
                    tab.load(page["url"], page["ready"])
                if "prepare" in page:
                    print("prepared:", tab.evaluate(page["prepare"]))
                    tab.wait_for(page["tiles_ready"])
                params = dict(format="png")
                if "clip" in page:
                    params["clip"] = dict(tab.evaluate(page["clip"]), scale=1)
                shot = tab.call("Page.captureScreenshot", **params)
                out = SHOT_DIR / page["file"]
                out.write_bytes(base64.b64decode(shot["data"]))
                print("wrote", out)
        finally:
            chrome.terminate()
            chrome.wait()


if __name__ == "__main__":
    main()
