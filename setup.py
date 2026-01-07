# THIS FILE IS EXCLUSIVELY MAINTAINED by the project aedev.project_tpls v0.3.72
""" setup of ae namespace module portion shell: shell execution and environment helpers. """
import sys
# noinspection PyUnresolvedReferences
import pathlib
# noinspection PyUnresolvedReferences
import setuptools


print("SetUp " + __name__ + ": " + sys.executable + str(sys.argv) + f" {sys.path=}")

setup_kwargs = {
    'author': 'AndiEcker',
    'author_email': 'aecker2@gmail.com',
    'classifiers': [
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Typing :: Typed',
    ],
    'description': 'ae namespace module portion shell: shell execution and environment helpers',
    'extras_require': {
        'dev': [
            'aedev_project_tpls',
            'ae_ae',
            'anybadge',
            'coverage-badge',
            'flake8',
            'mypy',
            'pylint',
            'pytest',
            'pytest-cov',
            'pytest-django',
            'typing',
            'types-setuptools',
        ],
        'docs': [],
        'tests': [
            'anybadge',
            'coverage-badge',
            'flake8',
            'mypy',
            'pylint',
            'pytest',
            'pytest-cov',
            'pytest-django',
            'typing',
            'types-setuptools',
        ],
    },
    'install_requires': [
        'ae_base',
        'ae_core',
        'ae_console',
    ],
    'keywords': [
        'configuration',
        'development',
        'environment',
        'productivity',
    ],
    'license': 'GPL-3.0-or-later',
    'long_description': (pathlib.Path(__file__).parent / 'README.md').read_text(encoding='utf-8'),
    'long_description_content_type': 'text/markdown',
    'name': 'ae_shell',
    'package_data': {
        '': [],
    },
    'packages': [
        'ae',
    ],
    'project_urls': {
        'Bug Tracker': 'https://gitlab.com/ae-group/ae_shell/-/issues',
        'Documentation': 'https://ae.readthedocs.io/en/latest/_autosummary/ae.shell.html',
        'Repository': 'https://gitlab.com/ae-group/ae_shell',
        'Source': 'https://ae.readthedocs.io/en/latest/_modules/ae/shell.html',
    },
    'python_requires': '>=3.12',
    'url': 'https://gitlab.com/ae-group/ae_shell',
    'version': '0.3.12',
    'zip_safe': True,
}

if __name__ == "__main__":
    setuptools.setup(**setup_kwargs)
    pass
