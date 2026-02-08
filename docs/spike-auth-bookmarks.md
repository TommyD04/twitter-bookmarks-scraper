# Spike: Auth (A1) + Bookmarks API (A2)

## Context

We need to authenticate with Twitter/X and fetch bookmarks programmatically. Both A1 and A2 were flagged unknowns in Shape A.

## Findings

### Library Comparison

| Library | Bookmarks? | Auth Method | Maintained? | Limit |
|---------|-----------|-------------|-------------|-------|
| **twikit** | Yes | Username/password + cookie file | Yes (v2.3.1, Feb 2025) | No hard cap |
| tweepy | Yes | OAuth 2.0 PKCE (dev account needed) | Yes | **800 max** |
| twitter-api-client | Yes | Browser cookies | Yes | No hard cap |
| twscrape | Partial | Account cookies in DB | Yes | No hard cap |
| snscrape | No | N/A | Poorly maintained | N/A |

### Recommendation: twikit

**twikit** is the clear winner:
- Built-in `get_bookmarks(count=20, cursor=None)` with `.next()` pagination
- Login with username/email/password — saves cookies to JSON for session persistence
- No API key or developer account needed
- Async Python (asyncio)
- Returns rich Tweet objects: `id`, `text`, `full_text`, `created_at`, `user`, `media`, `in_reply_to`, `view_count`, `retweet_count`, `favorite_count`, `reply_count`, `bookmark_count`

### Auth Mechanism (A1 resolved)

```python
from twikit import Client
client = Client('en-US')
await client.login(
    auth_info_1='username',
    auth_info_2='email@example.com',
    password='password',
    cookies_file='cookies.json'
)
```

- First run: full login flow, saves cookies
- Subsequent runs: loads from `cookies.json`, no re-login needed

### Bookmarks Endpoint (A2 resolved)

- Uses Twitter's internal GraphQL endpoint: `GET https://x.com/i/api/graphql/{queryId}/Bookmarks`
- twikit abstracts this entirely — just call `get_bookmarks()`
- ~20 bookmarks per page, cursor-based pagination
- Rate limits: ~50-180 req/15 min window (undocumented but empirical)
- At 20/page with 2s delay: ~2000 bookmarks in ~3-4 minutes

### Thread Resolution (A3 detail)

Bookmarks response includes `in_reply_to` and `conversation_id` but NOT the full thread. Separate calls needed:
- `get_tweet_by_id(tweet_id)` to walk parent chain
- Or use `TweetDetail` GraphQL endpoint for full thread in one call
- Cache fetched tweets to avoid redundant requests across bookmarks in same thread

### Anti-Scraping Notes

Twitter rotates GraphQL `queryId` values every 2-4 weeks. Using twikit abstracts this — the library handles ID rotation. Raw HTTP scraping would require 10-15 hours/month of upkeep.

## Conclusion

Both flags are resolved. twikit provides concrete, tested mechanisms for auth and bookmark fetching. No unknowns remain.
