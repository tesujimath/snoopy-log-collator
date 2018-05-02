#!/usr/bin/env python
#
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

import argparse
import sys

from snoopy_log_collator.Config import ConfigError
from snoopy_log_collator.PostProcessor import PostProcessor
from snoopy_log_collator.Scanner import Scanner

def main():
    parser = argparse.ArgumentParser(description='collate snoopy logfiles')
    parser.add_argument('--list-files', action='store', metavar='CLASS', help='list collated files for CLASS')
    parser.add_argument('--list-packages', action='store', metavar='CLASS', help='list collated files for CLASS which have a package')
    parser.add_argument('--list-excluded', action='store', metavar='CLASS', help='list collated files for CLASS which are excluded')
    parser.add_argument('--purge-excluded', action='store', metavar='CLASS', help='remove collated files for CLASS which are excluded')
    parser.add_argument('-c', '--config', metavar='FILE', help='configuration file')
    args = parser.parse_args()

    try:
        if args.list_files:
            p = PostProcessor(args)
            p.list_files(args.list_files)
        elif args.list_packages:
            p = PostProcessor(args)
            p.list_packages(args.list_packages)
        elif args.list_excluded:
            p = PostProcessor(args)
            p.list_excluded(args.list_excluded)
        elif args.purge_excluded:
            p = PostProcessor(args)
            p.list_excluded(args.purge_excluded, purge=True)
        else:
            scanner = Scanner(args)
            scanner.scan()
    except ConfigError as e:
        sys.stderr.write('%s\n' % e)
        sys.exit(1)

if __name__ == '__main__':
    main()
