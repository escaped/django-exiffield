import codecs
import os
import re

from setuptools import setup


def read(*parts):
    filename = os.path.join(os.path.dirname(__file__), *parts)
    with codecs.open(filename, encoding='utf-8') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name='django-exiffield',
    version=find_version('exiffield', '__init__.py'),
    description='django-exiffield',
    long_description=open('README.rst').read(),
    url='http://github.com/escaped/django-exiffield/',
    author='Alexander Frenzel',
    author_email='alex@relatedworks.com',
    license='BSD',
    packages=['exiffield'],
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=[
        'Django>=1.8',
        'jsonfield>2.0<2.1',
        'choicesenum>0.2.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)
