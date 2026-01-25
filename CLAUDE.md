# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains liturgical data for a Daily Office prayer application following the Anglican/Episcopal tradition. The project provides structured daily prayer readings, psalms, and collects organized according to the church calendar.

## Data Structure

### Daily Office CSV Format

The primary data source is `data/acn-prayers-2026.csv`, which contains the following columns:

- **Date**: Calendar date for the observance
- **Liturgical Color**: Color designation (White, Green, Purple, Pink, Red)
- **Observance**: Name of the liturgical season or feast day
- **MP Opening Sentence of Scripture**: Morning Prayer opening sentence with citation
- **Antiphon**: Seasonal antiphon response
- **MP First Lesson**: Morning Prayer Old Testament reading
- **MP Second Lesson**: Morning Prayer New Testament reading
- **Psalms (MP, 60-day)**: Morning Prayer psalm assignments
- **EP Opening Sentence of Scripture**: Evening Prayer opening sentence with citation
- **EP First Lesson**: Evening Prayer Old Testament reading
- **EP Second Lesson**: Evening Prayer New Testament reading
- **Psalms (EP, 60-day)**: Evening Prayer psalm assignments
- **Seasonal Collect**: Primary collect for the season
- **Special Collect**: Additional collects for saints' days or special observances

### Liturgical Calendar Features

The data includes:
- Complete liturgical year with proper seasons (Advent, Christmas, Epiphany, Lent, Easter, Pentecost)
- Special observances and saints' days with dedicated collects
- Color coding for liturgical seasons
- 60-day psalm cycle for both Morning and Evening Prayer
- Scripture reading plan following a systematic lectionary
- Ember Days and major feast days

### Data Format Notes

- Scripture references use abbreviated book names (Gen, Exod, Matt, etc.)
- Some readings include † markers indicating partial chapter readings
- Verse ranges indicated with notation like "1-28" or "1-20v"
- Multiple psalms separated by commas
- Empty cells for recurring seasonal collects (inherited from previous days)

## Architecture

This is a **static site generator** that converts liturgical CSV data into beautiful, printable HTML pages.

### Technology Stack
- **Python 3** with Jinja2 templating
- **Modern CSS** with Grid/Flexbox layouts
- **Print-optimized** styling using `@media print`
- No server or database required

### Deployment

The site is deployed to a Hetzner VPS and served via nginx:

- **Domain**: `ancadailyoffice.app`
- **DNS**: Managed through Squarespace (A record → `178.156.168.116`)
- **Server**: Hetzner VPS running Ubuntu with nginx
- **SSH Access**: `ssh -i ~/.ssh/hetzner_id_ed25519 root@178.156.168.116`
- **Deployment**: Automated via GitHub Actions workflow
- **SSL**: Let's Encrypt certificates via certbot

#### GitHub Actions Workflow
The site automatically deploys on push to main:
1. Build process generates static HTML from CSV data
2. Files are transferred to the server
3. nginx serves the static files from the build directory

### Directory Structure
```
daily-office/
├── data/acn-prayers-2026.csv   # Source data
├── templates/                  # Jinja2 templates
│   ├── day.html                # Individual day page
│   ├── all.html                # All-days print page
│   └── index.html              # Calendar index
├── static/style.css            # Styles (screen + print)
├── generate.py                 # Build script
└── build/                      # Generated site
    ├── index.html              # Calendar
    ├── all.html                # Print-all page
    └── YYYY-MM-DD.html         # Individual days
```

### Build Process
The `generate.py` script:
1. Parses CSV data into structured day objects
2. Renders Jinja2 templates for each day
3. Generates index and all-days pages
4. Copies static assets to build directory

## Common Commands

### Build the Site
```bash
python generate.py
```

This regenerates all HTML pages from the CSV data.

### View the Site
```bash
open build/index.html
```

### Print All Days
```bash
open build/all.html
# Then: File → Print → Print All
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Server Management

```bash
# SSH into production server
ssh -i ~/.ssh/hetzner_id_ed25519 root@178.156.168.116

# Check nginx status
sudo systemctl status nginx

# Reload nginx configuration
sudo nginx -t && sudo systemctl reload nginx

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Renew SSL certificate
sudo certbot renew
```

## Development Workflow

When modifying the site:

1. **Data changes**: Edit `data/acn-prayers-2026.csv` then run `python generate.py`
2. **Template changes**: Edit files in `templates/` then run `python generate.py`
3. **Style changes**: Edit `static/style.css` then run `python generate.py`
4. **Build script changes**: Edit `generate.py` then run it

The build directory (`build/`) is regenerated each time, so never edit files there directly.

## Print Optimization

The CSS includes special print styles that:
- Target single-page printing (8.5x11")
- Use serif fonts for better print readability
- Remove navigation and screen-only elements
- Optimize spacing to fit content on one page
- Add page breaks between days in the all-days view

## Key Features

### Calendar View (index.html)
- **Sunday-first layout**: Weeks start on Sunday, following traditional liturgical calendars
- **Calendar grid**: Organized by month with weeks displayed in rows
- **Liturgical colors**: Visual color bar at top of each day cell
- **Empty cells**: Days before/after the month are shown as empty
- **Hover effects**: Days highlight on hover for better UX
- The `organize_into_calendar_weeks()` function in `generate.py` handles the Sunday-first layout

### Individual Day Pages (day.html)
Each day page includes:
- **Morning Prayer**: Opening sentence, antiphon, psalms, two lessons
- **Evening Prayer**: Opening sentence, psalms, two lessons
- **Collects**: Seasonal collect and optional special collect
- **Navigation**: Previous/next day links, back to calendar
- **Print optimization**: Designed to fit on a single 8.5x11" page

### Print-All Page (all.html)
- Contains all 365 days in sequence
- Page breaks between each day (`page-break-after: always`)
- Allows printing entire year in one operation
- Optimized for creating a physical prayer book

## Design System

### Color Palette
```css
--color-text: #2c3e50          /* Main text */
--color-text-light: #7f8c8d    /* Secondary text */
--color-border: #e0e0e0         /* Borders and dividers */
--color-background: #ffffff     /* Page background */
--color-accent: #3498db         /* Links and highlights */
```

### Typography
- **Screen**: System font stack (San Francisco, Segoe UI, Roboto)
- **Print**: Serif fonts (Georgia, Times New Roman) for better readability
- **Font sizes**: 10-11pt for print, 16px base for screen

### Liturgical Colors
```python
COLOR_MAP = {
    'White': '#FFFFFF',
    'Green': '#228B22',
    'Purple': '#663399',
    'Pink': '#FFC0CB',
    'Red': '#DC143C'
}
```

### Responsive Design
- Desktop: Full calendar grid (7 columns)
- Mobile: Smaller day cells, condensed text
- Breakpoint: 768px

## Template Structure

### Templates Use Jinja2
All templates support:
- `{{ variable }}` - Variable interpolation
- `{% if condition %}` - Conditionals
- `{% for item in list %}` - Loops
- `{{ dict['key'] }}` - Dictionary access

### Common Template Variables
- `day` - Individual day object with all CSV fields
- `days` - List of all days
- `months` - Dictionary of months with organized weeks
- `color_map` - Liturgical color hex values
- `prev_day` / `next_day` - Adjacent days for navigation

## Attribution

All pages include footer attribution to:
> "Lectionary and collects from [The Book of Common Prayer (2019)](https://bcp2019.anglicanchurch.net/index.php), Anglican Church in North America"

This attribution is required and should not be removed.

## Assets

### Favicon
- Location: `static/favicon.svg`
- Design: 📖 open book emoji in SVG format
- Linked in all HTML templates with: `<link rel="icon" href="static/favicon.svg" type="image/svg+xml">`

## Common Modifications

### Adding a New Page
1. Create template in `templates/`
2. Add generation function in `generate.py`
3. Call function in `main()`
4. Run `python generate.py`

### Changing Colors/Fonts
Edit `static/style.css`:
- `:root` variables for global colors
- `body` for base typography
- `@media print` for print-specific styles

### Modifying Calendar Layout
The calendar is organized in `generate_index_page()`:
- `organize_into_calendar_weeks()` creates Sunday-first weeks
- Template uses nested loops: `{% for week in weeks %}` → `{% for day in week %}`
- CSS grid handles 7-column layout

### Updating Page Structure
Day pages follow this hierarchy:
1. `<header>` - Date, observance, liturgical color
2. `<section class="office-section morning-prayer">` - Morning Prayer content
3. `<section class="office-section evening-prayer">` - Evening Prayer content
4. `<section class="collects">` - Prayer collects
5. `<footer>` - Attribution and metadata

## Data Handling

When working with this data:
- Maintain CSV column order and structure
- Preserve liturgical color coding conventions
- Keep scripture reference format consistent
- Respect the 60-day psalm cycle pattern
- Maintain proper attribution in collect texts
- Handle empty cells gracefully (displayed as None or hidden in templates)
- Date parsing supports both abbreviated (Jan, Feb) and full (January, February) month names
