from typing import TypedDict, Optional, List


class RGBColor(TypedDict):
    r: int
    g: int
    b: int
    hex: str


class SkinData(TypedDict):
    rgb: RGBColor
    region_colors: dict
    color_temperature: str
    sample_count: int
    sources: int


class DAZResult(TypedDict):
    success: bool
    error: Optional[str]
    exit_code: int
    elapsed_seconds: float
    stdout: str
    stderr: str


class PipelineResult(TypedDict):
    success: bool
    error: Optional[str]
    face_output: Optional[str]
    skin_output: Optional[str]
    uv_output: Optional[str]
    daz_result: Optional[DAZResult]


class FaceResult(TypedDict):
    success: bool
    bbox: Optional[tuple]
    pose: str


class CacheEntry(TypedDict):
    image_hash: str
    face_path: str
    skin_path: str
    uv_path: Optional[str]
    timestamp: str
