"""
Layer-style image operations for clean cutouts (esp. gold logo on black).

Pipeline mental model:
  [RGB color layer]  +  [Alpha matte layer]  +  [Defringe]
  → RGBA without soft bloom / white haze on light backgrounds.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageFilter


def _as_float_rgba(im: Image.Image) -> np.ndarray:
    return np.array(im.convert("RGBA"), dtype=np.float32)


def unpremultiply_black(rgb: np.ndarray, alpha: np.ndarray, eps: float = 1e-3) -> np.ndarray:
    """
    Logo rendered on pure black is premultiplied: RGB = RGB_true * A.
    Recover straight RGB for cleaner edges when rematting.
    """
    a = np.clip(alpha / 255.0, 0.0, 1.0)[..., None]
    out = rgb.copy()
    mask = a[..., 0] > eps
    out[mask] = np.clip(rgb[mask] / np.maximum(a[mask], eps), 0, 255)
    out[~mask] = 0
    return out


def matte_from_luma(
    rgb: np.ndarray,
    thr: float = 48.0,
    soft: float = 8.0,
) -> np.ndarray:
    """Alpha matte layer from luminance (0..255). Small soft only for AA."""
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    if soft <= 0:
        return (luma >= thr).astype(np.float32) * 255.0
    return np.clip((luma - thr) / soft, 0.0, 1.0) * 255.0


def matte_from_gold(
    rgb: np.ndarray,
    thr: float = 40.0,
    soft: float = 10.0,
) -> np.ndarray:
    """Prefer warm gold pixels over gray haze."""
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    presence = np.maximum(np.maximum(r, g), b)
    gold = r * 0.55 + g * 0.45 - b * 0.35
    score = np.maximum(presence * 0.65 + gold * 0.55, 0)
    return np.clip((score - thr) / max(soft, 1e-3), 0.0, 1.0) * 255.0


def solidify_matte(alpha: np.ndarray, thr: float = 128.0) -> np.ndarray:
    """Hard matte layer (binary) — kills soft bloom bands."""
    return (alpha >= thr).astype(np.float32) * 255.0


def morph_matte(alpha_img: Image.Image, erode: int = 0, dilate: int = 0) -> Image.Image:
    """Morphology on matte via PIL Min/Max filters (odd sizes)."""
    a = alpha_img
    for _ in range(max(0, erode)):
        a = a.filter(ImageFilter.MinFilter(3))
    for _ in range(max(0, dilate)):
        a = a.filter(ImageFilter.MaxFilter(3))
    return a


def defringe(
    rgb: np.ndarray,
    alpha: np.ndarray,
    edge_lo: float = 20.0,
    edge_hi: float = 250.0,
    core_thr: float = 200.0,
    ring: int = 2,
) -> np.ndarray:
    """
    Color decontamination on matte edge.
    For hard (binary) mattes, edge = matte minus eroded matte (morphological ring).
    For soft mattes, also use partial-alpha band.
    """
    solid = alpha >= core_thr
    if not np.any(solid):
        solid = alpha > 128
    if not np.any(solid):
        return rgb

    # morphological interior (erode) via MinFilter
    a_im = Image.fromarray(np.clip(alpha, 0, 255).astype(np.uint8), "L")
    eroded = a_im
    for _ in range(max(1, int(ring))):
        eroded = eroded.filter(ImageFilter.MinFilter(3))
    eroded_a = np.array(eroded, dtype=np.float32)
    # edge ring of hard matte
    edge = (alpha >= 128) & (eroded_a < 128)
    # also soft partial band if present
    soft_edge = (alpha > edge_lo) & (alpha < edge_hi)
    edge = edge | soft_edge

    core = eroded_a >= core_thr
    if not np.any(core):
        core = solid
    mean_rgb = rgb[core].mean(axis=0)
    core_luma = float(0.299 * mean_rgb[0] + 0.587 * mean_rgb[1] + 0.114 * mean_rgb[2])
    out = rgb.copy()
    alpha_out = alpha.copy()
    if np.any(edge):
        edge_luma = 0.299 * out[edge, 0] + 0.587 * out[edge, 1] + 0.114 * out[edge, 2]
        # drop dark bloom rim entirely; recolor mid/bright edge to core gold
        dark = edge_luma < core_luma * 0.72
        edge_idx = np.where(edge)
        dark_idx = (
            edge_idx[0][dark],
            edge_idx[1][dark],
        )
        bright_edge = (
            edge_idx[0][~dark],
            edge_idx[1][~dark],
        )
        if len(dark_idx[0]):
            alpha_out[dark_idx] = 0
            out[dark_idx] = 0
        if len(bright_edge[0]):
            out[bright_edge] = mean_rgb
    # write alpha back if caller uses same buffer — return both via side channel
    # store on function for cutout_layers to pick up
    defringe.last_alpha = alpha_out  # type: ignore[attr-defined]
    return out


def antialias_matte(alpha: np.ndarray, radius: float = 0.8) -> np.ndarray:
    """Very slight blur on hard matte for 1px AA only."""
    if radius <= 0:
        return alpha
    im = Image.fromarray(alpha.astype(np.uint8), "L")
    im = im.filter(ImageFilter.GaussianBlur(radius=radius))
    return np.array(im, dtype=np.float32)


def cutout_layers(
    im: Image.Image,
    *,
    mode: str = "gold",
    thr: float = 42.0,
    soft: float = 6.0,
    hard: bool = True,
    hard_thr: float = 100.0,
    erode: int = 0,
    dilate: int = 0,
    defringe_on: bool = True,
    aa: float = 0.6,
    unpremult: bool = True,
) -> dict[str, Any]:
    """
    Layered cutout from black (or dark) background.

    Returns dict with:
      color  – RGB layer (straight)
      matte  – Alpha layer
      rgba   – composited result
      layers – intermediate debug names
    """
    arr = _as_float_rgba(im)
    rgb = arr[:, :, 0:3]
    src_a = arr[:, :, 3]
    # if already has alpha, use presence of color still
    if unpremult:
        # estimate premult alpha from luma for black-bg art
        est = matte_from_luma(rgb, thr=8.0, soft=12.0)
        rgb = unpremultiply_black(rgb, est)

    if mode == "luma":
        matte = matte_from_luma(rgb, thr=thr, soft=soft)
    else:
        matte = matte_from_gold(rgb, thr=thr, soft=soft)

    # combine with existing alpha if any
    matte = np.minimum(matte, src_a)

    matte_im = Image.fromarray(matte.astype(np.uint8), "L")
    matte_im = morph_matte(matte_im, erode=erode, dilate=dilate)
    matte = np.array(matte_im, dtype=np.float32)

    if hard:
        matte = solidify_matte(matte, thr=hard_thr)
        if aa > 0:
            matte = antialias_matte(matte, radius=aa)

    if defringe_on:
        rgb = defringe(rgb, matte, ring=3)
        # defringe may zero dark-rim alpha
        if hasattr(defringe, "last_alpha"):
            matte = np.minimum(matte, defringe.last_alpha)  # type: ignore[attr-defined]

    # zero rgb outside matte
    outside = matte < 4
    rgb[outside] = 0

    rgba = np.dstack([rgb, matte])
    out = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA")
    color_l = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")
    matte_l = Image.fromarray(np.clip(matte, 0, 255).astype(np.uint8), "L")
    return {
        "rgba": out,
        "color": color_l,
        "matte": matte_l,
        "ok": True,
        "mode": mode,
        "hard": hard,
    }


def export_layer_debug(result: dict[str, Any], prefix: Path) -> dict[str, str]:
    """Write color/matte/rgba layers for inspection."""
    paths = {}
    for key in ("color", "matte", "rgba"):
        if key in result and result[key] is not None:
            p = Path(str(prefix) + f"_{key}.png")
            result[key].save(p)
            paths[key] = str(p)
    return paths
