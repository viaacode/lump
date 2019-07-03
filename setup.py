from setuptools import setup, find_packages

with open('VERSION') as f:
    VERSION = f.read().strip()

with open('README.rst') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = list(map(str.rstrip, f.readlines()))

with open('requirements.gunicorn.txt') as f:
    requirements_gunicorn = list(map(str.rstrip, f.readlines()))

setup(
    name='lump',
    url='https://github.com/viaacode/lump/',
    version=VERSION,
    author='VIAA',
    author_email='support@viaa.be',
    descriptiona='Some modules useful for development at VIAA',
    long_description=long_description,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    python_requires='>=3.4',
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=requirements,
    extras_require={
        'test': [
            "pytest>=4.2.0"
        ],
        'gunicorn': requirements_gunicorn,
    },
    platforms='any'
)
