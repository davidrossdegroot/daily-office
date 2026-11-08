#!/usr/bin/env python3
"""
Daily Office Static Site Generator
Parses liturgical CSV data and generates beautiful, printable HTML pages.
"""

import argparse
import csv
import os
import re
import shutil
from datetime import UTC, datetime
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


def parse_csv(csv_path, year=None):
    """Parse the liturgical CSV file and return list of day dictionaries."""
    if year is None:
        match = re.search(r"(?<!\d)(\d{4})(?!\d)", Path(csv_path).name)
        if match is None:
            raise ValueError("Specify a year or use a CSV filename containing the year")
        year = int(match.group(1))
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
                    date_obj = datetime.strptime(f"{row['Date']} {year}", '%b %d %Y').replace(tzinfo=UTC)
                except ValueError:
                    # Try full month format (January, February, etc.)
                    date_obj = datetime.strptime(f"{row['Date']} {year}", '%B %d %Y').replace(tzinfo=UTC)

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

            # Substitute only the saint-name placeholder; leave other blanks untouched.
            if row.get('Special Collect') and row.get('Remembrance'):
                saint_name = row['Remembrance'].split(',')[0].strip()
                special_collect = row['Special Collect']
                special_collect = re.sub(r'\bN\.', saint_name, special_collect)
                row['Special Collect'] = special_collect

            days.append(row)

    return sorted(days, key=lambda x: x['date_obj'])


def setup_jinja_env(root_path='', year_links=()):
    """Set up Jinja2 templating environment.

    root_path is the relative path from the rendered pages to the site root.
    year_links drives the calendar's year switcher, which is hidden when empty.
    """
    template_dir = Path(__file__).parent / 'templates'
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        trim_blocks=True,
        lstrip_blocks=True
    )
    env.globals.update(root_path=root_path, year_links=year_links)
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
        year=days[0]['date_obj'].year,
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
        year=days[0]['date_obj'].year,
        color_map=COLOR_MAP,
        ga_measurement_id=GA_MEASUREMENT_ID
    )

    output_path = output_dir / 'all.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def generate_monthly_pages(env, days, output_dir):
    """Generate per-month print pages."""
    template = env.get_template('all-month.html')

    # Group days by month
    months = {}
    for day in days:
        month_name = day['date_obj'].strftime('%B')
        if month_name not in months:
            months[month_name] = {
                'name': month_name,
                'year': day['date_obj'].year,
                'days': []
            }
        months[month_name]['days'].append(day)

    for month_name, month_data in months.items():
        html = template.render(
            days=month_data['days'],
            month_name=month_name,
            year=month_data['year'],
            color_map=COLOR_MAP,
            ga_measurement_id=GA_MEASUREMENT_ID
        )
        filename = f"all-{month_name.lower()}.html"
        output_path = output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)


def generate_about_page(env, output_dir, year):
    """Generate the about page."""
    template = env.get_template('about.html')
    html = template.render(year=year, ga_measurement_id=GA_MEASUREMENT_ID)

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


def generate_day_redirect(env, day, output_dir):
    """Keep a day's root URL working when its year is not the one at the site root."""
    template = env.get_template('redirect.html')
    html = template.render(target=f"{day['date_obj'].year}/{day['date_slug']}.html")

    output_path = output_dir / f"{day['date_slug']}.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def select_default_year(years, current_year):
    """Return the year for the site root: the current year, else the nearest earlier one."""
    return max((year for year in years if year <= current_year), default=min(years))


def build_year_links(years, selected_year, root_path=''):
    """Describe the year switcher for a page showing selected_year."""
    return [
        {
            'year': year,
            'href': f'{root_path}{year}/index.html',
            'current': year == selected_year,
        }
        for year in sorted(years)
    ]


def build_year_pages(days, output_dir, root_path='', year_links=()):
    """Render every page for one year into output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    env = setup_jinja_env(root_path=root_path, year_links=year_links)

    for i, day in enumerate(days):
        prev_day = days[i - 1] if i > 0 else None
        next_day = days[i + 1] if i < len(days) - 1 else None
        generate_day_page(env, day, prev_day, next_day, output_dir)

    generate_index_page(env, days, output_dir)
    generate_all_page(env, days, output_dir)
    generate_monthly_pages(env, days, output_dir)
    generate_about_page(env, output_dir, days[0]['date_obj'].year)


def build_site(days_by_year, output_dir, current_year):
    """Build the site for one or more years.

    A single year is built flat at the root with no year switcher. With several
    years, each gets its own YEAR/ directory and the root repeats the default
    year. Other years' day URLs at the root redirect into their directories, so
    links stay valid when the default year changes.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    years = sorted(days_by_year)

    if len(years) == 1:
        build_year_pages(days_by_year[years[0]], output_dir)
    else:
        default_year = select_default_year(years, current_year)
        build_year_pages(
            days_by_year[default_year],
            output_dir,
            year_links=build_year_links(years, default_year),
        )
        redirect_env = setup_jinja_env()
        for year in years:
            build_year_pages(
                days_by_year[year],
                output_dir / str(year),
                root_path='../',
                year_links=build_year_links(years, year, root_path='../'),
            )
            if year != default_year:
                for day in days_by_year[year]:
                    generate_day_redirect(redirect_env, day, output_dir)

    copy_static_files(output_dir)


def main():
    """Main build function."""
    print("Daily Office Static Site Generator")
    print("=" * 50)

    # Paths
    base_dir = Path(__file__).parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--year', type=int, help='Calendar year to generate')
    parser.add_argument('--csv', type=Path, help='Input CSV (defaults to data/acna-prayers-YEAR.csv)')
    parser.add_argument('--output-dir', type=Path, default=base_dir / 'build')
    args = parser.parse_args()
    if args.year is not None and not 1 <= args.year <= 9999:
        parser.error('--year must be between 1 and 9999')
    if args.csv is not None:
        csv_paths = [args.csv]
    elif args.year is not None:
        csv_paths = [base_dir / 'data' / f'acna-prayers-{args.year}.csv']
    else:
        csv_paths = sorted((base_dir / 'data').glob('acna-prayers-[0-9][0-9][0-9][0-9].csv'))
        if not csv_paths:
            parser.error('No yearly CSV found; provide --year or --csv')
    output_dir = args.output_dir

    # Parse CSV data
    days_by_year = {}
    for csv_path in csv_paths:
        print(f"Parsing {csv_path}...")
        days = parse_csv(csv_path, year=args.year)
        if not days:
            parser.error(f'{csv_path} contains no valid dates')
        days_by_year[days[0]['date_obj'].year] = days
        print(f"Found {len(days)} days of liturgical data")

    # Render the site
    print("Generating pages...")
    build_site(days_by_year, output_dir, datetime.now(UTC).year)

    print("=" * 50)
    for year, days in sorted(days_by_year.items()):
        print(f"✓ Generated {year}: {len(days)} day pages")
    print(f"\nOutput directory: {output_dir}")
    print("\nTo view:")
    print(f"  open {output_dir}/index.html")
    print("\nTo print all days:")
    print(f"  open {output_dir}/all.html")


if __name__ == '__main__':
    main()
