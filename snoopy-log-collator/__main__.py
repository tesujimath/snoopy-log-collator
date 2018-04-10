#!/usr/bin/env python

from datetime import datetime
import errno
import gzip
import os
import pwd
import pytz
import re
import string
import subprocess
import sys
import tzlocal

class Mapper:
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

def get_tagged_fields(s):
    """Extract tagged snoopy fields as a dict."""
    # Alas embedded spaces cause difficulty, as snoopy doesn't quote them in the logfile.
    # We therefore split on a cunning regex
    cunningRE = re.compile(r"""(\s+\w+:)""")
    cunningSplit = re.split(cunningRE, s)
    toks = cunningSplit[0].split(':', 1) + cunningSplit[1:]
    fields = {}
    for i in range(len(toks) / 2):
        tag = toks[2 * i].lstrip().rstrip(':')
        value = toks[2 * i + 1]
        fields[tag] = value
    if re.search('gfortran compiled', s):
        sys.stderr.write('extracted %s from %s\n' % (str(fields), s))
    return fields

def bare_hostname():
    """Hostname without domain."""
    return os.uname()[1].split('.')[0]

def datetime_to_epoch(dt, tzinfo):
    epoch = datetime.fromtimestamp(0, tzinfo)
    return (dt - epoch).total_seconds()

def get_collationdir():
    return '/home/guestsi/junk/snoopy-collation/%s' % bare_hostname()

def get_output_path(collationdir, filename):
    if os.path.isabs(filename):
        return os.path.join(collationdir, filename[1:])
    else:
        return os.path.join(collationdir, filename)

def collate_log(logpath, logfile_dt, collationdir, mapper, local_tzinfo):
    loglineRE = re.compile(r"""^(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\w+)\s+\w+\[(\d+)\]:\s+\[([^\]]*)\]:\s+(.*)$""")
    logf = gzip.open(logpath)
    try:
        for logline in logf:
            m = loglineRE.match(logline)
            if m:
                # infer the year for the timestamp, which is usually the same as the logfile year,
                # except when we roll over from Dec to Jan
                timestamp_s = m.group(1)
                timestamp_year = logfile_dt.year - 1 if timestamp_s.startswith('Dec') and logfile_dt.month == 1 else logfile_dt.year
                naive = datetime.strptime('%d %s' % (timestamp_year, timestamp_s), '%Y %b %d %H:%M:%S')
                timestamp = datetime(naive.year, naive.month, naive.day, naive.hour, naive.minute, naive.second, tzinfo=local_tzinfo)

                fields = get_tagged_fields(m.group(4))
                args = m.group(5).rstrip()
                filename = fields['filename']
                if not os.path.isabs(filename):
                    filename = os.path.normpath(os.path.join(fields['cwd'], filename))
                user = mapper.username(int(fields['uid']))
                if mapper.exists(filename):
                    output_path = get_output_path(collationdir, filename)
                    if not os.path.exists(output_path):
                        output_dir = os.path.dirname(output_path)
                        if not os.path.exists(output_dir):
                            os.makedirs(output_dir)
                        package = mapper.package(filename)
                        if package is not None:
                            with open(output_path, 'w') as outf:
                                outf.write('package: %s\n' % package)
                    with open(output_path, 'a') as outf:
                        outf.write('%s %s %s\n' % (timestamp.strftime('%Y%m%d-%H:%M:%S'), user, args))
                    t = datetime_to_epoch(timestamp, local_tzinfo)
                    os.utime(output_path, (t, t))
            else:
                print("failed on %s" % logline.rstrip('\n'))
    finally:
        logf.close()

def get_last_collation(collationdir, local_tzinfo):
    timestampRE = re.compile(r"""^(\d\d\d\d)(\d\d)(\d\d)$""")
    try:
        with open(os.path.join(collationdir, '.processed')) as f:
            m = timestampRE.match(f.read())
            if m:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=local_tzinfo)
        return None
    except IOError, ValueError:
        return None

def set_last_collation(collationdir, dt):
    with open(os.path.join(collationdir, '.processed'), 'w') as f:
        f.write('%s\n' % dt.strftime('%Y%m%d'))

def main():
    #logdir = '/var/log'
    logdir = '/home/guestsi/junk/snoopy-log'
    mapper = Mapper()
    local_tzinfo = pytz.timezone(str(tzlocal.get_localzone()))
    collationdir = get_collationdir()
    last_collation_dt = get_last_collation(collationdir, local_tzinfo)

    # important to process logfiles in order, so timestamps are preserved
    for entry in sorted(os.listdir(logdir)):
        snoopyLogRE = re.compile(r"""^snoopy-(\d\d\d\d)(\d\d)(\d\d).gz$""")
        m = snoopyLogRE.match(entry)
        if m:
            logfile_year = int(m.group(1))
            logfile_month = int(m.group(2))
            logfile_day = int(m.group(3))
            logfile_dt = datetime(logfile_year, logfile_month, logfile_day, tzinfo=local_tzinfo)
            if last_collation_dt is None or last_collation_dt < logfile_dt:
                sys.stderr.write('collating %s\n' % entry)
                collate_log(os.path.join(logdir, entry), logfile_dt, collationdir, mapper, local_tzinfo)
                last_collation_dt = logfile_dt
                set_last_collation(collationdir, last_collation_dt)
            else:
                sys.stderr.write('skipping %s\n' % entry)

if __name__ == '__main__':
    main()
