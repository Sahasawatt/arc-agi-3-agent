# duckv23 cell 12 — port the newer bundle's grid-line renderer onto the anim bundle,
# plus one line of system prompt telling the model the lattice is a rendering aid.
#
# PROVENANCE (notes/R29-grid-lines.md): the post-anim TAAF bundle ships
# _render_grid_lined_image in inference/agent/vision_context.py, gated on
# MULTIMODAL_GRID_LINES == "1". Its own setup_commands.json sets the flag to 'true',
# so the feature has never run anywhere, including for its author. The anim bundle
# we run predates the feature entirely. This cell ports the renderer and arms it
# unconditionally (no env flag — fewer moving parts, and the flag's only failure
# mode is exactly the bug that killed it upstream).
#
# WHY THE PROMPT NOTE (v23.1, measured in the v23 smoke): with lines alone, ka59's
# opening turn read the lattice as GAME STRUCTURE ("a grid of white cells separated
# by gray grid lines") and burned a 7k-char turn on the image-vs-ascii contradiction,
# because nothing tells the model the lines exist. The upstream author never ran the
# feature, so nobody hit this before us.
#
# SEAM (verified against anim source): tool_agent imports current_grid_image_part
# only, and that function calls frame_to_png_data_url by bare name in-module, so
# patching the vision_context module attribute lands on every render. The prompt
# note is the v22 seam: tool_agent.py:22 imports MULTIMODAL_CONTEXT_ADDENDUM by
# name, so BOTH module bindings get patched. The teeth below re-verify all of it
# in-kernel.
import base64
import io

from PIL import Image

import inference.agent.prompts as _prompts
import inference.agent.tool_agent as _ta
import inference.agent.vision_context as _vc

_GRID_LINE_COLOR = (128, 128, 128)  # upstream GRID_LINE_COLOR
_MIN_CELL_PX = 4                    # upstream GRID_LINE_MIN_CELL_PX

_orig_frame_to_png_data_url = _vc.frame_to_png_data_url


def _render_grid_lined_image(frame, rows, cols, scale):
    # Ported from the newer bundle: fill the canvas with the line color, paint each
    # cell (scale-1)px shy of its span; the untouched sliver stays the line color.
    # Plain pixel writes on purpose (upstream comment: some Pillow builds break
    # ImageDraw's text submodule).
    image = Image.new("RGB", (cols * scale, rows * scale), _GRID_LINE_COLOR)
    pixels = image.load()
    cell_span = scale - 1
    color_map = _vc.ARC_COLOR_MAP
    for row_idx, row in enumerate(frame.grid):
        for col_idx in range(cols):
            value = row[col_idx] if col_idx < len(row) else 0
            color = color_map.get(int(value), color_map[0])
            base_x = col_idx * scale
            base_y = row_idx * scale
            for dy in range(cell_span):
                for dx in range(cell_span):
                    pixels[base_x + dx, base_y + dy] = color
    return image


def _grid_lined_frame_to_png_data_url(frame, *, upscale=None):
    rows = len(frame.grid)
    cols = max((len(row) for row in frame.grid), default=0)
    if rows <= 0 or cols <= 0:
        raise ValueError("Cannot render an empty grid as an image.")
    scale = _vc.current_grid_image_upscale() if upscale is None else max(1, int(upscale))
    if scale < _MIN_CELL_PX:
        return _orig_frame_to_png_data_url(frame, upscale=scale)
    image = _render_grid_lined_image(frame, rows, cols, scale)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


_vc.frame_to_png_data_url = _grid_lined_frame_to_png_data_url

# ---- prompt note: tell the model the lattice is a rendering aid, not game content ----
_GRID_NOTE = (
    "- The image draws a thin gray line between adjacent cells as a rendering aid; "
    "this gray lattice is NOT game content and does not appear in `current_frame.ascii` "
    "or `segmentation`.\n"
)
_stock_addendum = _prompts.MULTIMODAL_CONTEXT_ADDENDUM
_patched_addendum = _stock_addendum + _GRID_NOTE
_prompts.MULTIMODAL_CONTEXT_ADDENDUM = _patched_addendum
_ta.MULTIMODAL_CONTEXT_ADDENDUM = _patched_addendum  # tool_agent.py:22 imports by name


# ---- teeth (functional, pixel-level; no string asserts that a comment can satisfy) ----
def _teeth():
    class _FakeFrame:
        grid = [[1, 2], [3, 4]]

    url = _vc.frame_to_png_data_url(_FakeFrame(), upscale=8)
    prefix = "data:image/png;base64,"
    if not url.startswith(prefix):
        raise AssertionError("duckv23 TEETH FAIL: patched renderer returned a non-PNG data url")
    img = Image.open(io.BytesIO(base64.b64decode(url[len(prefix):]))).convert("RGB")
    if img.size != (16, 16):
        raise AssertionError(f"duckv23 TEETH FAIL: expected 16x16, got {img.size}")
    px = img.load()
    if px[7, 7] != _GRID_LINE_COLOR:
        raise AssertionError(f"duckv23 TEETH FAIL: no grid line at (7,7): {px[7, 7]}")
    expected = _vc.ARC_COLOR_MAP.get(1, _vc.ARC_COLOR_MAP[0])
    if px[0, 0] != tuple(expected):
        raise AssertionError(f"duckv23 TEETH FAIL: cell pixel {px[0, 0]} != color map {expected}")

    # no-op guard: the stock renderer at the same scale must produce a DIFFERENT image,
    # or this patch changed nothing.
    stock = _orig_frame_to_png_data_url(_FakeFrame(), upscale=8)
    if stock == url:
        raise AssertionError("duckv23 TEETH FAIL: stock render identical - patch is a no-op")

    # seam guard: tool_agent must not hold its own binding of frame_to_png_data_url,
    # or the patch would not reach the running call site (the v21/v22 trap).
    if hasattr(_ta, "frame_to_png_data_url"):
        raise AssertionError("duckv23 TEETH FAIL: tool_agent binds frame_to_png_data_url directly")
    if _vc.frame_to_png_data_url is not _grid_lined_frame_to_png_data_url:
        raise AssertionError("duckv23 TEETH FAIL: vision_context patch did not stick")

    # prompt-note teeth: compare RUNTIME strings only (a comment can never satisfy these).
    # The binding that actually reaches the prompt is tool_agent's (import-by-name).
    if _GRID_NOTE not in _ta.MULTIMODAL_CONTEXT_ADDENDUM:
        raise AssertionError("duckv23 TEETH FAIL: grid note missing from tool_agent binding")
    if _GRID_NOTE not in _prompts.MULTIMODAL_CONTEXT_ADDENDUM:
        raise AssertionError("duckv23 TEETH FAIL: grid note missing from prompts binding")
    if _GRID_NOTE in _stock_addendum:
        raise AssertionError(
            "duckv23 TEETH FAIL: stock addendum already carried the note - patch measures nothing"
        )
    if not _stock_addendum.strip():
        raise AssertionError("duckv23 TEETH FAIL: stock addendum empty - wrong module or import order")


_teeth()
print(
    "duckv23: grid-line renderer ported and armed "
    f"(line color {_GRID_LINE_COLOR}, min cell px {_MIN_CELL_PX}); "
    f"grid note appended to MULTIMODAL_CONTEXT_ADDENDUM (both bindings, "
    f"{len(_stock_addendum)} -> {len(_patched_addendum)} chars); teeth OK",
    flush=True,
)
