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

## Data Handling

When working with this data:
- Maintain CSV column order and structure
- Preserve liturgical color coding conventions
- Keep scripture reference format consistent
- Respect the 60-day psalm cycle pattern
- Maintain proper attribution in collect texts
- Handle empty cells gracefully (displayed as "—" or hidden)
