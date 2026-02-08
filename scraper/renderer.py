def render_bookmark(bookmark: dict, thread: list[dict] | None = None) -> str:
    is_thread = thread is not None and len(thread) > 1
    thread_length = len(thread) if is_thread else 1

    # YAML frontmatter
    text_escaped = bookmark["text"].replace("\\", "\\\\").replace('"', '\\"')
    lines = [
        "---",
        f'author: "{bookmark["author"]}"',
        f'handle: "{bookmark["handle"]}"',
        f'tweet_url: "{bookmark["url"]}"',
        f'date: "{bookmark["created_at"]}"',
        f"likes: {bookmark['likes']}",
        f"retweets: {bookmark['retweets']}",
        f"replies: {bookmark['replies']}",
        f"is_thread: {'true' if is_thread else 'false'}",
        f"thread_length: {thread_length}",
        "---",
        "",
    ]

    if is_thread:
        for i, tweet in enumerate(thread, 1):
            label = f"## Tweet {i} of {thread_length}"
            if i == 1:
                label += " (thread start)"
            elif i == thread_length:
                label += " (bookmarked)"
            lines.append(label)
            lines.append("")
            lines.append(tweet["text"])
            lines.append("")
            for item in tweet.get("media_items", []):
                if item["type"] == "photo":
                    lines.append(f'![image](media/{item["filename"]})')
                else:
                    lines.append(f'[{item["type"]}](media/{item["filename"]})')
                lines.append("")
            if i < thread_length:
                lines.append("---")
                lines.append("")
    else:
        lines.append(f"# @{bookmark['handle']} — {bookmark['created_at']}")
        lines.append("")
        lines.append(bookmark["text"])
        lines.append("")
        for item in bookmark.get("media_items", []):
            if item["type"] == "photo":
                lines.append(f'![image](media/{item["filename"]})')
            else:
                lines.append(f'[{item["type"]}](media/{item["filename"]})')
            lines.append("")

    return "\n".join(lines)


def bookmark_filename(bookmark: dict) -> str:
    return f"@{bookmark['handle']}-{bookmark['id']}.md"
