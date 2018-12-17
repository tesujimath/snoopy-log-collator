# Copyright (c) 2018 Simon Guest
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gzip
import os
import pendulum
import re
import sys

def get_tagged_fields(s):
    """Extract tagged snoopy fields as a dict."""
    # Alas embedded spaces cause difficulty, as snoopy doesn't quote them in the logfile.
    # We therefore split on a cunning regex
    cunningRE = re.compile(r"""(\s+[a-z]+:)""")
    cunningSplit = re.split(cunningRE, s)
    toks = cunningSplit[0].split(':', 1) + cunningSplit[1:]
    fields = {}
    for i in range(len(toks) // 2):
        tag = toks[2 * i].lstrip().rstrip(':')
        value = toks[2 * i + 1]
        fields[tag] = value
    if 'filename' not in fields:
        sys.stderr.write("warning: get_tagged_fields failed to find filename for %s\n" % s)
    return fields

class Reader(object):
    def __init__(self, log, logfile_dt, config):
        self._config = config
        self._logfile_dt = logfile_dt
        self._logpath = os.path.join(self._config.logdir, log)

    def collate_to(self, collator):
        loglineRE = re.compile(r"""^(\S+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+\S+\[(\d+)\]:\s+\[([^\]]*)\]:\s+(.*)$""")
        logf = gzip.open(self._logpath)
        loglineno = 0
        try:
            for logline_bytes in logf:
                try:
                    logline = logline_bytes.decode('utf-8')
                    loglineno += 1
                    m = loglineRE.match(logline)
                    if m:
                        # infer the year for the timestamp, which is usually the same as the logfile year,
                        # except when we roll over from Dec to Jan
                        timestamp_s = m.group(1)
                        timestamp_year = self._logfile_dt.year - 1 if timestamp_s.startswith('Dec') and self._logfile_dt.month == 1 else self._logfile_dt.year
                        timestamp = pendulum.parse('%d %s' % (timestamp_year, timestamp_s), tz=pendulum.now().timezone)
                        fields = get_tagged_fields(m.group(4))
                        command = m.group(5).rstrip()
                        collator.command(timestamp, fields, command)
                    else:
                        sys.stderr.write('warning: ignoring badly formatted line at %s:%d\n' % (self._logpath, loglineno))
                except UnicodeDecodeError:
                    sys.stderr.write('warning: ignoring badly encoded line at %s:%d\n' % (self._logpath, loglineno))
        except:
            sys.stderr.write('failed at %s:%d\n' % (self._logpath, loglineno))
            raise
        finally:
            logf.close()
