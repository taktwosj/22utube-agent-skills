"""Single layout contract for 119's inset image-card layer."""

from __future__ import annotations


INSET_CARD_STYLE_PROFILE = "DEMOCRATIC_BLUE_INSET_CARD_V2"
CANVAS = {"width": 1920, "height": 1080}
IMAGE_FRAME = {"x": 336, "y": 189, "width": 1248, "height": 702}
SUPPORTED_RASTER_SIZES = ((1920, 1080),)
CAPTION_SAFE_AREA = {"x": 0, "y": 891, "width": 1920, "height": 189}
CAPCUT_CLIP_GEOMETRY = {
    "scale": {"x": 0.65, "y": 0.65},
    "rotation": 0.0,
    "transform": {"x": 0.0, "y": 0.0},
    "alpha": 1.0,
}


def inset_card_profile() -> dict[str, object]:
    return {
        "style_profile": INSET_CARD_STYLE_PROFILE,
        "canvas": dict(CANVAS),
        "output_size": (1920, 1080),
        "render_size": (1280, 720),
        "supported_raster_sizes": SUPPORTED_RASTER_SIZES,
        "image_frame": dict(IMAGE_FRAME),
        "caption_safe_area": dict(CAPTION_SAFE_AREA),
        "capcut_clip_geometry": {
            "scale": dict(CAPCUT_CLIP_GEOMETRY["scale"]),
            "rotation": CAPCUT_CLIP_GEOMETRY["rotation"],
            "transform": dict(CAPCUT_CLIP_GEOMETRY["transform"]),
            "alpha": CAPCUT_CLIP_GEOMETRY["alpha"],
        },
    }
