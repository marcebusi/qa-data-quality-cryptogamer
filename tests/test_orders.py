"""
Calidad de datos — Tablas orders / order_items
Valida integridad referencial, montos y estados.
"""
import pytest


VALID_STATUSES = {"PENDING", "CONFIRMED", "PAID", "SHIPPED", "DELIVERED", "CANCELLED"}
VALID_PAYMENT_METHODS = {"transfer", "mercadopago", "cash", None}


class TestOrdersNotNull:
    """Campos obligatorios no deben ser nulos."""

    def test_id_not_null(self, df_orders):
        assert df_orders["id"].notna().all(), "Hay órdenes sin id"

    def test_user_id_not_null(self, df_orders):
        assert df_orders["userId"].notna().all(), "Hay órdenes sin userId"

    def test_total_amount_not_null(self, df_orders):
        assert df_orders["totalAmount"].notna().all(), "Hay órdenes sin totalAmount"

    def test_status_not_null(self, df_orders):
        assert df_orders["status"].notna().all(), "Hay órdenes sin status"


class TestOrdersUniqueness:

    def test_id_unique(self, df_orders):
        assert df_orders["id"].is_unique, "IDs de órdenes duplicados"


class TestOrdersAmounts:
    """Reglas de negocio sobre montos."""

    def test_total_amount_positive(self, df_orders):
        if len(df_orders) == 0:
            pytest.skip("No hay órdenes")
        assert (df_orders["totalAmount"] > 0).all(), "Hay órdenes con totalAmount <= 0"

    def test_shipping_cost_non_negative(self, df_orders):
        if len(df_orders) == 0:
            pytest.skip("No hay órdenes")
        with_shipping = df_orders[df_orders["shippingCost"].notna()]
        if len(with_shipping) > 0:
            assert (with_shipping["shippingCost"] >= 0).all(), "shippingCost negativo"


class TestOrdersStatus:
    """El status debe ser un valor permitido."""

    def test_valid_status_values(self, df_orders):
        if len(df_orders) == 0:
            pytest.skip("No hay órdenes")
        invalid = df_orders[~df_orders["status"].isin(VALID_STATUSES)]
        assert len(invalid) == 0, (
            f"Status inválidos: {invalid['status'].unique().tolist()}"
        )


class TestOrdersRelations:
    """Integridad referencial con users."""

    def test_all_orders_have_valid_user(self, df_orders, df_users):
        if len(df_orders) == 0:
            pytest.skip("No hay órdenes")
        user_ids = set(df_users["id"])
        order_user_ids = set(df_orders["userId"])
        orphans = order_user_ids - user_ids
        assert not orphans, f"Órdenes con userId inexistente: {orphans}"


class TestOrderItemsIntegrity:
    """Integridad de order_items."""

    def test_quantity_positive(self, df_order_items):
        if len(df_order_items) == 0:
            pytest.skip("No hay order items")
        assert (df_order_items["quantity"] > 0).all(), "Hay items con quantity <= 0"

    def test_price_positive(self, df_order_items):
        if len(df_order_items) == 0:
            pytest.skip("No hay order items")
        assert (df_order_items["price"] > 0).all(), "Hay items con price <= 0"

    def test_order_items_reference_valid_orders(self, df_order_items, df_orders):
        if len(df_order_items) == 0:
            pytest.skip("No hay order items")
        order_ids = set(df_orders["id"])
        item_order_ids = set(df_order_items["orderId"])
        orphans = item_order_ids - order_ids
        assert not orphans, f"Items referenciando órdenes inexistentes: {orphans}"

    def test_order_items_reference_valid_products(self, df_order_items, df_products):
        if len(df_order_items) == 0:
            pytest.skip("No hay order items")
        product_ids = set(df_products["id"])
        item_product_ids = set(df_order_items["productId"])
        orphans = item_product_ids - product_ids
        assert not orphans, f"Items referenciando productos inexistentes: {orphans}"


class TestOrdersTotalConsistency:
    """El totalAmount de una orden debe ser consistente con sus items."""

    def test_total_amount_matches_items(self, df_orders, df_order_items):
        if len(df_orders) == 0 or len(df_order_items) == 0:
            pytest.skip("No hay datos suficientes")

        df_order_items["line_total"] = df_order_items["price"] * df_order_items["quantity"]
        items_total = df_order_items.groupby("orderId")["line_total"].sum()

        mismatches = []
        for order_id, items_sum in items_total.items():
            order_row = df_orders[df_orders["id"] == order_id]
            if len(order_row) == 0:
                continue
            db_total = order_row.iloc[0]["totalAmount"]
            # totalAmount puede incluir shippingCost → toleramos esa diferencia
            shipping = order_row.iloc[0]["shippingCost"] or 0
            tolerance = max(1.0, shipping)
            if abs(db_total - items_sum) > tolerance:
                mismatches.append({
                    "order_id": order_id,
                    "db_total": db_total,
                    "items_sum": items_sum,
                    "diff": abs(db_total - items_sum),
                })

        assert not mismatches, (
            f"{len(mismatches)} órdenes con totalAmount inconsistente: "
            f"{mismatches[:3]}"
        )
