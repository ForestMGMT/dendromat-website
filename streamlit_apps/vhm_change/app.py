"""
Canopy Height Change Map — Streamlit app
Dendromat / dendromat.ch

Workflow:
  1. User draws a rectangle or polygon on a map of Switzerland (≤ 10 km²).
  2. App queries the FOEN/BAFU STAC catalog to list available VHM years.
  3. User selects two years (Year A = baseline, Year B = comparison).
  4. App reads windowed COG tiles for both years, computes difference (B – A),
     applies a red–green colormap, and offers the result as a GeoTIFF download.

Data sources (STAC, COG, EPSG:2056):
  LiDAR  — ch.bafu.landesforstinventar-vegetationshoehenmodell_lidar  (0.5 m, 2017–)
  Stereo — ch.bafu.landesforstinventar-vegetationshoehenmodell         (1 m,   2007–)

Resolution rule:
  • LiDAR available for BOTH selected years → use LiDAR (0.5 m)
  • Otherwise → use Stereo (1 m) for both years
"""

import io
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

import folium
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import requests
import rioxarray
import streamlit as st
from folium.plugins import Draw
from pyproj import Transformer
from rasterio.crs import CRS
from shapely.geometry import shape
from shapely.ops import transform as shapely_transform
from streamlit_folium import st_folium

# ── Constants ────────────────────────────────────────────────────────────────

STAC_BASE = "https://data.geo.admin.ch/api/stac/v0.9/collections"

COLLECTIONS = {
    "lidar": "ch.bafu.landesforstinventar-vegetationshoehenmodell_lidar",
    "stereo": "ch.bafu.landesforstinventar-vegetationshoehenmodell",
}

COG_URL_TEMPLATE = {
    "lidar": (
        "https://data.geo.admin.ch/"
        "ch.bafu.landesforstinventar-vegetationshoehenmodell_lidar/"
        "landesforstinventar-vegetationshoehenmodell_lidar_{year}/"
        "landesforstinventar-vegetationshoehenmodell_lidar_{year}_2056.tif"
    ),
    "stereo": (
        "https://data.geo.admin.ch/"
        "ch.bafu.landesforstinventar-vegetationshoehenmodell/"
        "landesforstinventar-vegetationshoehenmodell_{year}/"
        "landesforstinventar-vegetationshoehenmodell_{year}_stereo_2056.tif"
    ),
}

# Max allowed area in m²
MAX_AREA_M2 = 10_000_000  # 10 km²

# Switzerland center for the initial map view
CH_CENTER = [46.8, 8.2]
CH_ZOOM = 8

# EPSG:2056 ↔ WGS84
_to_2056 = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
_to_wgs84 = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)


# ── STAC helpers ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stac_items(collection_key: str) -> dict:
    """
    Return {year: {"bbox": (minx,miny,maxx,maxy), "geom": Polygon}} in WGS84.

    The item geometry is the precise survey footprint (a strip for LiDAR, a
    partial-country polygon for older Stereo years).  Using it for intersection
    is much more accurate than the bounding box alone, and avoids false positives
    for years where the bbox overlaps the drawn area but the actual strip does not.
    """
    coll_id = COLLECTIONS[collection_key]
    url = f"{STAC_BASE}/{coll_id}/items?limit=100"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        features = resp.json().get("features", [])
        items = {}
        for feat in features:
            item_id = feat.get("id", "")
            try:
                year = int(item_id.split("_")[-1])
                bbox = feat.get("bbox")
                geom_json = feat.get("geometry")
                if bbox:
                    items[year] = {
                        "bbox": tuple(bbox),
                        "geom": shape(geom_json) if geom_json else None,
                    }
            except (ValueError, Exception):
                pass
        return items
    except Exception:
        return {}


def cog_url(collection_key: str, year: int) -> str:
    return COG_URL_TEMPLATE[collection_key].format(year=year)


# ── Geometry helpers ──────────────────────────────────────────────────────────

def geojson_to_shapely(geojson_geom: dict):
    """Convert a GeoJSON geometry dict (WGS84) to a Shapely geometry."""
    return shape(geojson_geom)


def years_in_area(stac_items: dict, poly_wgs84) -> list[int]:
    """
    Return sorted years whose STAC footprint intersects the drawn polygon.

    Uses the precise item geometry when available (survey strip, not full-country
    bbox), which eliminates false positives for strip-based LiDAR acquisitions
    and avoids unnecessary COG requests for years that don't cover the area.
    Falls back to bbox if the item has no geometry.
    """
    from shapely.geometry import box as shapely_box
    result = []
    for year, item in stac_items.items():
        footprint = item.get("geom") or shapely_box(*item["bbox"])
        if footprint.intersects(poly_wgs84):
            result.append(year)
    return sorted(result)


def polygon_to_lv95_bbox(poly_wgs84) -> tuple[float, float, float, float]:
    """
    Transform a Shapely polygon (WGS84) to EPSG:2056 and return its bounding box
    as (minx, miny, maxx, maxy) in LV95 metres.
    """
    transformed = shapely_transform(
        lambda x, y: _to_2056.transform(x, y),
        poly_wgs84,
    )
    return transformed.bounds  # (minx, miny, maxx, maxy)


def area_m2(poly_wgs84) -> float:
    """Approximate planar area of a WGS84 polygon, in m², using LV95 projection."""
    transformed = shapely_transform(
        lambda x, y: _to_2056.transform(x, y),
        poly_wgs84,
    )
    return transformed.area


# ── Coverage check ────────────────────────────────────────────────────────────

def _open_and_clip(url: str, bbox_2056: tuple, overview_level: int | None = None):
    """
    Open a COG (without masked=True to avoid wrong nodata interpretation),
    clip to the LV95 bbox, squeeze the band dimension, and return a float32
    numpy array with nodata pixels set to NaN.
    """
    kwargs = {}
    if overview_level is not None:
        kwargs["overview_level"] = overview_level

    ds = rioxarray.open_rasterio(url, **kwargs)  # masked=False intentionally
    ds_clipped = ds.rio.clip_box(
        minx=bbox_2056[0], miny=bbox_2056[1],
        maxx=bbox_2056[2], maxy=bbox_2056[3],
        crs="EPSG:2056",
    )
    arr = ds_clipped.squeeze("band", drop=True).values.astype(np.float32)

    # Apply nodata mask manually from raster metadata
    nodata = ds.rio.nodata
    if nodata is not None:
        arr[arr == nodata] = np.nan
    # Also mask obviously invalid sentinel values (< -100 m or > 500 m)
    arr[(arr < -100) | (arr > 500)] = np.nan

    return ds_clipped.squeeze("band", drop=True), arr


@st.cache_data(ttl=3600, show_spinner=False)
def has_data(collection_key: str, year: int,
             bbox_2056: tuple[float, float, float, float]) -> bool:
    """
    Check whether a COG has a valid canopy-height value at the center of the bbox.

    Reads a single pixel via HTTP range request — fast enough to run in parallel
    for all candidate years.  The STAC geometry intersection (years_in_area) already
    removes obvious misses; this catch remaining edge cases (nodata at exact location).
    """
    import rasterio
    import rasterio.windows

    url = cog_url(collection_key, year)
    cx = (bbox_2056[0] + bbox_2056[2]) / 2
    cy = (bbox_2056[1] + bbox_2056[3]) / 2
    try:
        with rasterio.open(url) as src:
            row, col = src.index(cx, cy)
            win = rasterio.windows.Window(col, row, 1, 1)
            val = src.read(1, window=win).astype(np.float32)[0, 0]
            nd = src.nodata
            if nd is not None and val == nd:
                return False
            return -100.0 <= float(val) <= 500.0
    except Exception:
        return False


# ── Raster reading ────────────────────────────────────────────────────────────

def read_window(collection_key: str, year: int,
                bbox_2056: tuple[float, float, float, float]):
    """
    Read a full-resolution windowed region from a COG.
    Returns an xarray DataArray (EPSG:2056) with nodata → NaN.
    """
    url = cog_url(collection_key, year)
    da, arr = _open_and_clip(url, bbox_2056)
    # Return a DataArray that carries the spatial metadata but uses our clean arr
    return da.copy(data=arr)


# ── Forest mask (swissTLM3D Wald) ────────────────────────────────────────────

# Attempt 1: swisstopo MapServer REST (ArcGIS format) on api3.geo.admin.ch.
# This uses a completely different URL and query format than WFS and is more
# reliably accessible from US-hosted cloud providers.
_MAPSERVER_URL = (
    "https://api3.geo.admin.ch/rest/services/all/MapServer/"
    "ch.swisstopo.swisstlm3d-wald/query"
)

# Attempt 2: OpenStreetMap Overpass (global CDN, always reachable from cloud).
# Swiss forest data in OSM is very complete (landuse=forest / natural=wood).
_OVERPASS_URL = "https://overpass-api.de/api/interpreter"


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_forest_mask(bbox_2056: tuple, out_shape: tuple,
                      raster_bounds: tuple, bbox_wgs84: tuple) -> np.ndarray:
    """
    Fetch swissTLM3D Wald polygons and rasterize them onto the raster grid.
    Returns a boolean array: True = forest.

    Strategy (each attempt is tried in order; first success wins):
      1. swisstopo MapServer REST API (api3.geo.admin.ch, ArcGIS/GeoJSON format)
      2. OpenStreetMap Overpass API (globally reachable; landuse=forest + natural=wood)
      3. all-True fallback so the tool still produces a result

    bbox_2056   : (minx, miny, maxx, maxy) in LV95
    out_shape   : (height, width) of the target raster
    raster_bounds : actual raster bounds from da.rio.bounds()
    bbox_wgs84  : (minx, miny, maxx, maxy) in WGS84 — used by OSM Overpass
    """
    from rasterio.features import rasterize
    from rasterio.transform import from_bounds as rio_from_bounds

    geoms_lv95 = None  # list[Shapely geometry] in LV95, or None if attempt failed
    _errors: list[str] = []

    # ── Attempt 1: swisstopo MapServer REST (LV95 in, LV95 out) ──────────────
    # geo.admin.ch uses `sr` (not `inSR`/`outSR`) for the spatial reference.
    try:
        minx, miny, maxx, maxy = bbox_2056
        resp = requests.get(
            _MAPSERVER_URL,
            params={
                "geometryType": "esriGeometryEnvelope",
                "geometry": f"{minx},{miny},{maxx},{maxy}",
                "sr": "2056",
                "spatialRel": "esriSpatialRelIntersects",
                "returnGeometry": "true",
                "outFields": "*",
                "f": "geojson",
                "resultRecordCount": "5000",
            },
            timeout=30,
        )
        resp.raise_for_status()
        features = resp.json().get("features", [])
        if features:
            geoms_lv95 = [
                shape(feat["geometry"])
                for feat in features
                if feat.get("geometry")
            ]
            _errors.append(f"MapServer: OK ({len(geoms_lv95)} polygons)")
        else:
            _errors.append("MapServer: 0 features returned")
    except Exception as e:
        _errors.append(f"MapServer: {e}")

    # ── Attempt 2: OpenStreetMap Overpass mirrors (GET, [out:json] + out geom) ─
    _OVERPASS_MIRRORS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    ]
    if not geoms_lv95:  # also try Overpass when MapServer returned 0 features
        from shapely.geometry import Polygon as _Polygon
        west, south, east, north = bbox_wgs84
        query = (
            f"[out:json][timeout:30];\n"
            f"(\n"
            f'  way["landuse"="forest"]({south},{west},{north},{east});\n'
            f'  way["natural"="wood"]({south},{west},{north},{east});\n'
            f");\nout geom;"
        )
        for mirror in _OVERPASS_MIRRORS:
            try:
                resp = requests.get(
                    mirror,
                    params={"data": query},
                    headers={"Accept": "application/json"},
                    timeout=35,
                )
                resp.raise_for_status()
                geoms_wgs84 = []
                for el in resp.json().get("elements", []):
                    pts = el.get("geometry", [])
                    if len(pts) >= 3:
                        try:
                            geoms_wgs84.append(
                                _Polygon([(p["lon"], p["lat"]) for p in pts])
                            )
                        except Exception:
                            pass
                geoms_lv95 = [
                    shapely_transform(lambda x, y: _to_2056.transform(x, y), g)
                    for g in geoms_wgs84
                ]
                break  # success — stop trying mirrors
            except Exception as e:
                _errors.append(f"Overpass ({mirror}): {e}")

    if geoms_lv95 is None:
        st.warning(
            "Waldmaske konnte nicht geladen werden. Berechnung ohne Waldmaske.\n\n"
            + " | ".join(_errors)
        )
        return np.ones(out_shape, dtype=bool)

    if not geoms_lv95:
        return np.zeros(out_shape, dtype=bool)  # no forest in area

    height, width = out_shape
    transform = rio_from_bounds(*raster_bounds, width=width, height=height)
    mask = rasterize(
        [(g, 1) for g in geoms_lv95],
        out_shape=out_shape,
        transform=transform,
        fill=0,
        dtype=np.uint8,
    )
    return mask.astype(bool)


# ── Coarse preview ────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def read_window_preview(collection_key: str, year: int,
                        bbox_2056: tuple,
                        target_px: int = 400) -> np.ndarray | None:
    """
    Read a preview of the COG window at a consistent target resolution.

    Uses rasterio's out_shape to request exactly ~target_px pixels on the
    longest side, regardless of the file's native resolution or overview
    structure — so previews for different years are always comparable.
    """
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.windows import from_bounds as window_from_bounds

    url = cog_url(collection_key, year)
    try:
        with rasterio.open(url) as src:
            win = window_from_bounds(*bbox_2056, transform=src.transform)
            native_h = max(1, int(round(win.height)))
            native_w = max(1, int(round(win.width)))
            scale = max(1, max(native_h, native_w) / target_px)
            out_h = max(1, int(native_h / scale))
            out_w = max(1, int(native_w / scale))

            arr = src.read(
                1,
                window=win,
                out_shape=(out_h, out_w),
                resampling=Resampling.average,
            ).astype(np.float32)

            nodata = src.nodata
            if nodata is not None:
                arr[arr == nodata] = np.nan
            arr[(arr < -100) | (arr > 500)] = np.nan
            return arr
    except Exception:
        return None


def _raster_fig(arr, title: str):
    """Return a matplotlib Figure for a single-band float32 array."""
    valid = arr[np.isfinite(arr)] if arr is not None else np.array([])
    fig, ax = plt.subplots(figsize=(4, 3.5))
    if valid.size > 0:
        vmin, vmax = np.percentile(valid, 2), np.percentile(valid, 98)
        im = ax.imshow(arr, cmap="Greens", vmin=vmin, vmax=vmax,
                       interpolation="nearest")
        fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02).set_label("m", fontsize=8)
    else:
        ax.text(0.5, 0.5, "Keine Daten", ha="center", va="center",
                transform=ax.transAxes, fontsize=10, color="red")
    ax.set_title(title, fontsize=9)
    ax.set_axis_off()
    return fig


def compute_difference(da_new, da_old):
    """
    Subtract old from new (new – old) aligned on common grid.

    Both inputs are EPSG:2056 at the same pixel size, so clip results differ
    by at most one pixel due to origin alignment.  xr.align with join="inner"
    finds the shared coordinate intersection without any reproject / fill-value
    round-trip that could wipe valid pixels.
    """
    import xarray as xr

    da_new_a, da_old_a = xr.align(da_new, da_old, join="inner")

    if da_new_a.size == 0:
        raise ValueError(
            "Die räumlichen Ausschnitte der beiden Jahrgänge überlappen sich nicht."
        )

    arr_new = da_new_a.values.astype(np.float32)
    arr_old = da_old_a.values.astype(np.float32)

    diff = arr_new - arr_old
    # Wherever either input is NaN (NoData), the difference is undefined
    diff[~np.isfinite(arr_new) | ~np.isfinite(arr_old)] = np.nan

    return da_new_a.copy(data=diff)


# ── Colorized GeoTIFF output ──────────────────────────────────────────────────

def build_colorized_geotiff(diff_da) -> bytes:
    """
    Apply a diverging red–white–green colormap to a difference DataArray and
    write an RGBA cloud-optimized GeoTIFF in memory. Returns raw bytes.
    """
    data = diff_da.values.astype(np.float32)
    nodata_mask = ~np.isfinite(data)

    # Symmetric stretch: 5th–95th percentile of valid pixels, min ±0.5 m
    valid = data[~nodata_mask]
    if valid.size == 0:
        raise ValueError("No valid pixels in the computed difference raster.")

    abs_max = max(float(np.percentile(np.abs(valid), 95)), 0.5)

    # Normalize to [0, 1] where 0.5 = no change
    norm = mcolors.TwoSlopeNorm(vmin=-abs_max, vcenter=0.0, vmax=abs_max)
    normed = norm(np.clip(data, -abs_max, abs_max))

    # Red–white–green colormap
    cmap = plt.get_cmap("RdYlGn")
    rgba = cmap(normed)  # shape (H, W, 4), float64 in [0,1]

    # Apply NoData as fully transparent
    rgba[nodata_mask, 3] = 0.0

    # Convert to uint8
    rgba_uint8 = (rgba * 255).astype(np.uint8)

    import rasterio
    from rasterio.transform import from_bounds

    height, width = data.shape
    bounds = diff_da.rio.bounds()
    transform = from_bounds(*bounds, width=width, height=height)
    crs = CRS.from_epsg(2056)

    buf = io.BytesIO()
    with rasterio.open(
        buf,
        mode="w",
        driver="GTiff",
        height=height,
        width=width,
        count=4,
        dtype="uint8",
        crs=crs,
        transform=transform,
        compress="deflate",
    ) as dst:
        for i in range(4):
            dst.write(rgba_uint8[:, :, i], i + 1)

    buf.seek(0)
    return buf.read()


def build_raw_geotiff(diff_da) -> bytes:
    """
    Write the raw float32 difference raster as a GeoTIFF (EPSG:2056, single band).
    NoData = NaN. Returns raw bytes.
    """
    import rasterio
    from rasterio.transform import from_bounds

    data = diff_da.values.astype(np.float32)
    height, width = data.shape
    bounds = diff_da.rio.bounds()
    from rasterio.transform import from_bounds
    transform = from_bounds(*bounds, width=width, height=height)
    crs = CRS.from_epsg(2056)

    buf = io.BytesIO()
    with rasterio.open(
        buf,
        mode="w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs=crs,
        transform=transform,
        nodata=np.nan,
        compress="deflate",
    ) as dst:
        dst.write(data, 1)

    buf.seek(0)
    return buf.read()


# ── Streamlit UI ──────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Canopy Height Change Map",
        page_icon="🌲",
        layout="wide",
    )

    st.title("🌲 Canopy Height Change Map")
    st.markdown(
        "Zeichne ein Gebiet auf der Karte (max. 10 km²), wähle zwei Erhebungsjahre "
        "und berechne die Höhenveränderung des Waldes."
    )
    st.markdown("---")

    # ── Step 1: Map drawing ───────────────────────────────────────────────────
    st.subheader("1 · Gebiet einzeichnen")
    st.caption(
        "Verwende das Rechteck- oder Polygon-Werkzeug. "
        "Maximal 10 km² (ca. 3,2 km × 3,2 km)."
    )

    m = folium.Map(location=CH_CENTER, zoom_start=CH_ZOOM, tiles="CartoDB positron")
    folium.TileLayer(
        tiles="https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.swissimage-product/"
              "default/current/3857/{z}/{x}/{y}.jpeg",
        attr="© swisstopo",
        name="SWISSIMAGE",
        overlay=False,
    ).add_to(m)
    folium.LayerControl().add_to(m)

    Draw(
        draw_options={
            "polyline": False,
            "circle": False,
            "marker": False,
            "circlemarker": False,
            "polygon": True,
            "rectangle": True,
        },
        edit_options={"edit": True},
    ).add_to(m)

    map_result = st_folium(m, width="100%", height=480, returned_objects=["all_drawings"])

    # Parse drawn geometry
    drawn_poly = None
    area = None
    drawings = (map_result or {}).get("all_drawings") or []
    if drawings:
        last = drawings[-1]
        geom = last.get("geometry")
        if geom:
            try:
                drawn_poly = geojson_to_shapely(geom)
                area = area_m2(drawn_poly)
            except Exception as e:
                st.error(f"Geometrie konnte nicht verarbeitet werden: {e}")

    if drawn_poly is None:
        st.info("Bitte zeichne ein Gebiet auf der Karte ein.")
        st.stop()

    area_km2 = area / 1_000_000
    if area > MAX_AREA_M2:
        st.error(
            f"Das eingezeichnete Gebiet ist zu gross ({area_km2:.2f} km²). "
            "Bitte wähle ein Gebiet von maximal 10 km²."
        )
        st.stop()

    st.success(f"Gebiet: **{area_km2:.3f} km²** ✓")
    bbox_2056 = polygon_to_lv95_bbox(drawn_poly)

    # ── Step 2: Query available years ─────────────────────────────────────────
    st.markdown("---")
    st.subheader("2 · Verfügbare Datensätze prüfen")

    with st.spinner("Verfügbare Erhebungsjahre werden abgefragt…"):
        lidar_items = fetch_stac_items("lidar")
        stereo_items = fetch_stac_items("stereo")

    if not stereo_items:
        st.error(
            "Die STAC-Datenbank ist nicht erreichbar. "
            "Bitte später erneut versuchen."
        )
        st.stop()

    # For each collection: first filter by STAC bbox, then do a real data spot-check
    lidar_years_bbox  = years_in_area(lidar_items,  drawn_poly)
    stereo_years_bbox = years_in_area(stereo_items, drawn_poly)

    all_to_check = (
        [("lidar",  y) for y in lidar_years_bbox] +
        [("stereo", y) for y in stereo_years_bbox]
    )

    with st.spinner("Datenabdeckung wird geprüft…"):
        prog = st.progress(0)
        covered: dict[str, list[int]] = {}
        done_count = 0
        total = max(len(all_to_check), 1)

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {
                pool.submit(has_data, ck, yr, bbox_2056): (ck, yr)
                for ck, yr in all_to_check
            }
            for fut in as_completed(futures):
                ck, yr = futures[fut]
                if fut.result():
                    covered.setdefault(ck, []).append(yr)
                done_count += 1
                prog.progress(done_count / total)
        prog.empty()

    lidar_covered  = sorted(covered.get("lidar",  []))
    stereo_covered = sorted(covered.get("stereo", []))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**VHM LiDAR** (0,5 m) — Jahre mit Daten im Gebiet:")
        if lidar_covered:
            st.write(", ".join(str(y) for y in lidar_covered))
        else:
            st.caption("Kein LiDAR im gewählten Gebiet.")
    with col2:
        st.markdown("**VHM Stereo** (1 m) — Jahre mit Daten im Gebiet:")
        if stereo_covered:
            st.write(", ".join(str(y) for y in stereo_covered))
        else:
            st.caption("Keine Stereo-Daten im gewählten Gebiet.")

    # ── Step 3: Year selection ────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("3 · Erhebungsjahre wählen")

    all_years_sorted = sorted(set(lidar_covered) | set(stereo_covered))
    if not all_years_sorted:
        st.warning("Für das gewählte Gebiet sind keine Daten verfügbar.")
        st.stop()

    if len(all_years_sorted) < 2:
        st.warning(
            "Für das gewählte Gebiet ist nur ein Datensatz verfügbar — "
            "für eine Differenzberechnung werden mindestens zwei Jahre benötigt."
        )
        st.stop()

    col_a, col_b = st.columns(2)
    with col_a:
        year_a = st.selectbox(
            "Jahr A (älter / Referenz)",
            options=all_years_sorted[:-1],
            index=0,
            key="year_a",
        )
    with col_b:
        later_years = [y for y in all_years_sorted if y > year_a]
        year_b = st.selectbox(
            "Jahr B (neuer / Vergleich)",
            options=later_years,
            index=len(later_years) - 1,
            key="year_b",
        )

    # Decide which collection to use
    use_lidar = (year_a in lidar_covered) and (year_b in lidar_covered)
    # Only use Stereo if at least one year falls back
    if not use_lidar and (year_a not in stereo_covered or year_b not in stereo_covered):
        st.warning(
            "Für die gewählte Kombination sind nicht für beide Jahre Daten verfügbar. "
            "Bitte eine andere Jahreskombination wählen."
        )
        st.stop()
    collection_key = "lidar" if use_lidar else "stereo"
    res_label = "0,5 m (LiDAR)" if use_lidar else "1 m (Stereo)"

    st.info(
        f"**Datensatz:** VHM {'LiDAR' if use_lidar else 'Stereo'} · "
        f"Auflösung: {res_label} · "
        f"Differenz: {year_b} − {year_a}"
    )
    if not use_lidar and (year_a in lidar_covered or year_b in lidar_covered):
        st.caption(
            "LiDAR steht nicht für beide Jahre zur Verfügung → "
            "es wird für beide Jahre das Stereo-Modell verwendet."
        )

    # ── Auto-preview after year selection ─────────────────────────────────────
    st.markdown("**Vorschau der gewählten Höhenmodelle**")
    prev_col_a, prev_col_b = st.columns(2)
    with prev_col_a:
        with st.spinner(f"Vorschau {year_a}…"):
            arr_prev_a = read_window_preview(collection_key, year_a, bbox_2056)
        fig_a = _raster_fig(arr_prev_a, f"VHM {year_a} ({'LiDAR' if use_lidar else 'Stereo'})")
        st.pyplot(fig_a)
        plt.close(fig_a)
    with prev_col_b:
        with st.spinner(f"Vorschau {year_b}…"):
            arr_prev_b = read_window_preview(collection_key, year_b, bbox_2056)
        fig_b = _raster_fig(arr_prev_b, f"VHM {year_b} ({'LiDAR' if use_lidar else 'Stereo'})")
        st.pyplot(fig_b)
        plt.close(fig_b)

    # ── Step 4: Calculate ─────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("4 · Berechnen")

    if st.button("🔢 Höhenveränderung berechnen", type="primary"):
        with st.spinner(f"Daten für {year_a} werden gelesen…"):
            try:
                da_a = read_window(collection_key, year_a, bbox_2056)
            except Exception as e:
                st.error(f"Fehler beim Lesen von Jahr {year_a}: {e}")
                st.stop()

        valid_a = int(np.sum(np.isfinite(da_a.values)))
        if valid_a == 0:
            st.error(
                f"Jahr {year_a}: Raster wurde gelesen, enthält aber keine gültigen Pixel "
                f"(shape={da_a.shape}). Möglicherweise liegt das Gebiet ausserhalb der Abdeckung."
            )
            st.stop()

        with st.spinner(f"Daten für {year_b} werden gelesen…"):
            try:
                da_b = read_window(collection_key, year_b, bbox_2056)
            except Exception as e:
                st.error(f"Fehler beim Lesen von Jahr {year_b}: {e}")
                st.stop()

        valid_b = int(np.sum(np.isfinite(da_b.values)))
        if valid_b == 0:
            st.error(
                f"Jahr {year_b}: Raster wurde gelesen, enthält aber keine gültigen Pixel "
                f"(shape={da_b.shape}). Möglicherweise liegt das Gebiet ausserhalb der Abdeckung."
            )
            st.stop()

        # ── Forest mask ───────────────────────────────────────────────────────
        with st.spinner("Waldmaske (swissTLM3D) wird geladen…"):
            raster_bounds = da_a.rio.bounds()  # (minx, miny, maxx, maxy)
            forest_mask = fetch_forest_mask(
                bbox_2056,
                out_shape=da_a.shape,
                raster_bounds=raster_bounds,
                bbox_wgs84=tuple(drawn_poly.bounds),
            )

        n_forest = int(np.sum(forest_mask))
        st.caption(
            f"Waldmaske: {n_forest:,} von {da_a.size:,} Pixeln als Waldfläche klassiert."
        )

        # Apply mask: non-forest → NaN in both rasters
        arr_a = da_a.values.astype(np.float32)
        arr_b = da_b.values.astype(np.float32)
        arr_a[~forest_mask] = np.nan
        arr_b[~forest_mask] = np.nan
        da_a = da_a.copy(data=arr_a)
        da_b = da_b.copy(data=arr_b)

        with st.spinner("Differenz wird berechnet…"):
            diff = compute_difference(da_b, da_a)

        with st.spinner("GeoTIFF wird erstellt…"):
            try:
                tiff_colored = build_colorized_geotiff(diff)
                tiff_raw = build_raw_geotiff(diff)
            except ValueError as e:
                st.error(str(e))
                st.stop()

        # Store results in session state so they survive reruns.
        # Use "_res_" prefix to avoid colliding with widget keys "year_a"/"year_b".
        st.session_state["diff"] = diff
        st.session_state["tiff_colored"] = tiff_colored
        st.session_state["tiff_raw"] = tiff_raw
        st.session_state["_res_year_a"] = year_a
        st.session_state["_res_year_b"] = year_b
        st.session_state["_res_collection_key"] = collection_key

    # ── Step 5: Results & download ────────────────────────────────────────────
    if "diff" in st.session_state:
        diff = st.session_state["diff"]
        ya = st.session_state["_res_year_a"]
        yb = st.session_state["_res_year_b"]
        ck = st.session_state["_res_collection_key"]

        st.markdown("---")
        st.subheader("5 · Ergebnis")

        # Quick statistics
        vals = diff.values.astype(np.float32)
        valid_vals = vals[np.isfinite(vals)]

        if valid_vals.size > 0:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Mittlere Änderung", f"{np.mean(valid_vals):.2f} m")
            col2.metric("Median", f"{np.median(valid_vals):.2f} m")
            col3.metric("Max. Zuwachs", f"+{np.max(valid_vals):.2f} m",
                        help="Sehr hohe Werte können auf singuläre Artefakte zurückzuführen sein.")
            col4.metric("Max. Abnahme", f"{np.min(valid_vals):.2f} m")

        # Inline preview (matplotlib figure → st.image)
        abs_max = max(float(np.percentile(np.abs(valid_vals), 95)), 0.5)
        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(
            vals,
            cmap="RdYlGn",
            vmin=-abs_max,
            vmax=abs_max,
            interpolation="nearest",
        )
        ax.set_axis_off()
        cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
        cbar.set_label("Höhenveränderung (m)", fontsize=9)
        ax.set_title(
            f"VHM {'LiDAR' if ck == 'lidar' else 'Stereo'} · {yb} – {ya}",
            fontsize=10,
        )
        st.pyplot(fig)
        plt.close(fig)

        # Download buttons
        fname_base = f"vhm_change_{ck}_{ya}_{yb}"
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="⬇ GeoTIFF herunterladen (farbig, RGBA)",
                data=st.session_state["tiff_colored"],
                file_name=f"{fname_base}_colored.tif",
                mime="image/tiff",
            )
        with col_dl2:
            st.download_button(
                label="⬇ GeoTIFF herunterladen (Rohwerte, float32)",
                data=st.session_state["tiff_raw"],
                file_name=f"{fname_base}_raw.tif",
                mime="image/tiff",
            )

        st.caption(
            f"Koordinatensystem: EPSG:2056 (LV95) · "
            f"Auflösung: {'0,5 m' if ck == 'lidar' else '1 m'} · "
            f"Quelle: BAFU / WSL via data.geo.admin.ch"
        )

    st.markdown("---")
    st.caption(
        "Datenquellen: Vegetationshöhenmodell LiDAR LFI & Vegetationshöhenmodell LFI "
        "(BAFU / WSL / swisstopo) — [data.geo.admin.ch](https://data.geo.admin.ch) — "
        "Frei verfügbare Geodaten der Schweiz."
    )


if __name__ == "__main__":
    main()
