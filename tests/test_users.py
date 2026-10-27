"""
Calidad de datos — Tabla users
Valida integridad, unicidad y reglas de seguridad.
"""
import re
import pytest


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_ROLES = {"CUSTOMER", "ADMIN", "SUPERADMIN"}


class TestUsersNotNull:
    """Campos obligatorios no deben ser nulos."""

    def test_id_not_null(self, df_users):
        assert df_users["id"].notna().all(), "Hay usuarios sin id"

    def test_email_not_null(self, df_users):
        assert df_users["email"].notna().all(), "Hay usuarios sin email"

    def test_password_not_null(self, df_users):
        assert df_users["password"].notna().all(), "Hay usuarios sin contraseña"

    def test_role_not_null(self, df_users):
        assert df_users["role"].notna().all(), "Hay usuarios sin rol"


class TestUsersUniqueness:
    """Campos que deben ser únicos."""

    def test_id_unique(self, df_users):
        assert df_users["id"].is_unique, "IDs de usuarios duplicados"

    def test_email_unique(self, df_users):
        assert df_users["email"].is_unique, "Emails de usuarios duplicados"


class TestUsersEmailFormat:
    """El email debe tener formato válido."""

    def test_email_format(self, df_users):
        invalid = df_users[~df_users["email"].str.match(EMAIL_REGEX)]
        assert len(invalid) == 0, (
            f"Emails con formato inválido: {invalid['email'].tolist()}"
        )


class TestUsersRole:
    """El rol debe ser uno de los valores permitidos."""

    def test_valid_roles(self, df_users):
        invalid = df_users[~df_users["role"].isin(VALID_ROLES)]
        assert len(invalid) == 0, (
            f"Roles inválidos encontrados: {invalid['role'].unique().tolist()}"
        )


class TestUsersPasswordSecurity:
    """La contraseña no debe estar almacenada en texto plano."""

    def test_password_is_hashed(self, df_users):
        """Bcrypt hashes empiezan con $2b$ o $2a$."""
        plain_passwords = df_users[
            ~df_users["password"].str.startswith(("$2b$", "$2a$", "$2y$"))
        ]
        assert len(plain_passwords) == 0, (
            f"Hay {len(plain_passwords)} usuario(s) con contraseñas sin hashear"
        )

    def test_password_not_exposed_as_common_value(self, df_users):
        common = ["password", "123456", "admin", "qwerty", "test"]
        for pwd in common:
            exposed = df_users[df_users["password"] == pwd]
            assert len(exposed) == 0, f"Contraseña en texto plano '{pwd}' encontrada"


class TestUsersTimestamps:
    """Campos de fecha deben existir y ser coherentes."""

    def test_created_at_not_null(self, df_users):
        assert df_users["createdAt"].notna().all(), "Hay usuarios sin createdAt"

    def test_updated_at_not_null(self, df_users):
        assert df_users["updatedAt"].notna().all(), "Hay usuarios sin updatedAt"

    def test_updated_gte_created(self, df_users):
        violations = df_users[df_users["updatedAt"] < df_users["createdAt"]]
        assert len(violations) == 0, (
            f"updatedAt < createdAt en {len(violations)} usuario(s)"
        )


class TestUsersInventory:
    """Al menos hay un usuario registrado."""

    def test_at_least_one_user(self, df_users):
        assert len(df_users) > 0, "No hay usuarios en la base de datos"
