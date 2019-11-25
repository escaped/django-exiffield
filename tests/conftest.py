from pathlib import Path

import django
from django.conf import settings


def pytest_configure():
    tests_dir = Path(__file__).parent
    settings.configure(
        DATABASES={
            'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        },
        ROOT_URLCONF='tests.urls',
        INSTALLED_APPS=('tests',),
        MEDIA_ROOT=tests_dir / 'media',
    )

    django.setup()
