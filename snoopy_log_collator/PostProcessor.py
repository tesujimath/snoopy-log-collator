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
import os.path
import pendulum
import sys

from .Config import Config
from .Mapper import Mapper
from .KeyedReader import KeyedReader
from .KeyedReaderTree import KeyedReaderTree
from .util import bare_hostname, append_and_set_timestamp

class PostProcessor(object):

    def __init__(self, args):
        self._config = Config(args)
        self._mapper = Mapper()

    def _get_collated_files(self, cls, host, paths):
        collationdir = self._config.host_collation_dir(cls, host)
        n = len(collationdir)
        for root, dirs, files in os.walk(collationdir):
            for filename in files:
                path = os.path.join(root, filename)[n:]
                if path != '/.collated':
                    if path not in paths:
                        paths[path] = set()
                    paths[path].add(host)

    def list_packages(self, classes):
        paths = {}
        for cls in classes if len(classes) > 0 else ['all']:
            self._get_collated_files(cls, bare_hostname(), paths)
        for path in sorted(paths.keys()):
            package = self._mapper.rpm(path)
            repos = self._mapper.yum_repos(package) if package is not None else None
            if package is not None:
                print('%s:%s:%s' % (path, str(package), str(repos)))

    def list_files(self, classes):
        paths = {}
        for cls in classes if len(classes) > 0 else ['all']:
            for host in self._config.collated_hosts(cls):
                self._get_collated_files(cls, host, paths)
        for path in sorted(paths.keys()):
            print('%s %s' % (path, ','.join(sorted(list(paths[path])))))

    def list_excluded(self, classes, purge=False):
        paths = {}
        for cls in classes if len(classes) > 0 else ['all']:
            root = self._config.localhost_collation_dir(cls)
            self._get_collated_files(cls, bare_hostname(), paths)
            for path in paths:
                if self._mapper.excluded(path, cls, self._config):
                    if purge:
                        filepath = os.path.join(root, os.path.relpath(path, '/'))
                        print('rm %s' % filepath)
                        os.remove(filepath)
                    else:
                        print(path)
            if purge:
                self._purge_empty_dirs(cls)

    def _purge_empty_dirs(self, cls):
        for root, dirs, files in os.walk(self._config.localhost_collation_dir(cls), topdown=False):
            for dirname in dirs:
                dirpath = os.path.join(root, dirname)
                try:
                    os.rmdir(dirpath)
                    print('rmdir %s ' % dirpath)
                except:
                    pass

    @classmethod
    def timestamp(cls, line):
        """Return just the timestamp from a line in a collated file."""
        return pendulum.parse(line.split(maxsplit=1)[0], tz=pendulum.now().timezone)

    def consolidate(self):
        for cls in self._config.classes:
            hosts = self._config.collated_hosts(cls)
            all_relpaths = {}
            for host in hosts:
                collationdir = self._config.host_collation_dir(cls, host)
                n = len(collationdir) + 1
                for root, dirs, files in os.walk(collationdir):
                    for filename in files:
                        relpath = os.path.join(root, filename)[n:]
                        if relpath not in all_relpaths:
                            all_relpaths[relpath] = []
                        all_relpaths[relpath].append(host)
            for relpath, hosts in all_relpaths.items():
                krt = KeyedReaderTree()
                inpaths = [os.path.join(self._config.host_collation_dir(cls, host), relpath) for host in hosts]
                outpath = os.path.join(self._config.consolidation_dir(cls), relpath)
                for inpath in inpaths:
                    krt.insert(KeyedReader(inpath, self.__class__.timestamp))
                if os.path.exists(outpath):
                    krt.insert(KeyedReader(outpath, self.__class__.timestamp))
                outdir = os.path.dirname(outpath)
                if not os.path.exists(outdir):
                    os.makedirs(outdir)
                outpathnew = '%s.new' % outpath
                with open(outpathnew, 'w') as f:
                    for line in krt.lines():
                        f.write(line)
                os.rename(outpathnew, outpath)
                # set the timestamp according to the last key
                t = krt.lastkey.int_timestamp
                os.utime(outpath, (t, t))
            self._finalize_consolidated(cls)

    def _finalize_consolidated(self, cls):
        """Ensure the collated files don't get consolidated again, by moving them."""
        hosts = self._config.collated_hosts(cls)
        all_relpaths = {}
        for host in hosts:
            collationdir = self._config.host_collation_dir(cls, host)
            n = len(collationdir) + 1
            for root, dirs, files in os.walk(collationdir, topdown=False):
                for filename in files:
                    relpath = os.path.join(root, filename)[n:]
                    inpath = os.path.join(collationdir, relpath)
                    outpath = os.path.join(self._config.consolidation_dir(cls, host), relpath)
                    outdir = os.path.dirname(outpath)
                    if not os.path.exists(outdir):
                        os.makedirs(outdir)
                    if not os.path.exists(outpath):
                        os.rename(inpath, outpath)
                    else:
                        append_and_set_timestamp(inpath, outpath)
                        os.remove(inpath)
                # remove all the directories, which should be empty now
                os.rmdir(root)
