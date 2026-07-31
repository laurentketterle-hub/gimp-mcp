# Selection Tools & Emboss Filter (#4, #7)

## Overview

Selection tools and emboss filter for gimp-mcp — allows programmatic rectangle selection, fill, stroke, clear, and emboss operations through the MCP server.

## Available Operations

### Selection
| Tool | Description |
|------|-------------|
| `select_rect` | Define a rectangular selection region |
| `get_selection` | Query current selection state |
| `fill_selection` | Fill selection with a color |
| `stroke_selection` | Border stroke around selection |
| `clear_selection` | Remove active selection |

### Filters
| Filter | Description |
|--------|-------------|
| `emboss` | Apply emboss effect with configurable depth |

## Usage

### Mock Backend (for testing)
```python
from gimp_mcp.backend.mock import MockBackend

backend = MockBackend()
backend.load_image("test", 200, 200)
backend.select_rect("test", 50, 50, 100, 100)
backend.fill_selection("test", color="#ff0000")
backend.stroke_selection("test", color="#000000", line_width=2)
backend.emboss("test", depth=5)
```

### Pure Pillow Operations (no backend needed)
```python
from PIL import Image
from gimp_mcp import ops

im = Image.new("RGB", (200, 200), "#ffffff")
im = ops.selection_fill(im, 10, 10, 50, 50, color="#0000ff")
im = ops.selection_stroke(im, 20, 20, 60, 60, color="#ff0000", line_width=3)
im = ops.emboss(im, depth=4)
```

## Testing

```bash
pytest tests/test_selection_filters.py tests/test_selection_filters_enhanced.py -v
```

45 tests covering:
- Selection edge cases (full image, out-of-bounds, negative coords)
- Fill with RGB, RGBA, hex colors, transparent
- Stroke with variable line widths
- Emboss with varying depths, grayscale, single pixel
- Full pipelines (select → fill → stroke → emboss)
- Multi-region operations
- Selection state persistence
