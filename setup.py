from setuptools import setup
import re

with open('mahjong/__init__.py') as f:
    content = f.read()
match = re.search('"""(.+?)"""', content, re.S)
if match is None:
    raise ValueError('Could not find module docstring in multivectors.py')
longdesc = match.group(1).strip()
with open('README.rst', 'w') as f:
    f.write(longdesc)

setup()
