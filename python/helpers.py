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
def color(t):
    red = "\033[31m"
    green = "\033[32m"
    blue = "\033[34m"
    reset = "\033[39m"
    utterances = t.split()

    if "Sell" in utterances:
        # figure out the list-indices of occurences of "one"
        idxs = [i for i, x in enumerate(utterances) if x.startswith("Sell")]

        # modify the occurences by wrapping them in ANSI sequences
        for i in idxs:
            utterances[i] = red + utterances[i] + reset

    if "Buy" in utterances:
        idxs = [i for i, x in enumerate(utterances) if x.startswith("Buy")]
        for i in idxs:
            utterances[i] = green + utterances[i] + reset

    if "\u25B2" in utterances:  # up arrow
        idxs = [i for i, x in enumerate(utterances) if x.startswith("\u25B2")]
        for i in idxs:
            utterances[i] = green + utterances[i] + reset

    if "\u25BC" in utterances:  # down arrow
        idxs = [i for i, x in enumerate(utterances) if x.startswith("\u25BC")]
        for i in idxs:
            utterances[i] = red + utterances[i] + reset

    # join the list back into a string and print
    return " ".join(utterances)
