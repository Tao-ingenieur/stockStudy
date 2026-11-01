"""Board classification for the supported local A-share code universe.

This classifies market segments, not current listing status.
"""

BOARD_FILTERS = ("all", "sh-main", "star", "sz-main", "chinext", "bse", "other")
BOARDS_BY_MARKET = {
    "all": BOARD_FILTERS,
    "sh": ("all", "sh-main", "star", "other"),
    "sz": ("all", "sz-main", "chinext", "other"),
    "bj": ("all",),
    "shsz": ("all", "sh-main", "star", "sz-main", "chinext", "other"),
}


def board_for(market: str, code: str) -> str:
    if len(code) != 6 or not code.isdigit():
        return "other"
    if market == "sh":
        if code.startswith(("688", "689")):
            return "star"
        if code.startswith(("600", "601", "603", "605")):
            return "sh-main"
    elif market == "sz":
        if code.startswith("00"):
            return "sz-main"
        if code.startswith("30"):
            return "chinext"
    elif market == "bj" and code.startswith(("43", "83", "87", "92")):
        return "bse"
    return "other"
