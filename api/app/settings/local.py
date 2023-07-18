from app.settings.common import *  # noqa: F403

ENABLE_AXES = False


ALLOWED_HOSTS.extend([".ngrok.io", "127.0.0.1", "localhost"])  # noqa: F405

INSTALLED_APPS.extend(["debug_toolbar"])  # noqa: F405

MIDDLEWARE.extend(["debug_toolbar.middleware.DebugToolbarMiddleware"])  # noqa: F405

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


SWAGGER_SETTINGS["USE_SESSION_AUTH"] = False  # noqa: F405

# Allow admin login with username and password
ENABLE_ADMIN_ACCESS_USER_PASS = True

SKIP_MIGRATION_TESTS = True
