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

import errno
import os
import pwd
import subprocess
import sys

class Mapper(object):
    def __init__(self):
        self._package = {}
        self._username = {}
        self._exists = {}

    def username(self, uid):
        if uid not in self._username:
            try:
                pw = pwd.getpwuid(uid)
                name = pw[0]
            except KeyError:
                name = str(uid)
            self._username[uid] = name
        else:
            name = self._username[uid]
        return name

    def exists(self, path):
        """Whether path exists in the filesystem."""
        if path in self._exists:
            result = self._exists[path]
        else:
            try:
                s = os.stat(path)
                result = True
            except OSError as e:
                if e.errno == errno.ENOENT or e.errno == errno.EACCES:
                    result = False
                else:
                    raise
            self._exists[path] = result
        return result

    def package(self, path):
        if path in self._package:
            package = self._package[path]
        else:
            rpm = subprocess.Popen(["rpm", "-qf", "--qf", "%{NAME}\n", path], stdout = subprocess.PIPE)
            line = rpm.stdout.readline().rstrip('\n')
            if line.endswith('is not owned by any package'):
                package = None
            else:
                package = line
            self._package[path] = package
        return package
