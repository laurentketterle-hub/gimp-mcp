"""Tests for selection tools (issue #7)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from gimp_mcp.ops import selection_rectangular, fill_selection, stroke_selection
from gimp_mcp.backend.mock import MockBackend


class TestSelectionRectangular:
    def setup_method(self):
        self.mock = MockBackend()
        self.mock.create_image("test", 800, 600)

    def test_basic(self):
        result = selection_rectangular("1", 10, 20, 200, 150)
        assert result["op"] == "selection_rectangular"
        assert result["x"] == 10
        assert result["width"] == 200

    def test_mock_stores_selection(self):
        result = self.mock.selection_rectangular("1", 50, 50, 300, 200)
        assert result["op"] == "selection_rectangular"
        assert self.mock._selection is not None

    def test_negative_coords_allowed(self):
        result = selection_rectangular("1", -5, -10, 100, 100)
        assert result["op"] == "selection_rectangular"


class TestFillSelection:
    def setup_method(self):
        self.mock = MockBackend()
        self.mock.create_image("test", 800, 600)

    def test_fill_after_selection(self):
        self.mock.selection_rectangular("1", 0, 0, 100, 100)
        result = fill_selection("1", "#ff0000")
        assert result["op"] == "fill_selection"

    def test_fill_no_selection(self):
        result = self.mock.fill_selection("1", "#00ff00")
        assert result["op"] == "fill_selection"

    def test_fill_default_color(self):
        self.mock.selection_rectangular("1", 0, 0, 50, 50)
        result = fill_selection("1")
        assert result["op"] == "fill_selection"


class TestStrokeSelection:
    def setup_method(self):
        self.mock = MockBackend()
        self.mock.create_image("test", 800, 600)

    def test_stroke_after_selection(self):
        self.mock.selection_rectangular("1", 10, 10, 150, 150)
        result = stroke_selection("1", "#0000ff", 3)
        assert result["op"] == "stroke_selection"
        assert result.get("width") == 3

    def test_stroke_default_width(self):
        self.mock.selection_rectangular("1", 0, 0, 200, 200)
        result = stroke_selection("1", "#ffff00")
        assert result["op"] == "stroke_selection"

    def test_stroke_no_selection(self):
        result = self.mock.stroke_selection("1", "#ffffff", 1)
        assert result["op"] == "stroke_selection"


class TestSelectionChain:
    def setup_method(self):
        self.mock = MockBackend()
        self.mock.create_image("test", 800, 600)

    def test_full_chain(self):
        r1 = self.mock.selection_rectangular("1", 0, 0, 300, 300)
        r2 = self.mock.fill_selection("1", "#333333")
        r3 = self.mock.stroke_selection("1", "#ffffff", 2)
        ops = [r["op"] for r in (r1, r2, r3)]
        assert "selection_rectangular" in ops
        assert "fill_selection" in ops
        assert "stroke_selection" in ops
