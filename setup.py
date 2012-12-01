from setuptools import setup
import sys

classifiers = """\
Intended Audience :: Developers
License :: OSI Approved :: Apache Software License
Development Status :: 4 - Beta
Natural Language :: English
Programming Language :: Python :: 2
Programming Language :: Python :: 2.5
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.1
Programming Language :: Python :: 3.2
Programming Language :: Python :: 3.3
Operating System :: MacOS :: MacOS X
Operating System :: Unix
Programming Language :: Python
Programming Language :: Python :: Implementation :: CPython
Programming Language :: Python :: Implementation :: PyPy
"""

description = "Simple extensions to Tornado's gen module."

long_description = open("README.rst").read()

major, minor = sys.version_info[:2]

kwargs = {}
if major >= 3:
    kwargs['use_2to3'] = True

packages = ['yieldpoints']
if "nosetests" in sys.argv:
    packages.append('test')

setup(name='yieldpoints',
      version='0.1',
      packages=packages,
      description=description,
      long_description=long_description,
      author='A. Jesse Jiryu Davis',
      author_email='ajdavis@cs.oberlin.edu',
      url='http://github.com/ajdavis/yieldpoints/',
      install_requires=['tornado >= 2.4.0'],
      license='http://www.apache.org/licenses/LICENSE-2.0',
      classifiers=filter(None, classifiers.split('\n')),
      keywords='tornado coroutines semaphore mutex queue asynchronous',
      # use python setup.py nosetests to test
      setup_requires=['nose'],
      **kwargs
)
