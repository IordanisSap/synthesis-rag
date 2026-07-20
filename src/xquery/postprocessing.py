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