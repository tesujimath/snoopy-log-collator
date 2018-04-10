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
import pytoml as toml
import pytz
import sys
import tzlocal

def bare_hostname():
    """Hostname without domain."""
    return os.uname()[1].split('.')[0]

def expand(s):
    return os.path.expanduser(os.path.expandvars(s))

class ConfigError(Exception):

    def __init__(self, filename, msg):
        self.filename = filename
        self.msg = msg

    def __str__(self):
        return('Configuration error %s: %s' % (self.filename, self.msg))

class Config(object):

    def __init__(self, args):
        filename = None
        if args.config:
            filename = args.config
            if not os.path.exists(filename):
                raise ConfigError('%s' % filename, 'file not found')
        else:
            attempt_files = [
                os.path.expanduser('~/.snoopy-log-collator.toml'),
                '/etc/snoopy-log-collator.toml',
            ]
            for attempt in attempt_files:
                if os.path.exists(attempt):
                    filename = attempt
                    break
            if filename is None:
                raise ConfigError('', 'none of %s found' % ', '.join(attempt_files))

        with open(filename, 'rb') as f:
            try:
                self._config = toml.load(f)
            except toml.TomlError as e:
                raise ConfigError(filename, 'TOML error at line %d' % e.line)

    @property
    def hostdir(self):
        return os.path.join(expand(self._config['collation-dir']), bare_hostname())

    @property
    def logdir(self):
        return expand(self._config['log-dir'])

    def include_rpm(self, name):
        if 'include' in self._config:
            include = self._config['include']
            return 'rpm' in include and name in include['rpm']
        else:
            return False

    def exclude_rpm(self, name):
        if 'exclude' in self._config:
            exclude = self._config['exclude']
            return 'rpm' in exclude and name in exclude['rpm']
        else:
            return False

    def exclude_yum_repo(self, name):
        if 'exclude' in self._config:
            exclude = self._config['exclude']
            return 'yum-repo' in exclude and name in exclude['yum-repo']
        else:
            return False
