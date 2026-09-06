"""Smoke test for the project scaffold (backlog task 1)."""


def test_arithmetic() -> None:
    assert 1 + 1 == 2


def test_django_settings_import() -> None:
    from django.conf import settings

    assert settings.configured
    assert settings.SETTINGS_MODULE == "config.settings"
    assert "django.contrib.contenttypes" in settings.INSTALLED_APPS
