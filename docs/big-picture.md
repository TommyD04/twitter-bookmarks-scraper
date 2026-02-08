# Twitter Bookmarks Scraper — Big Picture

**Selected shape:** A (twikit + Python CLI)

---

## Frame

### Problem
- Twitter bookmarks accumulate over time but there's no built-in way to export or archive them
- Bookmarked tweets may disappear if accounts are deleted or tweets removed
- Thread context is lost when viewing individual bookmarks
- No offline access to bookmarked content

### Outcome
- All historic bookmarks are saved locally as individual markdown files
- Each bookmark preserves the full thread context (where applicable)
- All media (images, GIFs, video) is captured locally
- Content is organized in a designated folder, ready for offline reading or search
- Process is resumable — can stop and restart without re-downloading

---

## Shape

### Fit Check (R × A)

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

### Parts

| Part | Mechanism | Flag |
|------|-----------|:----:|
| **A1** | **Auth** — `twikit.Client.login()` with username/email/password, cookie persistence via `cookies.json` | |
| **A2** | **Bookmark Fetcher** — `client.get_bookmarks()` + `.next()` pagination, 2s delay, exponential backoff on 429 | |
| **A3** | **Thread Resolver** — walk parent chain via `get_tweet_by_id()`, in-memory cache | |
| **A4** | **Media Downloader** — download images/GIFs/MP4 to `media/`, skip existing | |
| **A5** | **Markdown Renderer** — YAML frontmatter + thread body + media refs | |
| **A6** | **Progress Tracker** — `manifest.json` with scraped IDs + cursor for resumability | |
| **A7** | **CLI Runner** — `python scrape.py --output ./bookmarks`, orchestrates pipeline | |

---

## Slices

|  |  |  |
|:--|:--|:--|
| **V1: LOGIN + FETCH + PRINT**<br>⏳ PENDING<br><br>• CLI arg parsing (`--output`, creds)<br>• twikit login + cookie persistence<br>• Fetch first page of bookmarks<br>• Print tweet ID + text to console<br><br>*Demo: Run script, see bookmarks printed* | **V2: FULL PAGINATION + BASIC MARKDOWN**<br>⏳ PENDING<br><br>• Full `.next()` pagination loop<br>• 2s delay + exponential backoff on 429<br>• Basic MarkdownRenderer (frontmatter + body)<br>• Summary message on completion<br><br>*Demo: `.md` files appear with frontmatter + text* | **V3: THREAD RESOLUTION**<br>⏳ PENDING<br><br>• ThreadResolver walks parent chain<br>• `get_tweet_by_id()` with in-memory cache<br>• MarkdownRenderer adds thread sections<br>• `## Tweet N of M` structure<br><br>*Demo: Open reply bookmark, see full thread* |
| **V4: MEDIA DOWNLOAD**<br>⏳ PENDING<br><br>• Download images/GIFs/MP4 to `media/`<br>• Name: `{tweet_id}_{index}.{ext}`<br>• Skip existing files<br>• `![](media/...)` in markdown<br><br>*Demo: Images render inline in markdown* | **V5: RESUMABILITY**<br>⏳ PENDING<br><br>• `manifest.json` tracks scraped IDs + cursor<br>• BookmarkFetcher resumes from saved cursor<br>• Skip already-scraped bookmarks<br>• &nbsp;<br><br>*Demo: Second run completes instantly* | |
