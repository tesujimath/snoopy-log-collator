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

class Collator(object):
    def __init__(self, config, mapper):
        self._config = config
        self._mapper = mapper

    def _output_path(self, cls, filename):
        if os.path.isabs(filename):
            return os.path.join(self._config.collationdir(cls), filename[1:])
        else:
            return os.path.join(self._config.collationdir(cls), filename)

    def command(self, timestamp, fields, command):
        filename = fields['filename']
        if os.path.isabs(filename):
            filepath = filename
        else:
            filepath = os.path.normpath(os.path.join(fields['cwd'], filename))
        user = self._mapper.username(int(fields['uid']))
        if self._mapper.isfile(filepath):
            for cls in self._config.classes:
                if not self._mapper.excluded(filepath, cls, self._config):
                    output_path = self._output_path(cls, filepath)
                    if not os.path.exists(output_path):
                        output_dir = os.path.dirname(output_path)
                        if not os.path.exists(output_dir):
                            os.makedirs(output_dir)
                    with open(output_path, 'a') as outf:
                        outf.write('%s %s %s\n' % (timestamp.strftime('%Y%m%d-%H:%M:%S'), user, command))
                    t = timestamp.int_timestamp
                    os.utime(output_path, (t, t))
