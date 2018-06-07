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
import re
import sys

from .util import bare_hostname

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
        self._filename = None
        if args.config:
            self._filename = args.config
            if not os.path.exists(self._filename):
                raise ConfigError('%s' % self._filename, 'file not found')
        else:
            attempt_files = [
                os.path.expanduser('~/.snoopy-log-collator.toml'),
                '/etc/snoopy-log-collator.toml',
            ]
            for attempt in attempt_files:
                if os.path.exists(attempt):
                    self._filename = attempt
                    break
            if self._filename is None:
                raise ConfigError('', 'none of %s found' % ', '.join(attempt_files))

        with open(self._filename, 'rb') as f:
            try:
                self._config = toml.load(f)
            except toml.TomlError as e:
                raise ConfigError(self._filename, 'TOML error at line %d, %s' % (e.line, e.message))
        self._validate()

    def _validate(self):
        if 'class' in self._config and 'all' in self._config['class']:
            raise ConfigError(self._filename, 'invalid class "all"')

    def localhost_collation_dir(self, cls):
        return os.path.join(expand(self._config['collation-dir']), cls, bare_hostname())

    def host_collation_dir(self, cls, hostname):
        return os.path.join(expand(self._config['collation-dir']), cls, hostname)

    def consolidation_dir(self, cls, host=None):
        subdir = 'ALL' if host is None else host
        return os.path.join(expand(self._config['consolidation-dir']), cls, subdir)

    @property
    def last_collation_file(self):
        return os.path.join(expand(self._config['collation-dir']), '.%s.collated' % bare_hostname())

    @property
    def logdir(self):
        return expand(self._config['log-dir'])

    @property
    def classes(self):
        return list(self._config['class'])

    @property
    def classes_with_all(self):
        # add the pseudo 'all' class
        return ['all'] + list(self._config['class'])

    def collated_hosts(self, cls):
        return os.listdir(os.path.join(expand(self._config['collation-dir']), cls))

    def _config_for_class(self, cls):
        if 'class' not in self._config or cls not in self._config['class']:
            return None
        else:
            return self._config['class'][cls]

    def exclude_file(self, cls, name):
        config_for_class = self._config_for_class(cls)
        if config_for_class is not None and 'exclude' in config_for_class:
            exclude = config_for_class['exclude']
            if 'file' in exclude:
                for name_re in exclude['file']:
                    if re.search(name_re, name):
                        return True
                return False
            else:
                return False
        else:
            return False

    def include_rpm(self, cls, name):
        config_for_class = self._config_for_class(cls)
        if config_for_class is not None and 'include' in config_for_class:
            include = config_for_class['include']
            if 'rpm' in include:
                for name_re in include['rpm']:
                    if re.search(name_re, name):
                        return True
                return False
            else:
                return False
        else:
            return False

    def exclude_rpm(self, cls, name):
        config_for_class = self._config_for_class(cls)
        if config_for_class is not None and 'exclude' in config_for_class:
            exclude = config_for_class['exclude']
            if 'rpm' in exclude:
                for name_re in exclude['rpm']:
                    if re.search(name_re, name):
                        return True
                return False
            else:
                return False
        else:
            return False

    def exclude_any_yum_repos(self, cls, names):
        config_for_class = self._config_for_class(cls)
        if config_for_class is not None and 'exclude' in config_for_class:
            exclude = config_for_class['exclude']
            if 'yum-repo' in exclude:
                for name_re in exclude['yum-repo']:
                    for name in names:
                        if re.search(name_re, name):
                            return True
                return False
            else:
                return False
        else:
            return False

