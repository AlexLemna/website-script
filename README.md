# alexsite.py — minimal static site builder for OpenBSD httpd

This is a personal script that helps me manage the content on my public websites:

- `alexanderlemna.com`
- `notes.alexanderlemna.com`

All of these websites serve up some basic, static HTML/CSS pages with no JavaScript required. I write all the pages up as Markdown documents, and run this script to convert them to HTML and copy them to my web server's document root. My web server is OpenBSD's `httpd`, with an expected directory structure of:

```
/var/www
|-- acme/
|-- bin/
|-- cache/
|-- cgi-bin/
|-- conf/
|   |-- alexanderlemna.com.css
|   |-- alexanderlemna.com.foot
|   |-- alexanderlemna.com.head
|   |-- notes.alexanderlemna.com.css
|   |-- notes.alexanderlemna.com.foot
|   `-- notes.alexanderlemna.com.head
|-- htdocs/
|   |-- alexanderlemna.com
|   |   `-- index.html
|   `-- notes.alexanderlemna.com
|       |-- index.html
|       `-- nb/
|           `-- OpenBSD-dhcpd.html
`-- src/
    |-- alexanderlemna.com/
    |   |-- __index__.md
    |   `-- __settings__.toml
    `-- notes.alexanderlemna.com/
        |-- __index__.md
        |-- __settings__.toml
        `-- nb/
            `-- OpenBSD-dhcpd.md
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
