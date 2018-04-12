snoopy-log-collator
===================

Snoopy-log-collator collates the log files from `snoopy
<https://github.com/a2o/snoopy>`_, producing a summary of what programs have
been run on the system, when, and by whom.  The output comprises a number of
files, one per command invoked, each being a list of invocation
instances.

For example, the output file ``usr/bin/gunzip`` might contain the following
output:

::

    20180312-16:54:38 guestsi /usr/bin/gunzip -c /usr/share/man/man1/condor_q.1.gz
    20180313-12:57:50 mccullocha /usr/bin/gunzip -c /usr/share/man/man1/grep.1.gz
    20180313-12:57:50 mccullocha /usr/bin/gunzip -c /usr/share/man/man1/grep.1.gz
    20180313-12:57:50 mccullocha /usr/bin/gunzip -c /usr/share/man/man1/grep.1.gz
    20180315-14:50:54 guestsi /usr/bin/gunzip -c /usr/share/man/man1/sh.1.gz
    20180315-14:50:54 guestsi /usr/bin/gunzip -c /usr/share/man/man1/sh.1.gz
    20180315-14:50:54 guestsi /usr/bin/gunzip -c /usr/share/man/man1/sh.1.gz

Installation
------------

Snoopy-log-collator is on PyPI, so may be installed using pip, preferably in
a virtualenv.

::

    $ pip install snoopy-log-collator

Alternatively, snoopy-log-collator is also on conda-forge.

::

    $ conda install snoopy-log-collator

Installing snoopy-log-collator from RPM is now deprecated, and the spec file has therefore
been removed from the repo.

Configuration
-------------

See the See the `example configuration file <doc/example-config.toml>`__.


Example Use
-----------

::

    $ snoopy_log_collator -c example-config.toml

Notes
-----

Snoopy-log-collator looks for logfiles in the log directory named
``snoopy-YYYYMMDD.gz``.  It therefore avoids processing the currently active
logfile.

Once a logfile has been collated, its timestamp is recorded in
``<collation-dir>/.<hostname>.collated``, to avoid repeated collation on
subsequent runs.
