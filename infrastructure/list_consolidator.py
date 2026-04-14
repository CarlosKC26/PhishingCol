from __future__ import annotations

from pathlib import Path


class ListConsolidator:
    def consolidate(self, file_paths: list[str | Path]) -> list[str]:
        domains: set[str] = set()

        for file_path in file_paths:
            path = Path(file_path)
            if path.suffix.lower() != ".txt" or not path.exists():
                continue
            with path.open("r", encoding="utf-8", errors="ignore") as file_handle:
                for line in file_handle:
                    cleaned = line.strip().lower()
                    if cleaned:
                        domains.add(cleaned)

        return sorted(domains)
