from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile


class ZipExtractor:
    def extract(self, archive_path: str | Path, destination_dir: str | Path) -> list[str]:
        archive = Path(archive_path)
        destination = Path(destination_dir)
        destination.mkdir(parents=True, exist_ok=True)
        extracted_files: list[str] = []

        with ZipFile(archive, "r") as zip_file:
            for member in zip_file.infolist():
                if member.is_dir():
                    continue
                target_path = (destination / member.filename).resolve()
                if not str(target_path).startswith(str(destination.resolve())):
                    continue
                zip_file.extract(member, destination)
                extracted_files.append(str(target_path))

        return extracted_files
