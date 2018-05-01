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
import os.path
import pwd
import re
import subprocess
import sys

class Mapper(object):
    def __init__(self):
        self._rpm_by_path = {}
        self._yum_repos_by_rpm = {}
        self._username = {}
        self._isfile = {}
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

    def isfile(self, path):
        """Whether path is a regular file (or symlink to one) in the filesystem."""
        if path in self._isfile:
            isfile = self._isfile[path]
        else:
            isfile = os.path.isfile(path)
            self._isfile[path] = isfile
        return isfile

    def rpm(self, path):
        if path in self._rpm_by_path:
            package = self._rpm_by_path[path]
        else:
            package = None
            if os.path.exists(path):
                rpm = subprocess.Popen(["rpm", "-qf", "--qf", "%{NAME}\n", path], stdout = subprocess.PIPE, universal_newlines=True)
                line = rpm.stdout.readline().rstrip('\n')
                if not line.endswith('is not owned by any package'):
                    package = line
            self._rpm_by_path[path] = package
        return package

    def yum_repos(self, rpm):
        if rpm in self._yum_repos_by_rpm:
            repos = self._yum_repos_by_rpm[rpm]
        else:
            repos = set()
            yum = subprocess.Popen(["yum", "info", rpm], stdout = subprocess.PIPE, stderr = subprocess.PIPE, universal_newlines=True)
            for line in yum.stdout:
                m = re.match(r"""(From )?[Rr]epo\s*:\s*(\S*)""", line)
                if m:
                    repos.add(m.group(2))
            if len(repos) == 0:
                errorline = yum.stderr.read()
                if errorline.startswith('Error'):
                    sys.stderr.write('Mapper::yum_repo(%s) %s' % (rpm, errorline))
            self._yum_repos_by_rpm[rpm] = repos
        return repos

    def excluded(self, path, cls, config):
        """Look up config and return whether this path is excluded for cls."""
        if cls not in self._excluded:
            self._excluded[cls] = {}
        excluded_for_class = self._excluded[cls]
        if path in excluded_for_class:
            return excluded_for_class[path]
        else:
            if config.exclude_file(cls, path):
                excluded = True
            else:
                package = self.rpm(path)
                if package is None:
                    excluded = False
                elif config.include_rpm(cls, package):
                    excluded = False
                elif config.exclude_rpm(cls, package):
                    excluded = True
                else:
                    repos = self.yum_repos(package)
                    if len(repos) == 0:
                        excluded = False
                    elif config.exclude_any_yum_repos(cls, repos):
                        excluded = True
                    else:
                        excluded = False
            excluded_for_class[path] = excluded
        return excluded
