from __future__ import annotations

from application.interfaces import CatalogProvider
from domain.models import BrandCatalog, BrandDefinition


class BrandCatalogService:
    def __init__(self, catalog_provider: CatalogProvider) -> None:
        self._catalog_provider = catalog_provider

    def get_catalog(self) -> BrandCatalog:
        return self._catalog_provider.get_brands()

    def get_brand(self, brand_id: str) -> BrandDefinition | None:
        return self._catalog_provider.get_brand(brand_id)
