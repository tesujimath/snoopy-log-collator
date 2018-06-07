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

import os.path
import pendulum
import re

from .util import bare_hostname

class Collator(object):
    def __init__(self, config, mapper):
        self._config = config
        self._mapper = mapper
        self._hostname = bare_hostname()

    def _outpath(self, cls, filename):
        if os.path.isabs(filename):
            return os.path.join(self._config.localhost_collation_dir(cls), filename[1:])
        else:
            return os.path.join(self._config.localhost_collation_dir(cls), filename)

    def command(self, timestamp, fields, command):
        filename = fields['filename']
        if os.path.isabs(filename):
            filepath = filename
        else:
            filepath = os.path.normpath(os.path.join(fields['cwd'], filename))
        user = self._mapper.username(int(fields['uid']))
        if self._mapper.isfile(filepath):
            for cls in self._config.classes_with_all:
                if not self._mapper.excluded(filepath, cls, self._config):
                    outpath = self._outpath(cls, filepath)
                    if not os.path.exists(outpath):
                        outdir = os.path.dirname(outpath)
                        if not os.path.exists(outdir):
                            os.makedirs(outdir)
                    with open(outpath, 'a') as outf:
                        outf.write('%s %s %s %s\n' % (timestamp.strftime('%Y%m%d-%H:%M:%S'), self._hostname, user, command))
                    t = timestamp.int_timestamp
                    os.utime(outpath, (t, t))
