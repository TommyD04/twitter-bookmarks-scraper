import json


def load_browser_cookies(path: str) -> dict[str, str]:
    """Parse a browser-exported cookie file and return a {name: value} dict.

    Supports two formats:
    - JSON array of objects with 'name' and 'value' fields (EditThisCookie, Cookie Editor, etc.)
    - Netscape cookies.txt (tab-separated lines)
    """
    with open(path) as f:
        content = f.read()

    stripped = content.strip()

    # Try JSON first
    if stripped.startswith("["):
        try:
            data = json.loads(stripped)
            return {cookie["name"]: cookie["value"] for cookie in data}
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Invalid JSON cookie file: {e}") from e

    # Fall back to Netscape cookies.txt
    cookies = {}
    for line in stripped.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        name, value = parts[5], parts[6]
        cookies[name] = value

    if not cookies:
        raise ValueError(f"No cookies found in {path}")

    return cookies
