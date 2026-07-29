"""Comprehensive tests for selection operations: rect, ellipse, polygon,
fill, stroke, feather, grow, shrink, invert, point containment.
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from PIL import Image, ImageDraw

from gimp_mcp.selections import (
    Selection,
    create_rect_selection,
    create_ellipse_selection,
    create_polygon_selection,
    create_free_selection,
    fill_selection,
    stroke_selection,
    invert_selection,
    feather_selection,
    grow_selection,
    shrink_selection,
    _point_in_polygon,
)


@pytest.fixture
def rgb_img() -> Image.Image:
    return Image.new("RGB", (200, 200), (128, 128, 128))


@pytest.fixture
def rgba_img() -> Image.Image:
    return Image.new("RGBA", (200, 200), (128, 128, 128, 255))


# ── Selection creation ──


class TestRectSelection:
    def test_create_basic(self):
        sel = create_rect_selection(10, 20, 100, 50)
        assert sel.type == "rect"
        assert sel.x == 10
        assert sel.y == 20
        assert sel.width == 100
        assert sel.height == 50
        assert sel.feather == 0.0

    def test_create_with_feather(self):
        sel = create_rect_selection(10, 20, 100, 50, feather=5.0)
        assert sel.feather == 5.0

    def test_to_dict(self):
        sel = create_rect_selection(10, 20, 100, 50, feather=2.0)
        d = sel.to_dict()
        assert d["type"] == "rect"
        assert d["x"] == 10
        assert d["y"] == 20
        assert d["width"] == 100
        assert d["height"] == 50
        assert d["feather"] == 2.0

    def test_get_bounds(self):
        sel = create_rect_selection(10, 20, 100, 50)
        x, y, w, h = sel.get_bounds()
        assert (x, y, w, h) == (10, 20, 100, 50)

    def test_contains_point_inside(self):
        sel = create_rect_selection(10, 20, 100, 50)
        assert sel.contains_point(50, 40)

    def test_contains_point_outside(self):
        sel = create_rect_selection(10, 20, 100, 50)
        assert not sel.contains_point(5, 40)
        assert not sel.contains_point(120, 40)
        assert not sel.contains_point(50, 10)
        assert not sel.contains_point(50, 80)

    def test_contains_point_boundary(self):
        sel = create_rect_selection(10, 20, 100, 50)
        assert sel.contains_point(10, 20)  # top-left inside
        assert not sel.contains_point(110, 70)  # bottom-right outside

    def test_apply_mask(self, rgb_img):
        sel = create_rect_selection(50, 50, 100, 80)
        mask = sel.apply_mask(rgb_img)
        assert mask.size == rgb_img.size
        assert mask.mode == "L"
        # Inside selection should be white (255)
        assert mask.getpixel((80, 80)) == 255
        # Outside should be black (0)
        assert mask.getpixel((10, 10)) == 0


class TestEllipseSelection:
    def test_create_basic(self):
        sel = create_ellipse_selection(30, 40, 140, 120, feather=1.0)
        assert sel.type == "ellipse"
        assert sel.x == 30
        assert sel.y == 40
        assert sel.width == 140
        assert sel.height == 120
        assert sel.feather == 1.0

    def test_contains_point_center(self):
        sel = create_ellipse_selection(0, 0, 100, 100)
        assert sel.contains_point(50, 50)

    def test_contains_point_corner(self):
        sel = create_ellipse_selection(0, 0, 100, 100)
        assert not sel.contains_point(0, 0)
        assert not sel.contains_point(99, 0)
        assert not sel.contains_point(0, 99)
        assert not sel.contains_point(99, 99)

    def test_contains_point_edge(self):
        sel = create_ellipse_selection(0, 0, 100, 100)
        assert sel.contains_point(50, 5)
        assert sel.contains_point(50, 95)

    def test_get_bounds(self):
        sel = create_ellipse_selection(30, 40, 140, 120)
        x, y, w, h = sel.get_bounds()
        assert (x, y, w, h) == (30, 40, 140, 120)

    def test_apply_mask(self, rgb_img):
        sel = create_ellipse_selection(50, 50, 100, 100)
        mask = sel.apply_mask(rgb_img)
        assert mask.size == rgb_img.size
        # Center should be white
        assert mask.getpixel((100, 100)) == 255
        # Corner should be black
        assert mask.getpixel((55, 55)) == 0


class TestPolygonSelection:
    def test_create_triangle(self):
        points = [(50, 10), (90, 90), (10, 90)]
        sel = create_polygon_selection(points)
        assert sel.type == "polygon"
        assert len(sel.points) == 3

    def test_contains_point_inside_triangle(self):
        points = [(50, 10), (90, 90), (10, 90)]
        sel = create_polygon_selection(points)
        assert sel.contains_point(50, 70)

    def test_contains_point_outside_triangle(self):
        points = [(50, 10), (90, 90), (10, 90)]
        sel = create_polygon_selection(points)
        assert not sel.contains_point(50, 5)
        assert not sel.contains_point(95, 50)

    def test_contains_point_on_vertex(self):
        points = [(50, 10), (90, 90), (10, 90)]
        sel = create_polygon_selection(points)
        # Vertices are on the boundary, ray casting may include or exclude
        # depending on implementation
        result = sel.contains_point(50, 10)
        assert isinstance(result, bool)

    def test_free_selection_alias(self):
        points = [(10, 10), (50, 50), (30, 80)]
        free = create_free_selection(points)
        assert free.type == "polygon"
        assert free.points == points

    def test_empty_polygon_fallback(self):
        sel = create_polygon_selection([], feather=3.0)
        assert sel.type == "rect"
        assert sel.feather == 3.0

    def test_get_bounds(self):
        points = [(50, 10), (90, 90), (10, 90)]
        sel = create_polygon_selection(points)
        x, y, w, h = sel.get_bounds()
        assert x == 10
        assert y == 10
        assert w == 80
        assert h == 80

    def test_apply_mask_triangle(self, rgb_img):
        points = [(100, 30), (170, 170), (30, 170)]
        sel = create_polygon_selection(points)
        mask = sel.apply_mask(rgb_img)
        assert mask.getpixel((100, 150)) == 255  # inside
        assert mask.getpixel((100, 20)) == 0   # above


# ── Point-in-polygon helper ──


class TestPointInPolygon:
    def test_inside_square(self):
        square = [(10, 10), (90, 10), (90, 90), (10, 90)]
        assert _point_in_polygon(50, 50, square)
        assert not _point_in_polygon(5, 50, square)
        assert not _point_in_polygon(95, 50, square)

    def test_inside_triangle(self):
        tri = [(50, 0), (100, 100), (0, 100)]
        assert _point_in_polygon(50, 50, tri)
        assert not _point_in_polygon(50, -5, tri)

    def test_less_than_3_points(self):
        assert not _point_in_polygon(10, 10, [(0, 0), (100, 100)])
        assert not _point_in_polygon(10, 10, [])


# ── Fill selection ──


class TestFillSelection:
    def test_fill_rect_rgb(self, rgb_img):
        sel = create_rect_selection(20, 30, 100, 60)
        result = fill_selection(rgb_img, sel, color="#ff0000")
        assert result.size == rgb_img.size
        # Center of rect should be red
        assert result.getpixel((70, 60))[:3] == (255, 0, 0)
        # Outside should be gray
        assert result.getpixel((10, 10))[:3] == (128, 128, 128)

    def test_fill_rect_rgba(self, rgba_img):
        sel = create_rect_selection(20, 30, 100, 60)
        result = fill_selection(rgba_img, sel, color="#00ff00")
        assert result.getpixel((70, 60))[:3] == (0, 255, 0)

    def test_fill_ellipse(self, rgb_img):
        sel = create_ellipse_selection(50, 50, 100, 100)
        result = fill_selection(rgb_img, sel, color="#0000ff")
        # Center should be blue
        assert result.getpixel((100, 100))[:3] == (0, 0, 255)
        # Corner should be gray
        assert result.getpixel((10, 10))[:3] == (128, 128, 128)

    def test_fill_polygon(self, rgb_img):
        points = [(100, 30), (170, 170), (30, 170)]
        sel = create_polygon_selection(points)
        result = fill_selection(rgb_img, sel, color="#ffff00")
        # Center of triangle should be yellow
        assert result.getpixel((100, 150))[:3] == (255, 255, 0)
        # Above triangle should be gray
        assert result.getpixel((100, 20))[:3] == (128, 128, 128)

    def test_fill_with_blend(self, rgba_img):
        sel = create_rect_selection(50, 50, 100, 100)
        result = fill_selection(rgba_img, sel, color="#ff0000", blend=True, opacity=0.5)
        assert result.size == rgba_img.size

    def test_fill_retains_alpha(self, rgba_img):
        sel = create_rect_selection(10, 10, 50, 50)
        result = fill_selection(rgba_img, sel, color="#ff0000")
        # Outside alpha preserved
        assert result.getpixel((150, 150))[3] == 255


# ── Stroke selection ──


class TestStrokeSelection:
    def test_stroke_rect_rgb(self, rgb_img):
        sel = create_rect_selection(20, 30, 100, 60)
        result = stroke_selection(rgb_img, sel, color="#ff0000", width=3)
        # On outline
        assert result.getpixel((20, 30))[:3] == (255, 0, 0)
        # Inside (not on outline) should be gray
        assert result.getpixel((70, 60))[:3] == (128, 128, 128)

    def test_stroke_ellipse(self, rgb_img):
        sel = create_ellipse_selection(50, 50, 100, 100)
        result = stroke_selection(rgb_img, sel, color="#00ff00", width=2)
        assert result.size == rgb_img.size

    def test_stroke_polygon(self, rgb_img):
        points = [(100, 30), (170, 170), (30, 170)]
        sel = create_polygon_selection(points)
        result = stroke_selection(rgb_img, sel, color="#0000ff", width=2)
        assert result.size == rgb_img.size

    def test_stroke_with_dash(self, rgb_img):
        sel = create_rect_selection(20, 30, 100, 60)
        result = stroke_selection(rgb_img, sel, color="#ff0000", width=2, dash=(5, 5))
        assert result.size == rgb_img.size

    def test_stroke_rgba(self, rgba_img):
        sel = create_rect_selection(50, 50, 60, 40)
        result = stroke_selection(rgba_img, sel, color="#ff00ff", width=4)
        assert result.size == rgba_img.size
        assert result.mode == "RGBA"


# ── Selection modification ──


class TestSelectionModification:
    def test_grow(self):
        sel = create_rect_selection(50, 50, 100, 80)
        grown = grow_selection(sel, 10)
        assert grown.x == 40
        assert grown.y == 40
        assert grown.width == 120
        assert grown.height == 100

    def test_shrink(self):
        sel = create_rect_selection(50, 50, 100, 80)
        shrunk = shrink_selection(sel, 10)
        assert shrunk.x == 60
        assert shrunk.y == 60
        assert shrunk.width == 80
        assert shrunk.height == 60

    def test_shrink_minimum(self):
        sel = create_rect_selection(50, 50, 100, 80)
        shrunk = shrink_selection(sel, 200)
        assert shrunk.width == 1
        assert shrunk.height == 1

    def test_feather(self):
        sel = create_rect_selection(10, 10, 100, 100)
        feathered = feather_selection(sel, 5.5)
        assert feathered.feather == 5.5
        assert feathered.type == "rect"

    def test_invert_rect(self, rgb_img):
        sel = create_rect_selection(50, 50, 100, 80)
        inverted = invert_selection(rgb_img, sel)
        assert inverted.type == "rect"
        assert inverted.width == rgb_img.width
        assert inverted.height == rgb_img.height

    def test_invert_polygon(self, rgb_img):
        points = [(50, 10), (90, 90), (10, 90)]
        sel = create_polygon_selection(points)
        inverted = invert_selection(rgb_img, sel)
        assert inverted.width == rgb_img.width
        assert inverted.height == rgb_img.height


# ── Edge cases ──


class TestSelectionEdgeCases:
    def test_zero_size_rect(self):
        sel = create_rect_selection(0, 0, 0, 0)
        assert sel.to_dict()["width"] == 1
        assert sel.to_dict()["height"] == 1

    def test_negative_rect_gets_positive_size(self):
        sel = create_rect_selection(-10, -10, -5, -5)
        assert sel.width == 1
        assert sel.height == 1

    def test_large_feather(self):
        sel = create_rect_selection(0, 0, 100, 100, feather=99.0)
        assert sel.feather == 99.0

    def test_stroke_width_one(self, rgb_img):
        sel = create_rect_selection(30, 30, 50, 50)
        result = stroke_selection(rgb_img, sel, color="#ffffff", width=1)
        assert result.size == rgb_img.size

    def test_fill_transparent(self, rgba_img):
        sel = create_rect_selection(10, 10, 50, 50)
        result = fill_selection(rgba_img, sel, color="#000000", opacity=0.0)
        assert result.size == rgba_img.size

    def test_selection_with_points_empty_type(self):
        sel = Selection(sel_type="rect", points=[(1, 1), (2, 2)])
        d = sel.to_dict()
        assert "points" in d
        assert d["points"] == [(1, 1), (2, 2)]


# ── Integration: selection + pipeline-style chain ──


class TestSelectionPipeline:
    def test_fill_then_stroke(self, rgb_img):
        sel = create_rect_selection(20, 30, 100, 60)
        filled = fill_selection(rgb_img, sel, color="#ff0000")
        stroked = stroke_selection(filled, sel, color="#000000", width=3)
        # Center should still be red (fill preserved)
        assert stroked.getpixel((70, 60))[:3] == (255, 0, 0)
        # Outline should be black
        assert stroked.getpixel((20, 30))[:3] == (0, 0, 0)

    def test_grow_then_fill(self, rgb_img):
        sel = create_rect_selection(40, 40, 40, 40)
        grown = grow_selection(sel, 20)
        result = fill_selection(rgb_img, grown, color="#00ff00")
        # Original selection center
        assert result.getpixel((60, 60))[:3] == (0, 255, 0)
        # Grown area (was outside original, now inside)
        assert result.getpixel((30, 30))[:3] == (0, 255, 0)

    def test_shrink_then_stroke(self, rgb_img):
        sel = create_rect_selection(20, 30, 100, 60)
        shrunk = shrink_selection(sel, 15)
        result = stroke_selection(rgb_img, shrunk, color="#0000ff", width=2)
        assert result.size == rgb_img.size

    def test_feather_mask_blur(self, rgb_img):
        sel = create_rect_selection(50, 50, 100, 100, feather=10.0)
        mask = sel.apply_mask(rgb_img)
        # Edge pixels should have intermediate values due to feathering
        edge_val = mask.getpixel((50, 100))
        assert 0 < edge_val < 255  # Not fully 0 or 255 due to blur

    def test_multiple_selections_on_same_image(self, rgb_img):
        sel1 = create_rect_selection(10, 10, 50, 50)
        sel2 = create_ellipse_selection(80, 80, 80, 80)
        result = fill_selection(rgb_img, sel1, color="#ff0000")
        result = fill_selection(result, sel2, color="#0000ff")
        # sel1 region should be red
        assert result.getpixel((35, 35))[:3] == (255, 0, 0)
        # sel2 center should be blue
        assert result.getpixel((120, 120))[:3] == (0, 0, 255)
        # Between them should still be gray
        assert result.getpixel((65, 65))[:3] == (128, 128, 128)
