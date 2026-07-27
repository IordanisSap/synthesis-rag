def trim_empty_class_fields(fields: list) -> list:
    """
    Returns a list of fields with always-empty fields removed.
    """
    if not isinstance(fields, list):
        return fields

    return [
        field_info 
        for field_info in fields 
        if field_info.get("category") != "always-empty"
    ]
