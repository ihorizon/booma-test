"""Stubbed geocoding / places — no external API calls."""

import json
from pathlib import Path

from app.config import settings
from app.schemas import MapSuggestion


class MapsStub:
    def __init__(self) -> None:
        self._landmarks: list[dict] = []
        path = settings.synthetic_data_path
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            ctx = data.get("map_context") or {}
            for lm in ctx.get("landmarks") or []:
                self._landmarks.append(lm)

    def autocomplete(self, query: str, limit: int = 8) -> list[MapSuggestion]:
        q = (query or "").strip().lower()
        if not q:
            return [
                MapSuggestion(
                    id=f"lm_{i}",
                    label=lm["name"],
                    lat=lm["lat"],
                    lng=lm["lng"],
                )
                for i, lm in enumerate(self._landmarks[:limit])
            ]
        matches = [lm for lm in self._landmarks if q in lm["name"].lower()]
        return [
            MapSuggestion(id=f"lm_{i}", label=lm["name"], lat=lm["lat"], lng=lm["lng"])
            for i, lm in enumerate(matches[:limit])
        ]
