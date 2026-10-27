# qa-data-quality-cryptogamer

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)
![pytest](https://img.shields.io/badge/pytest-Data%20Quality-0A9EDC?logo=pytest)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit)
![CI](https://github.com/marcebusi/qa-data-quality-cryptogamer/actions/workflows/data-quality.yml/badge.svg)

**Data Quality Testing** con Python, SQLite, pytest y Streamlit.

**Aplicación bajo prueba**: [cryptogamer-ecommerce](https://github.com/marcebusi/cryptogamer-ecommerce) — e-commerce gaming (Node.js + Prisma + SQLite).

---

## ¿Qué es Data Quality Testing?

Valida que los datos almacenados en la base de datos cumplan reglas de:

| Dimensión | Qué verifica |
|---|---|
| **Completitud** | Campos obligatorios no son nulos |
| **Unicidad** | IDs y emails no están duplicados |
| **Validez** | Formatos correctos (email, JSON), valores permitidos (roles, status) |
| **Consistencia** | totalAmount == suma de items, originalPrice >= price |
| **Integridad referencial** | FKs apuntan a registros existentes |
| **Seguridad** | Contraseñas hasheadas, no texto plano |

---

## Estructura del proyecto

```
qa-data-quality-cryptogamer/
├── tests/
│   ├── test_products.py      # 12 tests — integridad de productos
│   ├── test_users.py         # 10 tests — integridad de usuarios
│   └── test_orders.py        # 9 tests — integridad de órdenes
├── dashboard/
│   └── app.py                # Dashboard interactivo con Streamlit
├── conftest.py               # Conexión SQLite + fixtures pandas
├── requirements.txt
└── .github/workflows/
    └── data-quality.yml      # CI con pytest + HTML report
```

---

## Prerequisitos

- Python 3.10+
- [cryptogamer-ecommerce](https://github.com/marcebusi/cryptogamer-ecommerce) clonado al mismo nivel que este repo (o configurar `DB_PATH`)

### Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## Cómo correr los tests

```bash
pytest tests/ -v
```

### Con reporte HTML

```bash
pytest tests/ --html=reports/report.html --self-contained-html -v
```

### Apuntando a otra base de datos

```bash
DB_PATH=/ruta/a/otra.db pytest tests/ -v
```

---

## Dashboard Streamlit

```bash
streamlit run dashboard/app.py
```

Se abre en `http://localhost:8501` con:

- **KPIs** — total de productos, usuarios, órdenes
- **Tab Productos** — distribución por categoría, histograma de precios, scatter rating vs precio, detección de anomalías
- **Tab Usuarios** — distribución de roles, registros por mes, checks de seguridad
- **Tab Órdenes** — estados, distribución de montos, consistencia con items
- **Tab Checks** — score general de calidad con gauge chart

---

## Conceptos clave

### pytest fixtures con scope="session"

```python
@pytest.fixture(scope="session")
def df_products(db):
    return pd.read_sql_query("SELECT * FROM products", db)
```

La conexión se abre una sola vez y los DataFrames se reutilizan en todos los tests → eficiente para tests sobre la misma DB.

### pandas para validaciones vectorizadas

```python
# En lugar de iterar fila por fila:
assert (df["price"] > 0).all()
assert df["id"].is_unique
assert df["email"].str.match(EMAIL_REGEX).all()
```

### Integridad referencial manual (SQLite no la enforcea por defecto)

```python
user_ids = set(df_users["id"])
orphans = set(df_orders["userId"]) - user_ids
assert not orphans
```

---

## CI/CD

El pipeline corre en cada push:
1. Clona cryptogamer-ecommerce y genera la DB con `prisma db seed`
2. Corre todos los tests con pytest
3. Genera reporte HTML y lo sube como artifact

---

## Proyectos relacionados

| # | Proyecto | Repo |
|---|---|---|
| 1 | E2E con Playwright + TypeScript | [qa-playwright-cryptogamer](https://github.com/marcebusi/qa-playwright-cryptogamer) |
| 2 | API Testing con Playwright + Newman | [qa-api-testing-cryptogamer](https://github.com/marcebusi/qa-api-testing-cryptogamer) |
| 3 | E2E con Robot Framework | [qa-robot-framework-cryptogamer](https://github.com/marcebusi/qa-robot-framework-cryptogamer) |
| 4 | Performance Testing con k6 | [qa-performance-cryptogamer](https://github.com/marcebusi/qa-performance-cryptogamer) |
| 5 | Data Quality con Python + Streamlit | ← este repo |

---

## Autor

**Marcelo Busignani** — QA Engineer  
[LinkedIn](https://www.linkedin.com/in/marcelo-busignani/) · [GitHub](https://github.com/marcebusi)
