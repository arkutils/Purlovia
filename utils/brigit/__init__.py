# -*- coding: utf-8 -*-
# Copyright (C) 2011 by Florian Mounier, Kozea
# This file is part of brigit, licensed under a 3-clause BSD license.
"""
briGit - Very simple git wrapper module

"""

import logging
import os
import re
from datetime import datetime
from subprocess import run

CMD_TIMEOUT = 5 * 60  # 5 minutes should be plenty for any normal Git op

handler = logging.StreamHandler()


def kebab_case(s):
    return re.sub('([A-Z]+)', r'-\1', s).lower()


class NullHandler(logging.Handler):
    """Handler that do nothing"""
    def emit(self, record):
        """Do nothing"""


class GitException(Exception):
    """Exception raised when something went wrong for git"""
    def __init__(self, message):
        super(GitException, self).__init__(message)


class RawGit(object):
    """Git command wrapper"""
    def __init__(self, git_path, encoding="utf-8"):
        """Init a Git wrapper with an instance"""
        self.path = git_path
        self.encoding = encoding

    def __call__(self, command, *args, **kwargs):
        """Run a command with args as arguments."""
        full_command = (('git', kebab_case(command)) + tuple(
            (u"--%s=%s" % (key, value) if len(key) > 1 else u"-%s %s" % (key, value)) for key, value in kwargs.items()) + args)
        self.logger.debug(u"> %s" % u' '.join(full_command))
        result = run(full_command, cwd=self.path, text=True, capture_output=True, timeout=CMD_TIMEOUT, encoding=self.encoding)
        self.logger.debug("%s" % result.stdout)
        if result.returncode != 0:
            if result.stderr:
                self.logger.error("%s" % result.stderr)
            raise GitException("%s has returned %d - error was %s" % (' '.join(full_command), result.returncode, result.stderr))
        else:
            if result.stderr:
                self.logger.warning("%s" % result.stderr)
        return result.stdout

    def __getattr__(self, name):
        """Any method not implemented will be executed as is."""
        return lambda *args, **kwargs: self(name, *args, **kwargs)


class Git(RawGit):
    """Utility class overloading most used functions"""
    def __init__(self, git_path, remote=None, quiet=True, bare=False, logger=None):
        """Init the repo or clone the remote if remote is not None."""
        if "~" in git_path:
            git_path = os.path.expanduser(git_path)

        super(Git, self).__init__(git_path)

        dirpath = os.path.dirname(self.path)
        basename = os.path.basename(self.path)
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger("brigit")
            if not quiet:
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.addHandler(NullHandler())

        if not os.path.exists(self.path):
            # Non existing repository
            if remote:
                if not os.path.exists(dirpath):
                    os.makedirs(dirpath)
                self.path = dirpath
                # The '--recursive' option will clone all submodules, if any
                self.clone(remote, basename, '--recursive')
                self.path = git_path
            else:
                os.makedirs(self.path)
                if bare:
                    self.init('--bare')
                else:
                    self.init()
        self.remote_path = remote

    def pretty_log(self, *args, **kwargs):
        """Return the log as a list of dict"""
        kwargs["pretty"] = "format:%H;;%an;;%ae;;%at;;%s"
        for line in self.log(*args, **kwargs).split("\n"):
            fields = line.split(";;")
            yield {
                'hash': fields[0],
                'author': {
                    'name': fields[1],
                    'email': fields[2]
                },
                'datetime': datetime.fromtimestamp(float(fields[3])),
                'message': fields[4]
            }
