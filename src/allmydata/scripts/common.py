
import os, sys, urllib
from twisted.python import usage


class BaseOptions:
    optFlags = [
        ["quiet", "q", "Operate silently."],
        ["version", "V", "Display version numbers and exit."],
        ]

    def opt_version(self):
        import allmydata
        print allmydata.get_package_versions_string()
        sys.exit(0)


class BasedirMixin:
    optFlags = [
        ["multiple", "m", "allow multiple basedirs to be specified at once"],
        ]

    def postOptions(self):
        if not self.basedirs:
            raise usage.UsageError("<basedir> parameter is required")
        if self['basedir']:
            del self['basedir']
        self['basedirs'] = [os.path.abspath(os.path.expanduser(b))
                            for b in self.basedirs]

    def parseArgs(self, *args):
        self.basedirs = []
        if self['basedir']:
            self.basedirs.append(self['basedir'])
        if self['multiple']:
            self.basedirs.extend(args)
        else:
            if len(args) == 0 and not self.basedirs:
                if sys.platform == 'win32':
                    from allmydata.windows import registry
                    self.basedirs.append(registry.get_base_dir_path())
                else:
                    self.basedirs.append(os.path.expanduser("~/.tahoe"))
            if len(args) > 0:
                self.basedirs.append(args[0])
            if len(args) > 1:
                raise usage.UsageError("I wasn't expecting so many arguments")

class NoDefaultBasedirMixin(BasedirMixin):
    def parseArgs(self, *args):
        # create-client won't default to --basedir=~/.tahoe
        self.basedirs = []
        if self['basedir']:
            self.basedirs.append(self['basedir'])
        if self['multiple']:
            self.basedirs.extend(args)
        else:
            if len(args) > 0:
                self.basedirs.append(args[0])
            if len(args) > 1:
                raise usage.UsageError("I wasn't expecting so many arguments")
        if not self.basedirs:
            raise usage.UsageError("--basedir must be provided")

DEFAULT_ALIAS = "tahoe"

def get_alias(aliases, path, default):
    # transform "work:path/filename" into (aliases["work"], "path/filename")
    # We special-case URI:
    if path.startswith("URI:"):
        # The only way to get a sub-path is to use URI:blah:./foo, and we
        # strip out the :./ sequence.
        sep = path.find(":./")
        if sep != -1:
            return path[:sep], path[sep+3:]
        return path, ""
    colon = path.find(":")
    if colon == -1:
        # no alias
        return aliases[default], path
    alias = path[:colon]
    if "/" in alias:
        # no alias, but there's a colon in a dirname/filename, like
        # "foo/bar:7"
        return aliases[default], path
    return aliases[alias], path[colon+1:]

def escape_path(path):
    segments = path.split("/")
    return "/".join([urllib.quote(s) for s in segments])
