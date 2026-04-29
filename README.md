I created the Internet ScrapBook and its API. It's a site where you create "Pins", they're comments about website let's say i wanted to make a comment about Youtube.com so I'd make a Pin with the name of the website and the URL and make a comment saying "Great videos but too much ads!" and it will add the Pin there.

 **What I used:**

FastAPI - Simply because it handles multiple requests at once really well

JSON Storage - I mean i don't really want JSON because it practically breaks every 3 seconds but i don't have the financial situation for a Database

Regex Moderation - I don't need swearing so i added a .txt file to filter most swear words (my english dictionary got obliterated i won't sleep for 3 days)

Fly.io (with Docker) - A free hosting what do i say

 **Summary**

Security & Auth - Admin panel (password protected)

Interactive Docs - You can test the API in the docs with examples

Public Accessibility - As i said we have a URL using Fly.io i can't say it's stable though

Endpoint Variety - 4 different GET endpoints and 1 POST endpoint

**How to use**

 *Retrieving Data*
 
1. GET / - Home page to confirm the server works

2. GET /scrapbook - Pins Archive and Search Bar

3. GET /test - UI page so users can test adding Pins

 *Posting new Pins*

POST /pins - Primary way of sending Data
 Format: { "site_name": "string", "url": "string", "comment": "string" }

 *Admin Tools*

1. GET /admin-portal - This is a private dashboard

2. GET /delete {pid} - To remove specific posts

 **Censorship Filter**

 As i said i want for ScrapBook to be friendly and safe for users, so i built an automated filter that checks for swear words and slurs before a comment gets into the Archive the word will then be swapped to [CENSORED], this keeps ScrapBook Clean and stiall Anonymous

 **How to run the code**

 *Local Enviroment*

 1. First install neccessary Libraries: 
pip install fastapi uvicorn pydantic

 2. Then launch the server
python main.py

 **Deployment Notes**
I used a Dockerfile to ship this web, if you are hosting this yourself you must remember to set the ADMIN_PASSWORD in your enviroment secrets otherwise you won't have access to the Admin Panel

**!SORRY FOR BAD ENGLISH, THIS IS MY 4TH LANGUAGE!"
