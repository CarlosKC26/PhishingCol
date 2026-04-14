from __future__ import annotations

from domain.models import BrandCatalog, BrandDefinition
from infrastructure.config_provider import ConfigProvider


class JSONCatalogProvider:
    def __init__(self, config_provider: ConfigProvider) -> None:
        self._config_provider = config_provider
        self._catalog: BrandCatalog | None = None

    def get_brands(self) -> BrandCatalog:
        if self._catalog is None:
            self._catalog = self._config_provider.load_brand_catalog()
        return self._catalog

    def get_brand(self, brand_id: str) -> BrandDefinition | None:
        return self.get_brands().brands.get(brand_id)
