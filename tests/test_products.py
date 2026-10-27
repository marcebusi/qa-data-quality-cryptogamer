"""
Calidad de datos — Tabla products
Valida integridad, consistencia y reglas de negocio.
"""
import json
import pytest


class TestProductsNotNull:
    """Campos obligatorios no deben ser nulos."""

    def test_id_not_null(self, df_products):
        assert df_products["id"].notna().all(), "Hay productos sin id"

    def test_name_not_null(self, df_products):
        assert df_products["name"].notna().all(), "Hay productos sin nombre"

    def test_price_not_null(self, df_products):
        assert df_products["price"].notna().all(), "Hay productos sin precio"

    def test_category_id_not_null(self, df_products):
        assert df_products["categoryId"].notna().all(), "Hay productos sin categoría"

    def test_slug_not_null(self, df_products):
        assert df_products["slug"].notna().all(), "Hay productos sin slug"


class TestProductsUniqueness:
    """Campos que deben ser únicos."""

    def test_id_unique(self, df_products):
        assert df_products["id"].is_unique, "IDs de productos duplicados"

    def test_slug_unique(self, df_products):
        assert df_products["slug"].is_unique, "Slugs de productos duplicados"


class TestProductsPrices:
    """Reglas de negocio sobre precios."""

    def test_price_positive(self, df_products):
        assert (df_products["price"] > 0).all(), "Hay productos con precio <= 0"

    def test_original_price_gte_price(self, df_products):
        """originalPrice siempre debe ser >= price (precio de oferta no puede subir)."""
        with_original = df_products[df_products["originalPrice"].notna()]
        if len(with_original) == 0:
            pytest.skip("No hay productos con originalPrice")
        violations = with_original[with_original["originalPrice"] < with_original["price"]]
        assert len(violations) == 0, (
            f"originalPrice < price en {len(violations)} producto(s): {violations['name'].tolist()}"
        )

    def test_no_negative_prices(self, df_products):
        assert (df_products["price"] >= 0).all(), "Hay productos con precio negativo"

    def test_original_price_not_negative(self, df_products):
        with_original = df_products[df_products["originalPrice"].notna()]
        if len(with_original) > 0:
            assert (with_original["originalPrice"] >= 0).all(), "originalPrice negativo"


class TestProductsRating:
    """El rating debe estar dentro del rango 0-5."""

    def test_rating_range(self, df_products):
        assert (df_products["rating"] >= 0).all() and (df_products["rating"] <= 5).all(), (
            "Rating fuera del rango 0-5"
        )

    def test_review_count_non_negative(self, df_products):
        assert (df_products["reviewCount"] >= 0).all(), "reviewCount negativo"


class TestProductsRelations:
    """Integridad referencial con categories."""

    def test_all_products_have_valid_category(self, df_products, df_categories):
        category_ids = set(df_categories["id"])
        product_cats = set(df_products["categoryId"])
        orphans = product_cats - category_ids
        assert not orphans, f"Productos con categoryId inexistente: {orphans}"


class TestProductsJsonFields:
    """Campos que almacenan JSON deben ser JSON válido."""

    def test_images_is_valid_json(self, df_products):
        for _, row in df_products.iterrows():
            try:
                json.loads(row["images"])
            except (json.JSONDecodeError, TypeError):
                pytest.fail(f"Campo 'images' inválido en producto '{row['name']}'")

    def test_condition_tags_is_valid_json(self, df_products):
        for _, row in df_products.iterrows():
            try:
                json.loads(row["conditionTags"])
            except (json.JSONDecodeError, TypeError):
                pytest.fail(f"Campo 'conditionTags' inválido en producto '{row['name']}'")


class TestProductsInventory:
    """Al menos hay productos disponibles."""

    def test_at_least_one_product(self, df_products):
        assert len(df_products) > 0, "No hay productos en la base de datos"

    def test_at_least_one_in_stock(self, df_products):
        in_stock = df_products[df_products["inStock"] == 1]
        assert len(in_stock) > 0, "Ningún producto está en stock"
