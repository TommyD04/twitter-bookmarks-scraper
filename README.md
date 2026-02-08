# Twitter Bookmarks Scraper

A Python CLI tool that exports your Twitter/X bookmarks as local markdown files, preserving threads, media, and metadata.

## Features

- Saves each bookmark as an individual markdown file with YAML frontmatter
- Resolves full thread context for reply bookmarks
- Downloads all media (images, GIFs, video) locally
- Resumable — tracks progress and skips already-scraped bookmarks
- Handles rate limiting with exponential backoff

## Requirements

- Python 3.12+
- A Twitter/X account with bookmarks

## Setup

```bash
pip install -r requirements.txt
```

## Authentication

Direct login via username/password is often blocked by Cloudflare bot protection. The recommended approach is to import cookies from your browser.

### Browser Cookie Import (Recommended)

1. Install the [Cookie Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) extension for Chrome (also available for Firefox and Edge)
2. Log into [x.com](https://x.com) in your browser
3. While on x.com, click the Cookie Editor extension icon
4. Click **Export** (bottom of the popup) — this copies all cookies as JSON to your clipboard
5. Open a text editor, paste the contents, and save as a file (e.g., `twitter_cookies.json`)
6. Run the scraper with the `--cookies` flag:

```bash
python scrape.py --output .\bookmarks --cookies twitter_cookies.json
```

The first run imports the browser cookies and saves them as `cookies.json` in your output directory. All subsequent runs reuse that session automatically — no `--cookies` flag needed:

```bash
python scrape.py --output .\bookmarks
```

### Username/Password Login

If direct login works for your account, you can provide credentials via CLI flags or interactive prompts:

```bash
python scrape.py --output .\bookmarks --username myuser --email me@mail.com --password mypass
```

Or omit the credential flags to be prompted interactively.

## Usage

```bash
python scrape.py --output .\bookmarks
```

### CLI Options

| Flag | Description |
|------|-------------|
| `--output` | **(Required)** Destination folder for markdown files and media |
| `--cookies` | Path to a browser-exported cookie file (JSON or Netscape cookies.txt) |
| `--username` | Twitter username (prompted if not provided) |
| `--email` | Twitter email (prompted if not provided) |
| `--password` | Twitter password (prompted if not provided) |

## Output Structure

```
bookmarks/
  cookies.json           # Saved session (auto-generated)
  manifest.json          # Progress tracker for resumability
  {handle}_{tweet_id}.md # One markdown file per bookmark
  media/
    {tweet_id}_0.jpg     # Downloaded media files
    {tweet_id}_1.mp4
```

## Running Tests

```bash
python -m pytest tests/ -v
```
