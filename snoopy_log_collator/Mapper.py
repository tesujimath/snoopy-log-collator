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
import re
import subprocess

class Mapper(object):
    def __init__(self):
        self._rpm_by_path = {}
        self._yum_repo_by_rpm = {}
        self._username = {}
        self._exists = {}
        self._excluded = {}

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

    def rpm(self, path):
        if path in self._rpm_by_path:
            package = self._rpm_by_path[path]
        else:
            rpm = subprocess.Popen(["rpm", "-qf", "--qf", "%{NAME}\n", path], stdout = subprocess.PIPE)
            line = rpm.stdout.readline().rstrip('\n')
            if line.endswith('is not owned by any rpm'):
                package = None
            else:
                package = line
            self._rpm_by_path[path] = package
        return package

    def yum_repo(self, rpm):
        if rpm in self._yum_repo_by_rpm:
            repo = self._yum_repo_by_rpm[rpm]
        else:
            repo = None
            yum = subprocess.Popen(["yum", "info", rpm], stdout = subprocess.PIPE)
            for line in yum.stdout:
                m = re.match(r"""From repo\s*:\s*(\S*)""", line)
                if m:
                    repo = m.group(1)
                    break
            self._yum_repo_by_rpm[rpm] = repo
        return repo

    def excluded(self, path, config):
        """Look up config and return whether this path is excluded."""
        if path in self._excluded:
            return self._excluded[path]
        else:
            package = self.rpm(path)
            if package is None:
                excluded = False
            elif config.include_rpm(package):
                excluded = False
            elif config.exclude_rpm(package):
                excluded = True
            else:
                repo = self.yum_repo(package)
                if repo is None:
                    excluded = False
                elif config.exclude_yum_repo(repo):
                    excluded = True
                else:
                    excluded = False
            self._excluded[path] = excluded
            return excluded
