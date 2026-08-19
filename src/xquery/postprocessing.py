import re


def postprocess_xquery(xquery_string: str, database_config: dict) -> str:
    """
    Post-processes the XQuery string by replacing equality comparisons with 'contains' function calls
    and setting the collection name.

    Args:
        xquery_string (str): The original XQuery string.
        database_config (dict): Configuration dictionary containing the collection path.
    Returns:
        str: The modified XQuery string after post-processing.
    """
    xquery_with_contains = to_case_insensitive_contains(xquery_string)
    final_xquery = set_xquery_collection(xquery_with_contains, database_config)
    
    return final_xquery


_VAR = r"\$[A-Za-z_][\w\-]*"
_STEP = r"@?[A-Za-z_][\w\-]*(?::[A-Za-z_][\w\-]*)?"
_FIELD = rf"(?:{_VAR}(?:/{_STEP})*|{_STEP}(?:/{_STEP})*)"

_PATTERN = re.compile(
    rf"(\[|\(|\band\b|\bor\b|\bwhere\b|\bsatisfies\b)(\s*)({_FIELD})\s*=\s*"
    r"('(?:[^']|'')*'|\"(?:[^\"]|\"\")*\")"
)

def to_case_insensitive_contains(xquery_string: str) -> str:
    """
    Converts exact string-equality comparisons in an XQuery string
    (e.g. Name = 'X') into case-insensitive contains() calls
    (e.g. contains(lower-case(Name), lower-case('X'))).

    Only rewrites comparisons where the right-hand side is a quoted
    string literal, immediately following a predicate boundary
    ('[', '(', 'and', 'or'). Numeric/date comparisons, non-'=' operators,
    and comparisons it can't confidently anchor are left untouched.
    """
    def _replace(match: re.Match) -> str:
            boundary, ws, field, literal = match.groups()
            # Use explicit existential quantification (some $i in ... satisfies) 
            # to handle fields that resolve to a sequence of multiple nodes.
            return f"{boundary}{ws}(some $i in {field} satisfies contains(lower-case($i), lower-case({literal})))"

    return _PATTERN.sub(_replace, xquery_string)


def set_xquery_collection(xquery: str, database_config: dict) -> str:
    """
    Sets the collection name in the XQuery string.

    Args:
        xquery (str): The original XQuery string.
        database_config (dict): Configuration dictionary containing the collection path.
    Returns:
        str: The modified XQuery string with the collection name set.
    """
    modified_xquery = xquery.replace("$col", f"'{database_config['base_path']}/{database_config['workdir']}'")
    
    return modified_xquery


