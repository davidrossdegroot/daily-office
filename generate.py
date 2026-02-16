#!/usr/bin/env python3
"""
Daily Office Static Site Generator
Parses liturgical CSV data and generates beautiful, printable HTML pages.
"""

import csv
import os
import shutil
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


# Liturgical color mapping
COLOR_MAP = {
    'White': '#FFFFFF',
    'Green': '#228B22',
    'Purple': '#663399',
    'Pink': '#FFC0CB',
    'Red': '#DC143C'
}

# Google Analytics measurement ID (configurable via environment variable)
GA_MEASUREMENT_ID = os.environ.get('GA_MEASUREMENT_ID', 'G-RMEJ6VZKK0')


def parse_csv(csv_path):
    """Parse the liturgical CSV file and return list of day dictionaries."""
    days = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip rows without a valid date
            if not row.get('Date') or row['Date'].strip() == '':
                continue

            # Parse and format the date
            try:
                # Try abbreviated month format first (Jan, Feb, etc.)
                try:
                    date_obj = datetime.strptime(row['Date'], '%b %d')
                except ValueError:
                    # Try full month format (January, February, etc.)
                    date_obj = datetime.strptime(row['Date'], '%B %d')

                # Add year 2026
                date_obj = date_obj.replace(year=2026)
                row['date_obj'] = date_obj
                row['date_formatted'] = date_obj.strftime('%B %d, %Y')
                row['date_slug'] = date_obj.strftime('%Y-%m-%d')
                row['day_of_week'] = date_obj.strftime('%A')
            except ValueError:
                print(f"Warning: Could not parse date '{row['Date']}', skipping row")
                continue

            # Clean up empty fields
            for key, value in row.items():
                if isinstance(value, str) and value.strip() == '':
                    row[key] = None

            days.append(row)

    return sorted(days, key=lambda x: x['date_obj'])


def setup_jinja_env():
    """Set up Jinja2 templating environment."""
    template_dir = Path(__file__).parent / 'templates'
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        trim_blocks=True,
        lstrip_blocks=True
    )
    return env


def generate_day_page(env, day, prev_day, next_day, output_dir):
    """Generate an individual day page."""
    template = env.get_template('day.html')
    html = template.render(
        day=day,
        prev_day=prev_day,
        next_day=next_day,
        color_map=COLOR_MAP,
        ga_measurement_id=GA_MEASUREMENT_ID
    )

    output_path = output_dir / f"{day['date_slug']}.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def organize_into_calendar_weeks(days_in_month, year, month_num):
    """
    Organize days into calendar weeks (Sunday-Saturday).
    Returns a list of weeks, where each week is a list of 7 days (or None for empty cells).
    """
    from calendar import monthrange

    # Create a dict for quick lookup of days by day-of-month
    days_dict = {day['date_obj'].day: day for day in days_in_month}

    # Get the first day of the month and total days
    first_weekday, num_days = monthrange(year, month_num)

    # Adjust weekday to make Sunday = 0 (Python uses Monday = 0)
    # Python: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
    # We want: Sun=0, Mon=1, Tue=2, Wed=3, Thu=4, Fri=5, Sat=6
    first_weekday = (first_weekday + 1) % 7

    weeks = []
    current_week = [None] * first_weekday  # Empty cells before the month starts

    for day_num in range(1, num_days + 1):
        # Add the day (or None if we don't have data for it)
        current_week.append(days_dict.get(day_num))

        # If we've filled a week, start a new one
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []

    # Fill remaining days of the last week with None
    if current_week:
        current_week.extend([None] * (7 - len(current_week)))
        weeks.append(current_week)

    return weeks


def generate_index_page(env, days, output_dir):
    """Generate the index/calendar page."""
    template = env.get_template('index.html')

    # Group days by month and organize into calendar weeks
    months = {}
    for day in days:
        month_name = day['date_obj'].strftime('%B')
        month_num = day['date_obj'].month
        year = day['date_obj'].year

        if month_name not in months:
            months[month_name] = {
                'name': month_name,
                'days': [],
                'month_num': month_num,
                'year': year
            }
        months[month_name]['days'].append(day)

    # Organize each month into calendar weeks
    for month_name, month_data in months.items():
        month_data['weeks'] = organize_into_calendar_weeks(
            month_data['days'],
            month_data['year'],
            month_data['month_num']
        )

    html = template.render(
        days=days,
        months=months,
        color_map=COLOR_MAP,
        ga_measurement_id=GA_MEASUREMENT_ID
    )

    output_path = output_dir / 'index.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def generate_all_page(env, days, output_dir):
    """Generate the all-in-one print page."""
    template = env.get_template('all.html')
    html = template.render(
        days=days,
        color_map=COLOR_MAP,
        ga_measurement_id=GA_MEASUREMENT_ID
    )

    output_path = output_dir / 'all.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def generate_about_page(env, output_dir):
    """Generate the about page."""
    template = env.get_template('about.html')
    html = template.render(ga_measurement_id=GA_MEASUREMENT_ID)

    output_path = output_dir / 'about.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def copy_static_files(output_dir):
    """Copy static CSS files to build directory."""
    static_dir = Path(__file__).parent / 'static'
    build_static_dir = output_dir / 'static'

    if build_static_dir.exists():
        shutil.rmtree(build_static_dir)

    shutil.copytree(static_dir, build_static_dir)


def main():
    """Main build function."""
    print("Daily Office Static Site Generator")
    print("=" * 50)

    # Paths
    base_dir = Path(__file__).parent
    csv_path = base_dir / 'data' / 'acna-prayers-2026.csv'
    output_dir = base_dir / 'build'

    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)

    # Parse CSV data
    print(f"Parsing {csv_path}...")
    days = parse_csv(csv_path)
    print(f"Found {len(days)} days of liturgical data")

    # Set up Jinja2
    env = setup_jinja_env()

    # Generate individual day pages
    print("Generating individual day pages...")
    for i, day in enumerate(days):
        prev_day = days[i - 1] if i > 0 else None
        next_day = days[i + 1] if i < len(days) - 1 else None
        generate_day_page(env, day, prev_day, next_day, output_dir)

    # Generate index page
    print("Generating index page...")
    generate_index_page(env, days, output_dir)

    # Generate all-in-one page
    print("Generating print-all page...")
    generate_all_page(env, days, output_dir)

    # Generate about page
    print("Generating about page...")
    generate_about_page(env, output_dir)

    # Copy static files
    print("Copying static files...")
    copy_static_files(output_dir)

    print("=" * 50)
    print(f"✓ Generated {len(days)} day pages")
    print(f"✓ Generated index page")
    print(f"✓ Generated print-all page")
    print(f"✓ Generated about page")
    print(f"\nOutput directory: {output_dir}")
    print(f"\nTo view:")
    print(f"  open {output_dir}/index.html")
    print(f"\nTo print all days:")
    print(f"  open {output_dir}/all.html")


if __name__ == '__main__':
    main()
