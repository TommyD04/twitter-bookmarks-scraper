# Twitter Bookmarks Scraper — Shaping

## Requirements (R)

| ID | Requirement | Status |
|----|-------------|--------|
| R0 | Scrape all historic Twitter/X bookmarks | Core goal |
| R1 | Save each bookmark as a separate markdown file | Core goal |
| R2 | Capture the full thread when a bookmark is part of a thread | Core goal |
| R3 | Download and include all media (images, GIFs, video) | Core goal |
| R4 | Save files to a user-designated output folder | Must-have |
| R5 | Authenticate with Twitter/X to access private bookmarks endpoint | Must-have |
| R6 | Handle Twitter/X rate limiting gracefully | Must-have |
| R7 | Resumable — track progress, skip already-scraped bookmarks on re-run | Must-have |
| R8 | Full metadata in YAML frontmatter (author, handle, date, URL, likes, retweets, reply count) | Must-have |
| R9 | Built in Python | Must-have |
| R10 | Sensible file naming and folder organization | Nice-to-have |

---

## A: twikit + Python CLI

| Part | Mechanism | Flag |
|------|-----------|:----:|
| **A1** | **Auth** — Use `twikit.Client.login()` with username/email/password. Persist session via `cookies.json` so subsequent runs don't re-login. | |
| **A2** | **Bookmark Fetcher** — Call `client.get_bookmarks()`, paginate via `.next()` cursor. ~20 per page. Add 2s delay between pages. Exponential backoff on 429s. | |
| **A3** | **Thread Resolver** — For tweets where `in_reply_to` is set, walk parent chain via `client.get_tweet_by_id()`. Cache fetched tweets to avoid duplicates across bookmarks in the same thread. | |
| **A4** | **Media Downloader** — Download all media URLs from tweet objects (images, GIFs, MP4 video) to `media/` subfolder. Name files `{tweet_id}_{index}.{ext}`. | |
| **A5** | **Markdown Renderer** — Convert each bookmark into `.md` with YAML frontmatter (author, handle, date, URL, likes, retweets, replies, bookmark count) and body with thread text + `![](media/...)` references. | |
| **A6** | **Progress Tracker** — JSON manifest of scraped tweet IDs + last pagination cursor. On re-run, skip known IDs. Resume pagination from saved cursor. | |
| **A7** | **CLI Runner** — `python scrape.py --output ./bookmarks`. Orchestrates: login → fetch bookmarks → resolve threads → download media → render markdown. | |

### Spike Results (see [spike-auth-bookmarks.md](./spike-auth-bookmarks.md))

- **A1 resolved**: twikit handles auth via username/password login with cookie persistence. No API key needed.
- **A2 resolved**: twikit wraps the GraphQL bookmarks endpoint with built-in pagination. No hard bookmark cap (unlike tweepy's 800 limit).

---

## Fit Check (R × A)

| Req | Requirement | Status | A |
|-----|-------------|--------|---|
| R0 | Scrape all historic Twitter/X bookmarks | Core goal | ✅ |
| R1 | Save each bookmark as a separate markdown file | Core goal | ✅ |
| R2 | Capture the full thread when a bookmark is part of a thread | Core goal | ✅ |
| R3 | Download and include all media (images, GIFs, video) | Core goal | ✅ |
| R4 | Save files to a user-designated output folder | Must-have | ✅ |
| R5 | Authenticate with Twitter/X to access private bookmarks endpoint | Must-have | ✅ |
| R6 | Handle Twitter/X rate limiting gracefully | Must-have | ✅ |
| R7 | Resumable — track progress, skip already-scraped bookmarks on re-run | Must-have | ✅ |
| R8 | Full metadata in YAML frontmatter (author, handle, date, URL, likes, retweets, reply count) | Must-have | ✅ |
| R9 | Built in Python | Must-have | ✅ |
| R10 | Sensible file naming and folder organization | Nice-to-have | ✅ |

All requirements pass. No flagged unknowns remain.

---

## Next Steps

1. **Breadboard** — Map the pipeline into concrete affordances and wiring
2. **Slice** — Break into vertical implementation slices
3. **Build**
