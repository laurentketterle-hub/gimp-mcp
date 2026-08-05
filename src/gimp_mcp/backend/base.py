from __future__ import annotations

from typing import Any, Protocol


class GimpBackend(Protocol):
    name: str

    def doctor(self) -> dict[str, Any]: ...
    def seed_demo(self) -> dict[str, Any]: ...
    def list_images(self) -> list[dict[str, Any]]: ...
    def close_image(self, image_id: str) -> dict[str, Any]: ...
    def new_image(self, width: int, height: int, color: str = "#ffffff") -> dict[str, Any]: ...
    def open_image(self, path: str) -> dict[str, Any]: ...
    def info(self, image_id: str) -> dict[str, Any]: ...
    def resize(self, image_id: str, width: int, height: int) -> dict[str, Any]: ...
    def thumbnail(
        self, image_id: str, max_width: int = 512, max_height: int = 512
    ) -> dict[str, Any]: ...
    def crop(
        self, image_id: str, x: int, y: int, width: int, height: int
    ) -> dict[str, Any]: ...
    def flip(self, image_id: str, direction: str = "horizontal") -> dict[str, Any]: ...
    def rotate(self, image_id: str, degrees: float = 90) -> dict[str, Any]: ...
    def blur(self, image_id: str, radius: float = 2.0) -> dict[str, Any]: ...
    def sharpen(
        self, image_id: str, percent: float = 150.0, radius: float = 2.0
    ) -> dict[str, Any]: ...
    def desaturate(self, image_id: str) -> dict[str, Any]: ...
    def invert(self, image_id: str) -> dict[str, Any]: ...
    def brightness(self, image_id: str, factor: float = 1.2) -> dict[str, Any]: ...
    def contrast(self, image_id: str, factor: float = 1.2) -> dict[str, Any]: ...
    def saturation(self, image_id: str, factor: float = 1.2) -> dict[str, Any]: ...
    def auto_orient(self, image_id: str) -> dict[str, Any]: ...
    def text_overlay(
        self,
        image_id: str,
        text: str,
        x: int = 10,
        y: int = 10,
        size: int = 32,
        color: str = "#000000",
    ) -> dict[str, Any]: ...
    def pipeline(self, image_id: str, steps: list[dict[str, Any]]) -> dict[str, Any]: ...
    def export(self, image_id: str, path: str, format: str | None = None) -> dict[str, Any]: ...
    def batch_resize(
        self, input_dir: str, output_dir: str, width: int, height: int
    ) -> dict[str, Any]: ...
    def list_layers(self, image_id: str) -> dict[str, Any]: ...
    def new_layer(self, image_id: str, name: str = "New Layer") -> dict[str, Any]: ...
    def flatten(self, image_id: str) -> dict[str, Any]: ...

    def select_rect(
        self,
        image_id: str,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> dict[str, Any]: ...
    def select_ellipse(
        self,
        image_id: str,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> dict[str, Any]: ...
    def select_polygon(
        self,
        image_id: str,
        points_json: str,
    ) -> dict[str, Any]: ...
    def select_all(self, image_id: str) -> dict[str, Any]: ...
    def select_none(self, image_id: str) -> dict[str, Any]: ...
    def get_selection(self, image_id: str) -> dict[str, Any]: ...
    def invert_selection(self, image_id: str) -> dict[str, Any]: ...
    def feather_selection(self, image_id: str, radius: float) -> dict[str, Any]: ...
    def grow_selection(self, image_id: str, pixels: int) -> dict[str, Any]: ...
    def shrink_selection(self, image_id: str, pixels: int) -> dict[str, Any]: ...
    def fill_selection(
        self, image_id: str, color: str = "#000000", transparent: bool = False
    ) -> dict[str, Any]: ...
    def stroke_selection(
        self,
        image_id: str,
        color: str = "#000000",
        line_width: int = 2,
    ) -> dict[str, Any]: ...
    def clear_selection(self, image_id: str) -> dict[str, Any]: ...
    def get_selection(self, image_id: str) -> dict[str, Any]: ...
    def emboss(self, image_id: str, depth: int = 3) -> dict[str, Any]: ...

    def _validate_image(self, image_id):
        if image_id not in self._images:
            raise KeyError(f"Image {image_id} not found")
        return self._images[image_id]

    def _validate_color(self, color):
        if not isinstance(color, str) or not color.startswith('#'):
            raise ValueError(f"Invalid color format: {color}")
        if len(color) != 7:
            raise ValueError(f"Color must be #RRGGBB: {color}")
        return color

    def _validate_selection(self, image_id):
        sel = getattr(self, '_selections', {}).get(image_id)
        if sel is None:
            raise ValueError(f"No active selection for image {image_id}")
        return sel

    def get_image_count(self):
        return len(self._images)

    def get_total_size(self):
        return sum(im.size[0] * im.size[1] for im in self._images.values())

    def clear_all(self):
        self._images.clear()
        if hasattr(self, '_selections'):
            self._selections.clear()

    def _validate_image(self, image_id):
        if image_id not in self._images:
            raise KeyError(f"Image {image_id} not found")
        return self._images[image_id]

    def _validate_color(self, color):
        if not isinstance(color, str) or not color.startswith('#'):
            raise ValueError(f"Invalid color format: {color}")
        if len(color) != 7:
            raise ValueError(f"Color must be #RRGGBB: {color}")
        return color

    def _validate_selection(self, image_id):
        sel = getattr(self, '_selections', {}).get(image_id)
        if sel is None:
            raise ValueError(f"No active selection for image {image_id}")
        return sel

    def get_image_count(self):
        return len(self._images)

    def get_total_size(self):
        return sum(im.size[0] * im.size[1] for im in self._images.values())

    def clear_all(self):
        self._images.clear()
        if hasattr(self, '_selections'):
            self._selections.clear()
