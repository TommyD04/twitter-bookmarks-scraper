# Twitter Bookmarks Scraper — Slices

## Slice Definitions

### V1: Login + Fetch + Print

**Goal:** Prove the twikit auth and bookmarks pipeline works end-to-end.

| ID | Affordance | Notes |
|----|-----------|-------|
| U1 | `--output` arg | Folder path (created if missing) |
| U2 | Credential args/prompts | Username, email, password |
| U3 | Login status message | "Logging in..." / "Using saved session" |
| U4 | Progress counter | "Fetched 20 bookmarks..." |
| N1 | Orchestrator (minimal) | CLI parsing, calls auth then fetch |
| N2 | AuthManager | twikit login + cookies.json persistence |
| N3 | BookmarkFetcher (1 page only) | Fetch first page, print tweet IDs + text preview |

**Demo:** Run the script, see it log in, fetch first page of bookmarks, print tweet text to console.

---

### V2: Full Pagination + Basic Markdown

**Goal:** Fetch ALL bookmarks (not just first page) and write basic markdown files.

| ID | Affordance | Notes |
|----|-----------|-------|
| N3 | BookmarkFetcher (full pagination) | Loop `.next()`, 2s delay, backoff on 429 |
| U5 | Rate limit warning | "Rate limited, waiting 30s..." |
| N6 | MarkdownRenderer (basic) | Frontmatter + single tweet body, no threads, no media |
| U8 | Write progress | "Writing 50/200 markdown files..." |
| U9 | Summary message | "Done. 200 bookmarks saved." |

**Demo:** Run the script, watch it paginate through all bookmarks, see `.md` files appear in the output folder with frontmatter and tweet text.

---

### V3: Thread Resolution

**Goal:** Bookmarks that are part of threads now include the full thread in the markdown.

| ID | Affordance | Notes |
|----|-----------|-------|
| N4 | ThreadResolver | Walk parent chain via `get_tweet_by_id()`, cache in memory |
| U6 | Thread progress | "Resolving thread 12/85..." |
| N6 | MarkdownRenderer (threads) | Multi-tweet body with `## Tweet N of M` sections |

**Demo:** Open a markdown file for a bookmarked reply — see the full thread above it, properly ordered.

---

### V4: Media Download

**Goal:** Images, GIFs, and videos are downloaded locally and referenced in markdown.

| ID | Affordance | Notes |
|----|-----------|-------|
| N5 | MediaDownloader | Download to `media/{tweet_id}_{index}.{ext}`, skip existing |
| U7 | Download progress | "Downloading media 24/130..." |
| N6 | MarkdownRenderer (media) | `![](media/...)` references for images, links for video |

**Demo:** Open a markdown file — images render inline, video files are saved locally.

---

### V5: Resumability

**Goal:** Re-running the script skips already-scraped bookmarks and resumes pagination.

| ID | Affordance | Notes |
|----|-----------|-------|
| N7 | ProgressTracker | `manifest.json` with scraped IDs + last cursor |
| N3 | BookmarkFetcher (resume) | Load cursor from manifest, skip known IDs |
| N6 | MarkdownRenderer | Skip writing if file exists |

**Demo:** Run twice — second run completes almost instantly, printing "Skipping N already-scraped bookmarks."

---

## Sliced Breadboard

```mermaid
flowchart TB
    subgraph slice1["V1: LOGIN + FETCH + PRINT"]
        subgraph cli1["CLI Entry"]
            U1["U1: --output arg"]
            U2["U2: credentials"]
        end
        subgraph auth1["Auth"]
            N2["N2: AuthManager"]
            U3["U3: login status"]
        end
        subgraph fetch1["Fetch"]
            N3_v1["N3: BookmarkFetcher\n(1 page)"]
            U4["U4: progress counter"]
        end
        N1_v1["N1: Orchestrator\n(minimal)"]
    end

    subgraph slice2["V2: FULL PAGINATION + BASIC MARKDOWN"]
        N3_v2["N3: BookmarkFetcher\n(full pagination + backoff)"]
        U5["U5: rate limit warning"]
        subgraph render2["Render"]
            N6_v2["N6: MarkdownRenderer\n(basic: frontmatter + body)"]
            U8["U8: write progress"]
        end
        U9["U9: summary msg"]
    end

    subgraph slice3["V3: THREAD RESOLUTION"]
        subgraph resolve3["Resolve"]
            N4["N4: ThreadResolver"]
            U6["U6: thread progress"]
        end
        N6_v3["N6: MarkdownRenderer\n(+ thread sections)"]
    end

    subgraph slice4["V4: MEDIA DOWNLOAD"]
        subgraph download4["Download"]
            N5["N5: MediaDownloader"]
            U7["U7: download progress"]
        end
        N6_v4["N6: MarkdownRenderer\n(+ media refs)"]
    end

    subgraph slice5["V5: RESUMABILITY"]
        N7["N7: ProgressTracker\n(manifest.json)"]
        N3_v5["N3: BookmarkFetcher\n(+ resume from cursor)"]
    end

    %% Force slice ordering
    slice1 ~~~ slice2
    slice2 ~~~ slice3
    slice3 ~~~ slice4
    slice4 ~~~ slice5

    %% Cross-slice wiring
    U1 --> N1_v1
    U2 --> N1_v1
    N1_v1 --> N2
    N2 -.-> U3
    N1_v1 --> N3_v1

    N3_v2 -.-> U5
    N3_v2 --> N6_v2
    N6_v2 -.-> U8

    N3_v2 --> N4
    N4 -.-> U6
    N4 --> N6_v3

    N5 -.-> U7
    N5 --> N6_v4

    N3_v5 --> N7
    N7 -.-> N3_v5

    %% Slice boundary styling
    style slice1 fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style slice2 fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    style slice3 fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    style slice4 fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    style slice5 fill:#fff8e1,stroke:#ffc107,stroke-width:2px

    %% Nested subgraphs transparent
    style cli1 fill:transparent,stroke:#888,stroke-width:1px
    style auth1 fill:transparent,stroke:#888,stroke-width:1px
    style fetch1 fill:transparent,stroke:#888,stroke-width:1px
    style render2 fill:transparent,stroke:#888,stroke-width:1px
    style resolve3 fill:transparent,stroke:#888,stroke-width:1px
    style download4 fill:transparent,stroke:#888,stroke-width:1px

    %% Node styling
    classDef ui fill:#ffb6c1,stroke:#d87093,color:#000
    classDef nonui fill:#d3d3d3,stroke:#808080,color:#000
    class U1,U2,U3,U4,U5,U6,U7,U8,U9 ui
    class N1_v1,N2,N3_v1,N3_v2,N3_v5,N4,N5,N6_v2,N6_v3,N6_v4,N7 nonui
```

**Legend:**
- **Pink nodes (U)** = CLI inputs/outputs the user sees
- **Grey nodes (N)** = Code modules
- **Solid lines** = Calls/triggers
- **Dashed lines** = Returns/status

## Slices Grid

|  |  |  |
|:--|:--|:--|
| **V1: LOGIN + FETCH + PRINT**<br>⏳ PENDING<br><br>• CLI arg parsing (`--output`, creds)<br>• twikit login + cookie persistence<br>• Fetch first page of bookmarks<br>• Print tweet ID + text to console<br><br>*Demo: Run script, see bookmarks printed* | **V2: FULL PAGINATION + BASIC MARKDOWN**<br>⏳ PENDING<br><br>• Full `.next()` pagination loop<br>• 2s delay + exponential backoff on 429<br>• Basic MarkdownRenderer (frontmatter + body)<br>• Summary message on completion<br><br>*Demo: `.md` files appear with frontmatter + text* | **V3: THREAD RESOLUTION**<br>⏳ PENDING<br><br>• ThreadResolver walks parent chain<br>• `get_tweet_by_id()` with in-memory cache<br>• MarkdownRenderer adds thread sections<br>• `## Tweet N of M` structure<br><br>*Demo: Open reply bookmark, see full thread* |
| **V4: MEDIA DOWNLOAD**<br>⏳ PENDING<br><br>• Download images/GIFs/MP4 to `media/`<br>• Name: `{tweet_id}_{index}.{ext}`<br>• Skip existing files<br>• `![](media/...)` in markdown<br><br>*Demo: Images render inline in markdown* | **V5: RESUMABILITY**<br>⏳ PENDING<br><br>• `manifest.json` tracks scraped IDs + cursor<br>• BookmarkFetcher resumes from saved cursor<br>• Skip already-scraped bookmarks<br>• • &nbsp;<br><br>*Demo: Second run completes instantly* | |
