"""
Dashboard de Calidad de Datos — cryptogamer-ecommerce
Visualiza métricas clave de la base de datos SQLite.
"""
import os
import sqlite3
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Configuración ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Data Quality Dashboard — cryptogamer",
    page_icon="🎮",
    layout="wide",
)

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "cryptogamer-ecommerce",
        "backend",
        "prisma",
        "dev.db",
    ),
)


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    products = pd.read_sql_query("SELECT * FROM products", conn)
    users = pd.read_sql_query("SELECT * FROM users", conn)
    orders = pd.read_sql_query("SELECT * FROM orders", conn)
    order_items = pd.read_sql_query("SELECT * FROM order_items", conn)
    categories = pd.read_sql_query("SELECT * FROM categories", conn)
    conn.close()
    return products, users, orders, order_items, categories


products, users, orders, order_items, categories = load_data()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎮 Data Quality Dashboard")
st.caption("cryptogamer-ecommerce — SQLite · actualizado en tiempo real")

# ── KPI row ──────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Productos", len(products))
col2.metric("Usuarios", len(users))
col3.metric("Órdenes", len(orders))
col4.metric("Categorías", len(categories))
col5.metric("Items de órdenes", len(order_items))

st.divider()

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_prod, tab_users, tab_orders, tab_checks = st.tabs(
    ["📦 Productos", "👤 Usuarios", "🛒 Órdenes", "✅ Checks de Calidad"]
)

# ──────────────────────────────────────────────────────────────────────────────
# TAB: PRODUCTOS
# ──────────────────────────────────────────────────────────────────────────────
with tab_prod:
    st.subheader("Distribución por categoría")

    prod_cat = (
        products.merge(categories[["id", "name"]], left_on="categoryId", right_on="id", suffixes=("", "_cat"))
        .groupby("name")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    fig = px.bar(prod_cat, x="name", y="count", color="count",
                 color_continuous_scale="Blues", labels={"name": "Categoría", "count": "Productos"})
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Distribución de precios")
        fig2 = px.histogram(products, x="price", nbins=20,
                            labels={"price": "Precio ($)"}, color_discrete_sequence=["#6366f1"])
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        st.subheader("Rating vs Precio")
        fig3 = px.scatter(products, x="price", y="rating", size="reviewCount",
                          hover_name="name", color="inStock",
                          labels={"price": "Precio ($)", "rating": "Rating"})
        st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Productos con originalPrice < price (anomalías)")
    anomalies = products[products["originalPrice"].notna() & (products["originalPrice"] < products["price"])]
    if anomalies.empty:
        st.success("✅ Ningún producto tiene originalPrice < price")
    else:
        st.error(f"⚠️ {len(anomalies)} anomalía(s) encontrada(s)")
        st.dataframe(anomalies[["name", "price", "originalPrice"]])

# ──────────────────────────────────────────────────────────────────────────────
# TAB: USUARIOS
# ──────────────────────────────────────────────────────────────────────────────
with tab_users:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Distribución por rol")
        role_counts = users["role"].value_counts().reset_index()
        role_counts.columns = ["role", "count"]
        fig = px.pie(role_counts, names="role", values="count",
                     color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Registros por mes")
        users["createdAt"] = pd.to_datetime(users["createdAt"])
        monthly = users.resample("ME", on="createdAt").size().reset_index(name="count")
        monthly["month"] = monthly["createdAt"].dt.strftime("%Y-%m")
        fig2 = px.bar(monthly, x="month", y="count",
                      labels={"month": "Mes", "count": "Usuarios"}, color_discrete_sequence=["#6366f1"])
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Checks de seguridad")
    plain_pwd = users[~users["password"].str.startswith(("$2b$", "$2a$", "$2y$"))]
    if plain_pwd.empty:
        st.success("✅ Todas las contraseñas están hasheadas con bcrypt")
    else:
        st.error(f"🚨 {len(plain_pwd)} contraseña(s) en texto plano")

    invalid_email_mask = ~users["email"].str.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    invalid_emails = users[invalid_email_mask]
    if invalid_emails.empty:
        st.success("✅ Todos los emails tienen formato válido")
    else:
        st.warning(f"⚠️ {len(invalid_emails)} email(s) con formato inválido")
        st.dataframe(invalid_emails[["id", "email"]])

# ──────────────────────────────────────────────────────────────────────────────
# TAB: ÓRDENES
# ──────────────────────────────────────────────────────────────────────────────
with tab_orders:
    if orders.empty:
        st.info("No hay órdenes en la base de datos.")
    else:
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Estados de órdenes")
            status_counts = orders["status"].value_counts().reset_index()
            status_counts.columns = ["status", "count"]
            fig = px.pie(status_counts, names="status", values="count",
                         color_discrete_sequence=px.colors.sequential.Teal)
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.subheader("Distribución de montos")
            fig2 = px.histogram(orders, x="totalAmount", nbins=20,
                                labels={"totalAmount": "Total ($)"}, color_discrete_sequence=["#14b8a6"])
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Consistencia: totalAmount vs suma de items")
        if not order_items.empty:
            order_items["line_total"] = order_items["price"] * order_items["quantity"]
            items_sum = order_items.groupby("orderId")["line_total"].sum().reset_index(name="items_sum")
            merged = orders[["id", "totalAmount"]].merge(items_sum, left_on="id", right_on="orderId", how="left")
            merged["diff"] = (merged["totalAmount"] - merged["items_sum"]).abs()
            inconsistent = merged[merged["diff"] > 1.0]
            if inconsistent.empty:
                st.success("✅ Todos los totalAmount son consistentes con los items")
            else:
                st.warning(f"⚠️ {len(inconsistent)} órdenes con diferencia > $1")
                st.dataframe(inconsistent)

# ──────────────────────────────────────────────────────────────────────────────
# TAB: CHECKS DE CALIDAD
# ──────────────────────────────────────────────────────────────────────────────
with tab_checks:
    st.subheader("Resumen de calidad de datos")

    checks = []

    # Products
    checks.append(("Productos", "IDs únicos", products["id"].is_unique))
    checks.append(("Productos", "Slugs únicos", products["slug"].is_unique))
    checks.append(("Productos", "Precios > 0", (products["price"] > 0).all()))
    checks.append(("Productos", "Rating en 0-5", ((products["rating"] >= 0) & (products["rating"] <= 5)).all()))
    checks.append(("Productos", "Sin nombre nulo", products["name"].notna().all()))

    # Users
    checks.append(("Usuarios", "IDs únicos", users["id"].is_unique))
    checks.append(("Usuarios", "Emails únicos", users["email"].is_unique))
    checks.append(("Usuarios", "Contraseñas hasheadas", users["password"].str.startswith(("$2b$", "$2a$", "$2y$")).all()))
    checks.append(("Usuarios", "Roles válidos", users["role"].isin({"CUSTOMER", "ADMIN", "SUPERADMIN"}).all()))

    # Orders
    if not orders.empty:
        checks.append(("Órdenes", "IDs únicos", orders["id"].is_unique))
        checks.append(("Órdenes", "totalAmount > 0", (orders["totalAmount"] > 0).all()))
        valid_statuses = {"PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"}
        checks.append(("Órdenes", "Status válidos", orders["status"].isin(valid_statuses).all()))

    df_checks = pd.DataFrame(checks, columns=["Tabla", "Check", "Resultado"])
    df_checks["Estado"] = df_checks["Resultado"].map({True: "✅ OK", False: "❌ FAIL"})

    passing = df_checks["Resultado"].sum()
    total = len(df_checks)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total checks", total)
    col2.metric("✅ Pasando", int(passing))
    col3.metric("❌ Fallando", int(total - passing))

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(passing / total * 100, 1),
        title={"text": "Score de calidad (%)"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#6366f1"},
            "steps": [
                {"range": [0, 60], "color": "#fee2e2"},
                {"range": [60, 80], "color": "#fef9c3"},
                {"range": [80, 100], "color": "#dcfce7"},
            ],
            "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 80},
        },
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        df_checks[["Tabla", "Check", "Estado"]],
        use_container_width=True,
        hide_index=True,
    )
