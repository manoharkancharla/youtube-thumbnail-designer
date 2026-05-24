import operator
from typing import Annotated, Optional
from typing_extensions import TypedDict


class IterationRecord(TypedDict):
    iteration: int
    prompt: str
    image_path: str
    rating: int
    critique: str


class ThumbnailStrategy(TypedDict):
    main_subject: str
    topic_symbols: list[str]
    emotion: str
    background: str
    style: str
    text_overlay: str
    text_placement: str
    attention_hook: str
    color_palette: str


class ThumbnailState(TypedDict):
    topic: str
    search_summary: str
    strategy: dict
    current_prompt: str
    image_path: str
    rating: int
    critique: str
    iteration: int
    target_rating: int
    max_iterations: int
    output_dir: str
    history: Annotated[list[IterationRecord], operator.add]
