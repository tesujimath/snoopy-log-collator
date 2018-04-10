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

from datetime import datetime
import gzip
import os
import re

def get_tagged_fields(s):
    """Extract tagged snoopy fields as a dict."""
    # Alas embedded spaces cause difficulty, as snoopy doesn't quote them in the logfile.
    # We therefore split on a cunning regex
    cunningRE = re.compile(r"""(\s+\w+:)""")
    cunningSplit = re.split(cunningRE, s)
    toks = cunningSplit[0].split(':', 1) + cunningSplit[1:]
    fields = {}
    for i in range(len(toks) / 2):
        tag = toks[2 * i].lstrip().rstrip(':')
        value = toks[2 * i + 1]
        fields[tag] = value
    return fields

class Reader(object):
    def __init__(self, log, logfile_dt, config):
        self._config = config
        self._logfile_dt = logfile_dt
        self._logpath = os.path.join(self._config.logdir, log)

    def collate_to(self, collator):
        loglineRE = re.compile(r"""^(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\w+)\s+\w+\[(\d+)\]:\s+\[([^\]]*)\]:\s+(.*)$""")
        logf = gzip.open(self._logpath)
        try:
            for logline in logf:
                m = loglineRE.match(logline)
                if m:
                    # infer the year for the timestamp, which is usually the same as the logfile year,
                    # except when we roll over from Dec to Jan
                    timestamp_s = m.group(1)
                    timestamp_year = self._logfile_dt.year - 1 if timestamp_s.startswith('Dec') and self._logfile_dt.month == 1 else self._logfile_dt.year
                    naive = datetime.strptime('%d %s' % (timestamp_year, timestamp_s), '%Y %b %d %H:%M:%S')
                    timestamp = datetime(naive.year, naive.month, naive.day, naive.hour, naive.minute, naive.second, tzinfo=self._config.local_tzinfo)

                    fields = get_tagged_fields(m.group(4))
                    command = m.group(5).rstrip()
                    collator.command(timestamp, fields, command)
                else:
                    print("failed on %s" % logline.rstrip('\n'))
        finally:
            logf.close()
