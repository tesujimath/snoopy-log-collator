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
import os.path
import re
import sys

class Collator(object):
    def __init__(self, config, mapper):
        self._config = config
        self._mapper = mapper

    def _output_path(self, filename):
        if os.path.isabs(filename):
            return os.path.join(self._config.hostdir, filename[1:])
        else:
            return os.path.join(self._config.hostdir, filename)

    def _epoch_t(self, dt):
        epoch = datetime.fromtimestamp(0, self._config.utc_tzinfo)
        t = (dt - epoch).total_seconds()
        sys.stderr.write('epoch from %s to %s = %d\n' % (str(epoch), str(dt), t))
        return t

    def command(self, timestamp, fields, command):
        filename = fields['filename']
        if not os.path.isabs(filename):
            filename = os.path.normpath(os.path.join(fields['cwd'], filename))
        user = self._mapper.username(int(fields['uid']))
        if self._mapper.exists(filename):
            output_path = self._output_path(filename)
            if not os.path.exists(output_path):
                output_dir = os.path.dirname(output_path)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
            with open(output_path, 'a') as outf:
                outf.write('%s %s %s\n' % (timestamp.strftime('%Y%m%d-%H:%M:%S'), user, command))
            t = self._epoch_t(timestamp)
            os.utime(output_path, (t, t))
