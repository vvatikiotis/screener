#
# helper functions
#

#
def group(strings):
    groups = {}
    for s in map(lambda s: s.split(".")[0], strings):
        prefix, remainder = s.split("_")
        groups.setdefault(prefix, []).append(remainder)
    return groups


#
def sort_lambda(v):
    SORT_ORDER = {"1w": 0, "3d": 1, "1d": 2, "12h": 3, "6h": 4, "4h": 5, "1h": 6}
    return SORT_ORDER[v]


#
def dict_filter(it, *keys):
    for d in it:
        yield dict((k, d[k]) for k in keys)
