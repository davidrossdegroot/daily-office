# Daily Office

A beautiful, printable web-based Daily Office for the liturgical year, following the Anglican/Episcopal tradition.

## Features

- **Clean, modern design** - Minimalist interface optimized for readability
- **Print-optimized** - Each day designed to fit on a single 8.5x11" page
- **Complete liturgical year** - All 365 days with Morning Prayer, Evening Prayer, and Collects
- **Print all at once** - Generate the entire year as a single printable document
- **Liturgical colors** - Visual indicators for each season
- **Navigation** - Browse by calendar or jump to specific dates

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate the Site

```bash
python generate.py
```

This will:
- Parse the liturgical CSV data
- Generate individual HTML pages for each day
- Create a calendar index page
- Generate an all-in-one print page
- Copy static assets to the build directory

### 3. View the Site

```bash
open build/index.html
```

Or navigate to `build/index.html` in your web browser.

## Printing

### Print Individual Days

1. Open any day page (e.g., `build/2026-01-25.html`)
2. Use your browser's print function (File → Print)
3. Each day is optimized to fit on one printed page

### Print All Days at Once

1. Open `build/all.html` in your browser
2. File → Print → Print All (or Save as PDF)
3. This creates a complete prayer book with all 365 days

## Project Structure

```
daily-office/
├── data/
│   └── acn-prayers-2026.csv    # Liturgical data source
├── templates/
│   ├── day.html                # Individual day template
│   ├── all.html                # All-days print template
│   └── index.html              # Calendar index template
├── static/
│   └── style.css               # Styles (screen + print)
├── build/                      # Generated site (created by generate.py)
│   ├── index.html
│   ├── all.html
│   ├── 2026-01-01.html
│   └── ...
├── generate.py                 # Static site generator
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── CLAUDE.md                   # Development guide
```

## Data Format

The CSV file (`data/acn-prayers-2026.csv`) contains:
- Date and liturgical observance
- Morning Prayer: Opening sentence, antiphon, psalms, lessons
- Evening Prayer: Opening sentence, psalms, lessons
- Seasonal and special collects
- Liturgical colors (White, Green, Purple, Pink, Red)

## Development

The site is generated using:
- **Python 3** for the build script
- **Jinja2** for HTML templating
- **CSS Grid/Flexbox** for responsive layout
- **Print CSS** with `@media print` for optimal printing

To regenerate the site after making changes to templates or data:

```bash
python generate.py
```

## License

Liturgical content follows traditional Anglican/Episcopal Daily Office structure.
