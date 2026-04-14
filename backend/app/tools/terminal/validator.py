def is_safe_command(command: str) -> bool:
    lowered = command.lower()
    blocked_terms = [
        " rm ",
        " del ",
        " rmdir ",
        " format ",
        " shutdown ",
        " taskkill ",
        " explorer ",
    ]

    normalized = f" {lowered} "
    return not any(term in normalized for term in blocked_terms)
