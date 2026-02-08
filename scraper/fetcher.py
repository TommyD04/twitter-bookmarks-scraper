async def fetch_bookmarks(client) -> list[dict]:
    result = await client.get_bookmarks(count=20)

    bookmarks = []
    for tweet in result:
        bookmarks.append({
            "id": tweet.id,
            "text": tweet.text,
            "author": f"{tweet.user.name} (@{tweet.user.screen_name})",
            "handle": tweet.user.screen_name,
            "created_at": tweet.created_at,
            "likes": tweet.favorite_count,
            "retweets": tweet.retweet_count,
            "replies": tweet.reply_count,
            "url": f"https://x.com/{tweet.user.screen_name}/status/{tweet.id}",
            "has_media": bool(tweet.media),
            "is_reply": tweet.in_reply_to is not None,
        })

    return bookmarks
