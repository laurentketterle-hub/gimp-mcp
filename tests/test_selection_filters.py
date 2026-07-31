"""Tests for selection tools and emboss filter (issues #4, #7)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from gimp_mcp.backend.mock import MockBackend
from gimp_mcp import ops


@pytest.fixture
def backend() -> MockBackend:
    return MockBackend()


@pytest.fixture
def tmp_image(backend: MockBackend) -> str:
    """Create a 200×200 RGB test image and return its id."""
    im = Image.new("RGB", (200, 200), "#ffffff")
    im.paste("#0000ff", (50, 50, 150, 150))
    path = Path(backend._ws) / "test_input.png"
    im.save(path)
    img = backend.open_image(str(path))
    assert img["ok"]
    return img["image"]["id"]


@pytest.fixture
def selected_image(backend: MockBackend, tmp_image: str) -> str:
    """Image with an active rectangular selection."""
    r = backend.select_rect(tmp_image, 10, 20, 60, 40)
    assert r["ok"]
    return tmp_image


# ------------------------------------------------------------------
# Selection: select_rect
# ------------------------------------------------------------------

class TestSelectRect:
    def test_select_returns_ok(self, backend: MockBackend, tmp_image: str) -> None:
        r = backend.select_rect(tmp_image, 10, 20, 30, 40)
        assert r["ok"] is True
        assert r["selection"]["x"] == 10
        assert r["selection"]["y"] == 20
        assert r["selection"]["width"] == 30
        assert r["selection"]["height"] == 40

    def test_select_negative_width_clamps(self, backend: MockBackend, tmp_image: str) -> None:
        r = backend.select_rect(tmp_image, 0, 0, -5, 10)
        assert r["selection"]["width"] >= 1

    def test_select_unknown_image(self, backend: MockBackend) -> None:
        r = backend.select_rect("nope", 0, 0, 10, 10)
        assert r["ok"] is False


# ------------------------------------------------------------------
# Selection: get_selection
# ------------------------------------------------------------------

class TestGetSelection:
    def test_no_selection_by_default(self, backend: MockBackend, tmp_image: str) -> None:
        r = backend.get_selection(tmp_image)
        assert r["ok"]
        assert r["active"] is False
        assert r["selection"] is None

    def test_unknown_image(self, backend: MockBackend) -> None:
        r = backend.get_selection("nope")
        assert r["ok"] is False


class TestGetSelectionIntegration:
    def test_roundtrip(self, backend: MockBackend) -> None:
        im = Image.new("RGB", (100, 100), "#ffffff")
        p = backend._ws / "g_sel.png"
        im.save(p)
        img = backend.open_image(str(p))
        assert img["ok"]
        iid = img["image"]["id"]

        g = backend.get_selection(iid)
        assert g["ok"] and g["active"] is False

        s = backend.select_rect(iid, 5, 10, 20, 30)
        assert s["ok"]

        g = backend.get_selection(iid)
        assert g["ok"] and g["active"] is True
        assert g["selection"]["width"] == 20


# ------------------------------------------------------------------
# Selection: fill_selection
# ------------------------------------------------------------------

class TestFillSelection:
    def test_fill_no_selection(self, backend: MockBackend, tmp_image: str) -> None:
        r = backend.fill_selection(tmp_image)
        assert r["ok"] is False
        assert "no active selection" in r["error"]

    def test_fill_red(self, backend: MockBackend, selected_image: str) -> None:
        r = backend.fill_selection(selected_image, color="#ff0000")
        assert r["ok"] is True
        assert r["selection"]["width"] == 60
        im = Image.open(r["image"]["path"])
        pixels = list(im.crop((10, 20, 70, 60)).getdata())
        assert all(p == (255, 0, 0) for p in pixels)


class TestFillSelectionTransparent:
    def test_transparent_fill(self, backend: MockBackend, selected_image: str) -> None:
        backend._apply(selected_image, lambda im: im.convert("RGBA"))
        r = backend.fill_selection(selected_image, transparent=True)
        assert r["ok"] is True


# ------------------------------------------------------------------
# Selection: stroke_selection
# ------------------------------------------------------------------

class TestStrokeSelection:
    def test_stroke_no_selection(self, backend: MockBackend, tmp_image: str) -> None:
        r = backend.stroke_selection(tmp_image)
        assert r["ok"] is False
        assert "no active selection" in r["error"]

    def test_stroke_green(self, backend: MockBackend, selected_image: str) -> None:
        r = backend.stroke_selection(selected_image, color="#00ff00", line_width=2)
        assert r["ok"] is True
        assert r["selection"]["width"] == 60

    def test_stroke_default_line_width(self, backend: MockBackend, selected_image: str) -> None:
        r = backend.stroke_selection(selected_image)
        assert r["ok"] is True


# ------------------------------------------------------------------
# Selection: clear_selection
# ------------------------------------------------------------------

class TestClearSelection:
    def test_clear_active(self, backend: MockBackend, selected_image: str) -> None:
        r = backend.clear_selection(selected_image)
        assert r["ok"] is True
        assert r["cleared"] is True
        g = backend.get_selection(selected_image)
        assert g["active"] is False

    def test_clear_no_selection(self, backend: MockBackend, tmp_image: str) -> None:
        r = backend.clear_selection(tmp_image)
        assert r["ok"] is True
        assert r["cleared"] is False


# ------------------------------------------------------------------
# Ops: selection_fill / selection_stroke
# ------------------------------------------------------------------

class TestOpsSelection:
    def test_fill_rgba(self) -> None:
        im = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        out = ops.selection_fill(im, 10, 10, 20, 20, color="#0000ff")
        assert out.mode == "RGBA"
        assert out.getpixel((15, 15)) == (0, 0, 255, 255)

    def test_stroke_rgb(self) -> None:
        im = Image.new("RGB", (100, 100), (255, 255, 255))
        out = ops.selection_stroke(im, 10, 10, 20, 20, color="#000000", line_width=2)
        assert out.mode == "RGB"
        assert out.getpixel((20, 20)) == (255, 255, 255)


# ------------------------------------------------------------------
# Emboss filter
# ------------------------------------------------------------------

class TestEmboss:
    def test_emboss_rgb(self) -> None:
        im = Image.new("RGB", (100, 100), "#ffffff")
        im.paste("#000000", (30, 30, 70, 70))
        out = ops.emboss(im)
        assert out.size == im.size
        assert out.mode in ("RGB", "RGBA")

    def test_emboss_depth(self) -> None:
        im = Image.new("RGB", (50, 50), "#888888")
        out = ops.emboss(im, depth=10)
        assert out.size == (50, 50)

    def test_emboss_backend(self, backend: MockBackend) -> None:
        im = Image.new("RGB", (100, 100), "#ffffff")
        p = backend._ws / "emboss_test.png"
        im.save(p)
        img = backend.open_image(str(p))
        assert img["ok"]
        r = backend.emboss(img["image"]["id"])
        assert r["ok"] is True

    def test_emboss_rgba_preserves_alpha(self) -> None:
        im = Image.new("RGBA", (50, 50), (255, 255, 255, 128))
        out = ops.emboss(im)
        assert out.mode == "RGBA"
        a = out.getpixel((25, 25))[-1]
        assert a == 128

    def test_emboss_unknown_image(self, backend: MockBackend) -> None:
        r = backend.emboss("nope")
        assert r["ok"] is False
