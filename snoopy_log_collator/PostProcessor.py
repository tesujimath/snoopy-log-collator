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

import os

from .Config import Config
from .Mapper import Mapper

class PostProcessor(object):

    def __init__(self, args):
        self._config = Config(args)
        self._mapper = Mapper()

    def _get_collated_files(self):
        collated = []
        n = len(self._config.hostdir)
        for root, dirs, files in os.walk(self._config.hostdir):
            for filename in files:
                path = os.path.join(root, filename)[n:]
                if path != '/.processed':
                    collated.append(path)
        return collated

    def list_packages(self):
        for path in sorted(self._get_collated_files()):
            package = self._mapper.rpm(path)
            repo = self._mapper.yum_repo(package) if package is not None else None
            print('%s:%s:%s' % (str(repo), str(package), path))
