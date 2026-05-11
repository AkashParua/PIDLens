"""Plugin shell for external ML providers (VLM / OCR / detectors / loaders).

The Provider ABC is intentionally tiny — concrete providers register
themselves by appending to BUILTINS at import time. Each provider declares a
JSON-shaped settings schema so the Integrations screen can render a form
without knowing anything about the underlying API.

The real network/SDK calls aren't wired here. `infer()` is left abstract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


KIND_VLM = "vlm"
KIND_OCR = "ocr"
KIND_DETECTOR = "detector"
KIND_LOADER = "loader"

KINDS = (KIND_VLM, KIND_OCR, KIND_DETECTOR, KIND_LOADER)
KIND_LABELS = {
    KIND_VLM: "Vision-language models",
    KIND_OCR: "OCR engines",
    KIND_DETECTOR: "Object detectors",
    KIND_LOADER: "Dataset loaders",
}


@dataclass
class SettingField:
    name: str
    label: str
    kind: str = "text"  # text | password | int | float | enum
    default: Any = ""
    options: tuple[str, ...] = ()


@dataclass
class ProviderSpec:
    id: str
    label: str
    kind: str
    description: str = ""
    fields: tuple[SettingField, ...] = field(default_factory=tuple)


class Provider(ABC):
    spec: ProviderSpec

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self.settings = dict(settings or {})

    @abstractmethod
    def infer(self, payload: Any) -> Any:
        """Run inference. Shape of `payload`/return is per-kind (see docs)."""

    def is_configured(self) -> bool:
        """Default: every non-default field has a non-empty value."""
        for f in self.spec.fields:
            if f.kind == "password":
                if not self.settings.get(f.name):
                    return False
        return True


# ── Built-in stubs ───────────────────────────────────────────
# These don't ship real integrations — they exist so the Integrations screen
# has something to render and `infer()` calls fail loudly with a clear message
# instead of silently doing nothing.

class _StubProvider(Provider):
    def infer(self, payload: Any) -> Any:
        raise NotImplementedError(
            f"{self.spec.id} is a stub; install the real provider package"
        )


class OpenAIVLMProvider(_StubProvider):
    spec = ProviderSpec(
        id="openai-vlm",
        label="OpenAI GPT-4o (Vision)",
        kind=KIND_VLM,
        description="Send images to GPT-4o for captions / VQA. Requires API key.",
        fields=(
            SettingField("api_key", "API key", "password"),
            SettingField("model", "Model", "enum", default="gpt-4o", options=("gpt-4o", "gpt-4o-mini")),
        ),
    )


class AnthropicVLMProvider(_StubProvider):
    spec = ProviderSpec(
        id="anthropic-vlm",
        label="Anthropic Claude (Vision)",
        kind=KIND_VLM,
        description="Send images to Claude. Requires API key.",
        fields=(
            SettingField("api_key", "API key", "password"),
            SettingField("model", "Model", "enum", default="claude-opus-4-7",
                         options=("claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5")),
        ),
    )


class TesseractOCRProvider(_StubProvider):
    spec = ProviderSpec(
        id="tesseract",
        label="Tesseract",
        kind=KIND_OCR,
        description="Local OCR via pytesseract. No network calls.",
        fields=(
            SettingField("tesseract_path", "Binary path", "text", default="tesseract"),
            SettingField("lang", "Language", "text", default="eng"),
        ),
    )


class PaddleOCRProvider(_StubProvider):
    spec = ProviderSpec(
        id="paddleocr",
        label="PaddleOCR",
        kind=KIND_OCR,
        description="Local OCR via PaddleOCR.",
        fields=(
            SettingField("lang", "Language", "text", default="en"),
        ),
    )


class RFDetrProvider(_StubProvider):
    spec = ProviderSpec(
        id="rf-detr",
        label="RF-DETR",
        kind=KIND_DETECTOR,
        description="Real-time DETR; trained models from the Training screen plug in here.",
        fields=(
            SettingField("weights", "Weights path", "text"),
            SettingField("conf", "Confidence threshold", "float", default=0.25),
        ),
    )


class UltralyticsYOLOProvider(_StubProvider):
    spec = ProviderSpec(
        id="ultralytics-yolo",
        label="Ultralytics YOLO",
        kind=KIND_DETECTOR,
        description="Run inference with an Ultralytics YOLOv8 model.",
        fields=(
            SettingField("weights", "Weights path", "text"),
            SettingField("conf", "Confidence threshold", "float", default=0.25),
        ),
    )


class CocoLoaderProvider(_StubProvider):
    spec = ProviderSpec(
        id="coco-loader",
        label="COCO JSON loader",
        kind=KIND_LOADER,
        description="Import annotations from a COCO-format JSON file.",
        fields=(
            SettingField("json_path", "annotations.json", "text"),
        ),
    )


BUILTINS: list[type[Provider]] = [
    OpenAIVLMProvider,
    AnthropicVLMProvider,
    TesseractOCRProvider,
    PaddleOCRProvider,
    RFDetrProvider,
    UltralyticsYOLOProvider,
    CocoLoaderProvider,
]


def all_provider_specs() -> list[ProviderSpec]:
    return [cls.spec for cls in BUILTINS]
