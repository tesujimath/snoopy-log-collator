#!/usr/bin/env python
#
# distutils setup script for filebutler package

from setuptools import setup, find_packages

long_description = """Snoopy-log-collator collates the log files from snoopy, producing a
summary of what programs have been run on the system, when, and by whom.  The
output comprises a number of files, one per command invoked, each being a list
of invocation instances.
"""

setup(name='snoopy-log-collator',
      use_scm_version=True,
      setup_requires=['setuptools_scm', 'setuptools_scm_git_archive'],
      description='Collate logfiles from snoopy logger',
      long_description=long_description,
      author='Simon Guest',
      author_email='simon.guest@tesujimath.org',
      url='https://github.com/tesujimath/snoopy-log-collator',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 3',
          'Topic :: System :: Systems Administration',
          'Topic :: Utilities',
      ],
      packages=find_packages(),
      entry_points={
        'console_scripts': [
            'snoopy-log-collator = snoopy_log_collator.__main__:main',
        ],
      },
      package_data={
          'doc': ['*.rst'],
      },
      license='GPLv3',
      install_requires=[
          'pendulum',
          'pytoml',
          'setuptools',
      ],
      python_requires='>=3',
     )
