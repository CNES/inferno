from setuptools import setup
from setuptools import find_packages

# Import the library to make sure there is no side effect

def request_gdal_version():
    import subprocess
    try:
        r = subprocess.run(['gdal-config', '--version'], stdout=subprocess.PIPE )
        version = r.stdout.decode('utf-8').strip('\n')
        print("GDAL %s detected on the system, using 'gdal=%s'" % (version, version))
        return '3.2.2'
        return version
    except Exception as ex:  # pylint: disable=broad-except
        return '3.2.2'


setup(
    name                          = "inferno",
    version                       = "0.0.0",
    description                   = "description",
    long_description              = "readme",
    # long_description_content_type = "text/markdown",
    author                        = "author",
    author_email                  = "author_email",
    url                           = "url",
    license                       = "license",
    packages=find_packages(exclude=()),
    package_data={
        "": ["LICENSE"],
        "script":["resources/**/*"]
        },
    
    python_requires='>=3.7',
    install_requires=[
        'numpy',
        "eodag",
        "pyyaml",
        "pyqt5",
        "numpy",
        "xmltodict",
        "aiohttp",
        "gdal=="+request_gdal_version(),
        ],
    extras_require={
        },
    classifiers=[
        ],
    project_urls={
            },
    entry_points = {
        'console_scripts': [
            'inferno = script.main:main',
        ],
    },
)
