from setuptools import setup
import re

with open('mahjong/__init__.py') as f:
    content = f.read()
    longdesc = re.match(r'^"""([\s\S]+?)"""', content).group(1).strip()
    with open('README.rst', 'w') as rdme:
        rdme.write(longdesc)
    version = re.search(r'__version__\s*=\s*"([^"]+)"', content).group(1)
del f, rdme

setup(
    name="python-mahjong",
    version=version,
    description="Abstract away the logic of mahjong games.",
    long_description=longdesc,
    url="https://github.com/Kenny2github/mahjong",
    author="Ken Hilton",
    license="GPLv3+",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Games/Entertainment :: Board Games',
        'Topic :: Games/Entertainment :: Turn Based Strategy',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3.7'
    ],
    keywords='mahjong game engine',
    packages=['mahjong'],
    python_requires='>=3.7',
)
