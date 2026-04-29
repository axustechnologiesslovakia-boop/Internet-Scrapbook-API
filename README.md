# Internet-Scrapbook-API
A FastAPI powered web archive with a built-in moderation engine, administrative controls, and a searchable frontend.
# internet-scrapbook

A simple FastAPI web app for archiving and searching site reviews. Includes a basic moderation system and an admin dashboard.

## Features
- Searchable review archive
- Regex-based word filtering via `blocked.txt`
- Admin portal for toggling filters and deleting posts

## Setup
1. `pip install -r requirements.txt`
2. Add banned words to `blocked.txt` (one per line)
3. Run: `uvicorn main:app --reload`

## Admin Access
Access the dashboard at `/admin-portal?pw=YOUR_PASSWORD`

## Project Info
Created for Hack Club. Uses a local JSON store for data.
