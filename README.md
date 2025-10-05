# alexsite.py — minimal static site builder for OpenBSD httpd

This is a personal script that helps me manage the content on my public websites:

- `alexanderlemna.com`
- `notes.alexanderlemna.com`

All of these websites serve up some basic, static HTML/CSS pages with no JavaScript required. I write all the pages up as Markdown documents, and run this script to convert them to HTML and copy them to my web server's document root. 

# BACKGROUND

I have the following problem: I want to run my website on OpenBSD because it has the web server and documentation I'm most comfortable with. However, I write my code and some of my content in VSCode, and unfortunately VSCode doesn't work on on OpenBSD (even using the Remote - SSH extension).

Obviously, the long term solution is to get used to working with tools that are actually available on OpenBSD! That's a future goal, though. Right now, I've got to figure out how to accomplish my goals (OpenBSD deployment + comfortable dev tools) using only the skills I already have.

My current solution, though it sounds and feels a bit messy, is to actually have three servers:

1. WEBSITE-DEV-LINUX, a minimal Ubuntu server. This server is a modest 2-core virtual machine with 4GB of memory. I'm running the minimal installation of Ubuntu Server 24.04. I connect to this server using the Remote - SSH extension. I use `Caddy` here. TODO: EXPAND.

2. WEBSITE-DEV-OBSD, an OpenBSD server. Like the Linux server, it also has 2 cores and 4GB of RAM. I pull my changes from GitHub down to this box and run `httpd` and actually get to see what my website is going to look like. Once I'm happy, I can 

3. WEBSITE-PROD, an OpenBSD server.




My web servers are OpenBSD's `httpd` (and Linux's `Caddy`, for dev purposes), with an expected directory structure of (roughly):

```
/src/
|-- alexanderlemna.com/
|   |-- __index__.md
|   `-- __settings__.toml
|
`-- notes.alexanderlemna.com/
    |-- __index__.md
    |-- __settings__.toml
    `-- nb/
        |-- note1.md
        |-- note2.md
        |-- note3.md
        `-- note4.md


/srv/
|-- acme/
|-- logs/
`-- sites/
    |-- alexanderlemna.com/
    |   |-- footer.html
    |   |-- header.html
    |   |-- index.html
    |   `-- style.css
    `-- notes.alexanderlemna.com/
        |-- footer.html
        |-- header.html
        |-- index.html
        |-- style.css
        `-- nb/
            |-- note1.html
            |-- note2.html
            |-- note3.html
            `-- note4.html
```

Configuration precedence:
1) CLI flags
2) Per-domain settings file: `src_root/<domain>/__settings__.toml`
3) Global config file: `/etc/alexsite.toml`

Notes:
- Markdown converter is intentionally minimal: headings (#, ##, ###),
  paragraphs, fenced code blocks ``` and indented code, inline `code`,
  emphasis `*em*` and `**strong**`, links [text](url), and lists (- or 1.).
- All unknown markdown is escaped as plain text.
