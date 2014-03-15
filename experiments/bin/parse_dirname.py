import sys
import re


def parse_dirname(dirname, field):
    parts = dirname.split("/")
    match = re.search("%s([^A-Z]+)" % field, parts[-1])
    if match is None:
        raise Exception("Field '%s' not matched in '%s'" %  (field, dirname))
    return match.groups()[0]

# print sys.argv
print parse_dirname(sys.argv[1], sys.argv[2])
