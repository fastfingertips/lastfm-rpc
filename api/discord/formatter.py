from loguru import logger

from constants.project import RPC_LINE_LIMIT, RPC_XCHAR


def format_rpc_text(lines: dict, limit: int = RPC_LINE_LIMIT, xchar: str = RPC_XCHAR) -> str | None:
    """
    Formats multi-line text for Discord RPC hover previews using a padding character
    to force line wraps (Discord doesn't natively support newlines in hover text).

    Args:
        lines (dict): A dictionary where values are strings to be displayed as separate lines.
        limit (int): The character limit per line for wrapping.
        xchar (str): The specific wide character to use for padding.

    Returns:
        str: A single formatted string for Discord RPC.
    """
    logger.debug(f"Formatting RPC text for keys: {list(lines.keys())}")

    if not lines:
        return None

    result_text = ""

    # We only pad if there's something to "wrap" to the next line
    should_pad = len(lines) > 1

    for key in lines:
        content = lines[key]
        # Ensure string and add a space at the end for slightly better look
        line = f"{str(content).strip()} "

        if should_pad:
            # Padding calculation:
            # Uppercase characters are typically wider in Discord's font.
            # This heuristic helps maintain alignment across different character widths.
            padding_count = limit - len(line) - sum(c.isupper() for c in line)

            if padding_count > 0:
                line += xchar * padding_count

        result_text += f"{line} "

    # Discord has a strict 128 character limit for hover text (small_text/large_text)
    if len(result_text) > 128:
        logger.warning(f"RPC text too long ({len(result_text)}), stripping padding to fit.")
        result_text = result_text.replace(xchar, "")

        # If still too long, hard truncate
        if len(result_text) > 128:
            result_text = result_text[:125] + "..."

    final_text = result_text.strip()
    return final_text if final_text else None
