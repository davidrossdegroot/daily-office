"""Exercise draft generation and publication through the command-line interfaces."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests' / 'fixtures' / 'february-2027-pr51.csv'


class PrayerPipelineTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.work = Path(self.directory.name)
        with FIXTURE.open(newline='') as stream:
            self.february = list(csv.DictReader(stream))

    def save_rows(self, target, rows):
        with target.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def regenerate(self, rows, year=2027):
        source = self.work / f'source-{year}.csv'
        target = self.work / f'draft-{year}.csv'
        with source.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        result = subprocess.run(
            [sys.executable, str(ROOT / 'bin' / 'map_common_prayers.py'),
             '--in', str(source), '--out', str(target), '--flatten-whitespace',
             '--mp-opening-mode', 'overwrite', '--ep-opening-mode', 'overwrite',
             '--antiphon-mode', 'overwrite', '--seasonal-blessing-mode', 'overwrite',
             '--special-collect-mode', 'overwrite'],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with target.open(newline='') as stream:
            return list(csv.DictReader(stream)), target

    def test_shrove_tuesday_keeps_epiphany_antiphon_when_heading_omits_season(self):
        source = next(row for row in self.february if row['Date'] == 'Feb 9')
        rows, _ = self.regenerate([source])
        self.assertEqual(
            rows[0]['Antiphon'],
            'The Lord has shown forth his glory: * O come, let us adore him.',
        )

    def test_matthias_keeps_proper_collect_and_color_with_lenten_prayer(self):
        source = next(row for row in self.february if row['Date'] == 'Feb 24')
        rows, _ = self.regenerate([source])
        self.assertEqual(rows[0]['Liturgical Color'], 'Red')
        self.assertEqual(rows[0]['Seasonal Collect'], source['Seasonal Collect'])
        self.assertTrue(
            rows[0]['Seasonal Blessing'].startswith('Look with compassion, O Lord,'),
            'A named feast during Lent must retain the seasonal Prayer over the People',
        )

    def test_draft_reports_unfilled_collects_and_publication_blocks_them(self):
        rows, target = self.regenerate(self.february)
        rows[20]['Special Collect'] = 'Grant peace to the people of _________. Amen.'
        self.save_rows(target, rows)
        output = self.work / 'preview'
        command = [sys.executable, str(ROOT / 'generate.py'), '--year', '2027',
                   '--csv', str(target), '--month', '2', '--output-dir', str(output)]
        draft = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(draft.returncode, 0, draft.stderr)
        report_path = output.with_suffix('.review.json')
        self.assertTrue(report_path.exists(), 'Drafts must emit an actionable review report')
        report = json.loads(report_path.read_text())
        blanks = [finding for finding in report['findings'] if finding['code'] == 'unfilled_blank']
        self.assertEqual({finding['date'] for finding in blanks},
                         {'2027-02-21'})
        published = self.work / 'published'
        result = subprocess.run(command[:-1] + [str(published), '--publish'],
                                cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(published.exists(), 'Rejected publication must not write site output')

    def test_plural_commemoration_is_flagged_even_after_place_blanks_are_filled(self):
        rows, target = self.regenerate(self.february)
        for row in rows:
            if row['Date'] == 'Feb 14':
                row['Special Collect'] = row['Special Collect'].replace(
                    'your servants Cyril and Methodius', 'your servant Cyril and Methodius')
        with target.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        output = self.work / 'plural-preview'
        result = subprocess.run(
            [sys.executable, str(ROOT / 'generate.py'), '--csv', str(target),
             '--month', '2', '--output-dir', str(output)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        findings = json.loads(output.with_suffix('.review.json').read_text())['findings']
        self.assertTrue(any(item['date'] == '2027-02-14' and item['code'] == 'plural_collect'
                            for item in findings))

    def test_unknown_commemoration_reports_review_instead_of_silently_approving_generic_collect(self):
        source = dict(self.february[0], Remembrance='An Unclassified Commemoration')
        _, target = self.regenerate([source])
        report_path = target.with_suffix('.review.json')
        self.assertTrue(report_path.exists(), 'CSV generation must also emit review findings')
        findings = json.loads(report_path.read_text())['findings']
        self.assertTrue(any(item['code'] == 'unknown_commemoration' and
                            item['field'] == 'Special Collect' for item in findings))

    def test_publication_reports_missing_readings_duplicate_missing_and_invalid_dates(self):
        rows = [dict(row) for row in self.february if row['Date'] != 'Feb 12']
        rows.append(dict(rows[0]))
        rows.append(dict(rows[0], Date='Feb 30'))
        rows[1]['EP Second Lesson'] = ''
        target = self.work / 'invalid-2027.csv'
        with target.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        output = self.work / 'invalid-site'
        result = subprocess.run(
            [sys.executable, str(ROOT / 'generate.py'), '--csv', str(target), '--month', '2',
             '--publish', '--output-dir', str(output)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        findings = json.loads(output.with_suffix('.review.json').read_text())['findings']
        codes = {item['code'] for item in findings}
        self.assertTrue({'missing_field', 'duplicate_date', 'missing_date', 'invalid_date'} <= codes, codes)
        self.assertFalse(output.exists())

    def test_unresolved_tokens_are_blocked_even_when_required_fields_are_populated(self):
        rows, target = self.regenerate(self.february)
        rows[0]['MP Opening Sentence of Scripture'] = 'EPIPHANY_PLACEHOLDER'
        rows[0]['Special Collect'] = 'Grant your servant N. peace. Amen.'
        rows[0]['Remembrance'] = ''
        with target.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        output = self.work / 'token-site'
        result = subprocess.run(
            [sys.executable, str(ROOT / 'generate.py'), '--csv', str(target), '--month', '2',
             '--publish', '--output-dir', str(output)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        findings = json.loads(output.with_suffix('.review.json').read_text())['findings']
        codes = {item['code'] for item in findings if item['date'] == '2027-02-01'}
        self.assertTrue({'unresolved_placeholder', 'unresolved_name'} <= codes, codes)

    def test_ignored_source_failure_survives_csv_and_blocks_publication(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from threading import Thread

        class UnavailableCalendar(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_error(503)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), UnavailableCalendar)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        _, target = self.regenerate([self.february[0]])
        failed = self.work / 'failed-2027.csv'
        result = subprocess.run(
            [sys.executable, str(ROOT / 'bin' / 'map_common_prayers.py'), '--in', str(target),
             '--out', str(failed), '--acna-year', '2027', '--ignore-fetch-errors',
             '--acna-base-url', f'http://127.0.0.1:{server.server_port}'],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        findings = json.loads(failed.with_suffix('.review.json').read_text())['findings']
        self.assertTrue(any(item['code'] == 'source_error' for item in findings))
        output = self.work / 'failed-site'
        result = subprocess.run(
            [sys.executable, str(ROOT / 'generate.py'), '--csv', str(failed), '--month', '2',
             '--publish', '--output-dir', str(output)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        findings = json.loads(output.with_suffix('.review.json').read_text())['findings']
        self.assertTrue(any(item['code'] == 'source_error' for item in findings))

    def test_publish_resolves_name_tokens_and_replaces_stale_preview_output(self):
        source = []
        for original in self.february:
            row = dict(original)
            if row['Date'] != 'Feb 23':
                row['Remembrance'] = ''
                row['Special Collect'] = ''
            source.append(row)
        _, target = self.regenerate(source)
        output = self.work / 'approved-site'
        output.mkdir()
        (output / 'stale-unreviewed.html').write_text('UNREVIEWED_PLACEHOLDER')
        result = subprocess.run(
            [sys.executable, str(ROOT / 'generate.py'), '--csv', str(target), '--month', '2',
             '--publish', '--output-dir', str(output)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((output / 'stale-unreviewed.html').exists())
        self.assertEqual(len(list(output.glob('2027-02-*.html'))), 28)
        html = (output / '2027-02-23.html').read_text()
        self.assertIn('your servant Polycarp', html)
        self.assertNotIn('N.', html)
        report = json.loads(output.with_suffix('.review.json').read_text())
        self.assertTrue(report['publishable'])

    def test_final_rendered_text_is_checked_before_replacing_published_output(self):
        source = [dict(row, **{'Remembrance': '', 'Special Collect': ''}) for row in self.february]
        source[0]['Seasonal Collect'] = 'A prayer containing the unresolved name N&#46; Amen.'
        _, target = self.regenerate(source)
        output = self.work / 'existing-site'
        output.mkdir()
        (output / 'index.html').write_text('previous reviewed site')
        result = subprocess.run(
            [sys.executable, str(ROOT / 'generate.py'), '--csv', str(target), '--month', '2',
             '--publish', '--output-dir', str(output)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((output / 'index.html').read_text(), 'previous reviewed site')
        findings = json.loads(output.with_suffix('.review.json').read_text())['findings']
        self.assertTrue(any(item['code'] == 'rendered_placeholder' for item in findings))

    def test_multiple_commemorations_require_review_instead_of_one_combined_saint_name(self):
        source = [dict(row) for row in self.february]
        source[16]['Remembrance'] += ' / An Additional Bishop'
        _, target = self.regenerate(source)
        findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
        self.assertTrue(any(item['date'] == '2027-02-17' and
                            item['code'] == 'ambiguous_commemorations' for item in findings))

    def test_nativity_of_john_does_not_turn_an_ordinary_summer_day_into_christmas(self):
        rows, _ = self.regenerate([{
            'Date': 'Jun 24', 'Observance': 'The Nativity of Saint John the Baptist',
            'Remembrance': '',
        }], year=2028)
        self.assertEqual(
            rows[0]['MP Opening Sentence of Scripture'],
            'The Lord is in his holy temple; let all the earth keep silence before him. habakkuk 2:20',
        )

    def test_optional_feast_name_cannot_replace_primary_season_antiphon(self):
        rows, _ = self.regenerate([{
            'Date': 'Mar 3', 'Observance': 'The Wednesday in Lent',
            'Remembrance': 'An Example Teacher, Remembered for the Annunciation',
        }])
        self.assertEqual(
            rows[0]['Antiphon'],
            'The Lord is full of compassion and mercy: * O come, let us adore him.',
        )

    def test_generic_collect_alternatives_are_explicit_editorial_findings(self):
        source = [dict(row) for row in self.february]
        source[12]['Remembrance'] = 'An Unreviewed Priest'
        _, target = self.regenerate(source)
        findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
        self.assertTrue(any(item['date'] == '2027-02-13' and
                            item['code'] == 'editorial_choice' for item in findings))

    def test_missing_collect_cannot_hide_an_unresolved_commemoration(self):
        rows, target = self.regenerate(self.february)
        rows[13]['Special Collect'] = ''
        with target.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        output = self.work / 'missing-collect'
        result = subprocess.run(
            [sys.executable, str(ROOT / 'generate.py'), '--csv', str(target), '--month', '2',
             '--output-dir', str(output)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        findings = json.loads(output.with_suffix('.review.json').read_text())['findings']
        self.assertTrue(any(item['date'] == '2027-02-14' and
                            item['code'] == 'missing_collect' for item in findings))

    def test_entirely_invalid_input_still_produces_actionable_review_report(self):
        target = self.work / 'bad-2028.csv'
        target.write_text('Date,Remembrance\nFeb 30,\n')
        output = self.work / 'bad-site'
        result = subprocess.run(
            [sys.executable, str(ROOT / 'generate.py'), '--csv', str(target), '--month', '2',
             '--publish', '--output-dir', str(output)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        report = output.with_suffix('.review.json')
        self.assertTrue(report.exists(), 'Invalid input must be reported before date rows are skipped')
        self.assertTrue(any(item['code'] == 'invalid_date'
                            for item in json.loads(report.read_text())['findings']))

    def test_deployment_build_command_rejects_unresolved_prayer_content(self):
        import shlex

        workflow = (ROOT / '.github' / 'workflows' / 'deploy.yml').read_text()
        build_command = next(line.strip() for line in workflow.splitlines()
                             if line.strip().startswith('python generate.py'))
        rows, target = self.regenerate(self.february)
        rows[20]['Special Collect'] = 'Grant peace to the people of _________. Amen.'
        self.save_rows(target, rows)
        output = self.work / 'deployment-site'
        command = [sys.executable] + shlex.split(build_command)[1:] + [
            '--csv', str(target), '--month', '2', '--output-dir', str(output)]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0,
                            'The deployment build command must reject unresolved prayers')
        self.assertFalse(output.exists())

    def test_canonical_month_update_also_writes_review_findings(self):
        canonical = self.work / 'canonical-2027.csv'
        canonical.write_bytes(FIXTURE.read_bytes())
        result = subprocess.run(
            [sys.executable, str(ROOT / 'bin' / 'map_common_prayers.py'),
             '--update-canonical', str(canonical), '--year', '2027', '--month', '2',
             '--antiphon-mode', 'overwrite', '--seasonal-blessing-mode', 'overwrite'],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = canonical.with_suffix('.review.json')
        self.assertTrue(report.exists())
        self.assertFalse(json.loads(report.read_text())['publishable'])

    def test_input_csv_can_supply_explicit_year_without_fetching_a_calendar(self):
        source = self.work / 'manual.csv'
        source.write_text('Date,Observance,Remembrance\nFeb 9,Shrove Tuesday,\n')
        target = self.work / 'manual-draft.csv'
        result = subprocess.run(
            [sys.executable, str(ROOT / 'bin' / 'map_common_prayers.py'), '--in', str(source),
             '--year', '2027', '--out', str(target)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with target.open(newline='') as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual(row['Antiphon'],
                         'The Lord has shown forth his glory: * O come, let us adore him.')
        self.assertTrue(target.with_suffix('.review.json').exists())

    def test_successful_http_status_with_no_calendar_data_is_still_a_source_failure(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from threading import Thread

        class EmptyCalendar(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'<html><body>Temporarily unavailable</body></html>')

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), EmptyCalendar)
        Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        _, source = self.regenerate([self.february[0]])
        target = self.work / 'empty-response-2027.csv'
        result = subprocess.run(
            [sys.executable, str(ROOT / 'bin' / 'map_common_prayers.py'), '--in', str(source),
             '--out', str(target), '--acna-year', '2027', '--ignore-fetch-errors',
             '--acna-base-url', f'http://127.0.0.1:{server.server_port}'],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
        self.assertTrue(any(item['code'] == 'source_error' for item in findings))

    def test_regeneration_clears_old_lenten_blessing_when_2028_feast_is_before_lent(self):
        source = dict(next(row for row in self.february if row['Date'] == 'Feb 24'))
        source['Seasonal Blessing'] = 'A stale Lenten prayer from a different year.'
        rows, _ = self.regenerate([source], year=2028)
        self.assertEqual(rows[0]['Seasonal Blessing'], '')
        self.assertEqual(rows[0]['Liturgical Color'], 'Red')

    def test_generation_requires_year_context_instead_of_silently_skipping_review(self):
        source = self.work / 'manual.csv'
        source.write_text('Date,Observance,Remembrance\nFeb 9,Shrove Tuesday,\n')
        result = subprocess.run(
            [sys.executable, str(ROOT / 'bin' / 'map_common_prayers.py'), '--in', str(source),
             '--out', str(self.work / 'manual-draft.csv')],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--year', result.stderr)

    def test_default_multi_year_build_validates_every_published_csv(self):
        import shutil

        data = self.work / 'data'
        data.mkdir()
        for year in (2027, 2028):
            source = [dict(self.february[0], **{
                'Date': f'Jan {day}', 'Observance': 'Feria', 'Remembrance': '', 'Special Collect': '',
            }) for day in range(1, 32)]
            rows, target = self.regenerate(source, year=year)
            if year == 2028:
                rows[0]['MP Opening Sentence of Scripture'] = 'UNREVIEWED_PLACEHOLDER'
                with target.open('w', newline='') as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
            shutil.copyfile(target, data / f'acna-prayers-{year}.csv')
        shutil.copyfile(ROOT / 'generate.py', self.work / 'generate.py')
        (self.work / 'bin').symlink_to(ROOT / 'bin', target_is_directory=True)
        output = self.work / 'multi-year-site'
        result = subprocess.run(
            [sys.executable, str(self.work / 'generate.py'), '--publish', '--month', '1',
             '--output-dir', str(output)],
            cwd=self.work, capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        report = json.loads(output.with_suffix('.review.json').read_text())
        self.assertEqual(report['years'], [2027, 2028])
        self.assertTrue(any(item['date'].startswith('2028-') and
                            item['code'] == 'unresolved_placeholder' for item in report['findings']))
        self.assertFalse(output.exists())

    def test_reviewed_anskar_collect_names_ministry_without_blanks_in_future_years(self):
        source = next(row for row in self.february if row['Date'] == 'Feb 3')
        for year in (2027, 2028):
            rows, target = self.regenerate([source], year=year)
            prayer = rows[0]['Special Collect']
            self.assertIn('your servant Anskar', prayer)
            self.assertIn('the people of Denmark and Sweden', prayer)
            findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
            self.assertFalse(any(item['field'] == 'Special Collect' for item in findings))

    def test_reviewed_cyril_and_methodius_collect_is_plural_and_names_slavic_people(self):
        source = next(row for row in self.february if row['Date'] == 'Feb 14')
        for year in (2027, 2028):
            rows, target = self.regenerate([source], year=year)
            prayer = rows[0]['Special Collect']
            self.assertIn('your servants Cyril and Methodius', prayer)
            self.assertIn('to the Slavic people', prayer)
            findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
            self.assertFalse(any(item['field'] == 'Special Collect' for item in findings))

    def test_reviewed_thomas_bray_collect_uses_pastor_without_bishop(self):
        source = next(row for row in self.february if row['Date'] == 'Feb 15')
        for year in (2027, 2028):
            rows, target = self.regenerate([source], year=year)
            prayer = rows[0]['Special Collect']
            self.assertIn('your faithful servant Thomas Bray to be a pastor', prayer)
            findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
            self.assertFalse(any(item['field'] == 'Special Collect' for item in findings))

    def test_reviewed_second_batch_collects_persist_across_years(self):
        selections = {
            'Feb 4': ('your servant Cornelius the Centurion', 'great cloud of witnesses'),
            'Feb 5': ('your servants the martyrs of Japan', 'courage to die for this faith'),
            'Feb 21': ('your servant Billy Graham', 'to the peoples of the world'),
        }
        for year in (2027, 2028):
            for day, phrases in selections.items():
                with self.subTest(year=year, day=day):
                    source = next(row for row in self.february if row['Date'] == day)
                    rows, target = self.regenerate([source], year=year)
                    prayer = rows[0]['Special Collect']
                    for phrase in phrases:
                        self.assertIn(phrase, prayer)
                    findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
                    self.assertFalse(any(item['field'] == 'Special Collect' for item in findings))

    def source_row(self, day, observance, remembrance):
        return dict(self.february[0], **{
            'Date': day, 'Observance': observance, 'Remembrance': remembrance, 'Special Collect': '',
        })

    def test_reviewed_perpetua_collect_is_plural_across_years(self):
        source = self.source_row(
            'Mar 7', 'The Fourth Sunday in Lent (Laetare Sunday)',
            'Perpetua and Her Companions, Martyrs at Carthage, 203',
        )
        for year in (2027, 2028):
            rows, target = self.regenerate([source], year=year)
            self.assertIn('your servants Perpetua and her companions boldness', rows[0]['Special Collect'])
            findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
            self.assertFalse(any(item['field'] == 'Special Collect' for item in findings))

    def test_reviewed_march_missionary_collects_name_people_across_years(self):
        selections = {
            'David, Bishop and Apostle of Wales, 601': ('David', 'the people of Wales'),
            'Chad, Bishop of Lichfield and Missionary, 672': ('Chad', 'the people of Mercia'),
            'Felix, Bishop and Missionary to the Angles, 647': ('Felix', 'the people of East Anglia'),
            'Patrick, Bishop and Apostle to the Irish, 461': ('Patrick', 'the Irish people'),
            'Cuthbert, Bishop-Abbot of Lindisfarne and Missionary, 687': ('Cuthbert', 'the people of Northumbria'),
            'Gregory the Illuminator, Missionary to Armenia, 333': ('Gregory the Illuminator', 'the Armenian people'),
            'Charles Henry Brent, Bishop and Missionary to the Philippines, 1929': (
                'Charles Henry Brent', 'the people of the Philippines',
            ),
            'Easter Eve / Charles Henry Brent, Bishop and Missionary to the Philippines, 1929': (
                'Charles Henry Brent', 'the people of the Philippines',
            ),
        }
        for year in (2027, 2028):
            for remembrance, (name, people) in selections.items():
                with self.subTest(year=year, remembrance=remembrance):
                    source = self.source_row('Mar 9', 'Lent', remembrance)
                    rows, target = self.regenerate([source], year=year)
                    prayer = rows[0]['Special Collect']
                    self.assertIn(f'your servant {name} to preach the Gospel to {people}:', prayer)
                    findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
                    self.assertFalse(any(item['field'] == 'Special Collect' for item in findings))

    def test_reviewed_march_final_batch_persists_across_years(self):
        selections = {
            'John and Charles Wesley, Priests and Reformers of the Church, 1791, 1788': (
                'your servants John and Charles Wesley, kindled', 'became burning and shining lights in your Church',
            ),
            'Gregory the Great, Bishop of Rome and Teacher of the Faith, 604': (
                'your servant Gregory the Great special gifts of grace', 'teach the truth',
            ),
            'Cyril, Bishop of Jerusalem and Teacher of the Faith, 386': (
                'your servant Cyril special gifts of grace', 'teach the truth',
            ),
            'Robert Machray, First Primate of Canada, 1904': (
                'your faithful servant Robert Machray to be a Bishop and pastor in your Church',
            ),
            'James DeKoven, Priest, 1879': ('your faithful servant James DeKoven to be a pastor in your Church',),
            'John Donne, Priest and Poet, 1631': ('your faithful servant John Donne to be a pastor in your Church',),
        }
        for year in (2027, 2028):
            for remembrance, phrases in selections.items():
                with self.subTest(year=year, remembrance=remembrance):
                    rows, target = self.regenerate([self.source_row('Mar 9', 'Lent', remembrance)], year=year)
                    for phrase in phrases:
                        self.assertIn(phrase, rows[0]['Special Collect'])
                    findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
                    self.assertFalse(any(item['field'] == 'Special Collect' for item in findings))

    def test_reviewed_january_first_batch_persists_across_years(self):
        selections = {
            'Hilary of Poitiers, Bishop and Teacher of the Faith, 367': (
                'your servant Hilary of Poitiers special gifts of grace',
            ),
            'Thomas Aquinas, Friar, Priest, and Teacher of the Faith, 1274': (
                'your servant Thomas Aquinas special gifts of grace',
            ),
            'Vedanayagam Samuel Azariah, Bishop in South India, Evangelist, 1945': (
                'your servant Vedanayagam Samuel Azariah to preach the Gospel to the people of South India:',
            ),
            'Kentigern, Missionary to Strathclyde and Cumbria, 603': (
                'your servant Kentigern to preach the Gospel to the people of Strathclyde and Cumbria:',
            ),
            'Anthony, Hermit in Egypt, 356': ('inspired by the devotion of your servant Anthony, may seek you',),
            'Wulfstan, Bishop of Worcester, 1095': (
                'your faithful servant Wulfstan to be a Bishop and pastor in your Church',
            ),
        }
        for year in (2027, 2028):
            for remembrance, phrases in selections.items():
                with self.subTest(year=year, remembrance=remembrance):
                    rows, target = self.regenerate([self.source_row('Jan 13', 'Epiphany', remembrance)], year=year)
                    for phrase in phrases:
                        self.assertIn(phrase, rows[0]['Special Collect'])
                    findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
                    self.assertFalse(any(item['field'] == 'Special Collect' for item in findings))

    def test_reviewed_january_companions_are_plural_across_years(self):
        selections = {
            'Timothy and Titus, Companions of Paul the Apostle': (
                'your faithful servants Timothy and Titus to be pastors in your Church',
            ),
            'Lydia, Dorcas and Phoebe, Helpers of the Apostles': (
                'the good example of your servants Lydia, Dorcas, and Phoebe, may persevere',
                'until at last, with them, we attain',
            ),
        }
        for year in (2027, 2028):
            for remembrance, phrases in selections.items():
                with self.subTest(year=year, remembrance=remembrance):
                    rows, target = self.regenerate([self.source_row('Jan 13', 'Epiphany', remembrance)], year=year)
                    prayer = rows[0]['Special Collect']
                    for phrase in phrases:
                        self.assertIn(phrase, prayer)
                    self.assertNotIn('Or this', prayer)
                    findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
                    self.assertFalse(any(item['field'] == 'Special Collect' for item in findings))

    def test_approval_for_one_cyril_does_not_cover_another(self):
        source = self.source_row('Mar 9', 'Lent', 'Cyril of Alexandria, Bishop and Teacher of the Faith, 444')
        rows, target = self.regenerate([source])
        self.assertNotIn('your servant Cyril special gifts', rows[0]['Special Collect'])
        findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
        self.assertTrue(any(item['field'] == 'Special Collect' for item in findings))

    def test_unreviewed_companions_still_require_plural_review(self):
        source = self.source_row('Mar 9', 'Lent', 'Example and Her Companions, Martyrs at Nowhere, 200')
        _, target = self.regenerate([source])
        findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
        self.assertTrue(any(item['code'] == 'plural_collect' for item in findings))

    def test_commemoration_after_temporal_heading_gets_its_common_and_review(self):
        source = self.source_row(
            'Mar 27', 'Holy Saturday', 'Easter Eve / Example Person, Bishop and Missionary to Nowhere, 1900',
        )
        rows, target = self.regenerate([source])
        self.assertIn('to preach the Gospel', rows[0]['Special Collect'])
        findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
        self.assertTrue(any(item['code'] == 'unfilled_blank' for item in findings))

    def test_annunciation_in_holy_week_moves_after_second_sunday_of_easter(self):
        rows, _ = self.regenerate([
            self.source_row('Mar 25', 'Maundy Thursday', 'The Annunciation of Our Lord Jesus Christ'),
            self.source_row('Apr 5', 'The Second Monday of Easter', ''),
        ])
        self.assertEqual(rows[0]['Observance'], 'Maundy Thursday')
        self.assertEqual(rows[0]['Remembrance'], '')
        self.assertEqual(rows[0]['Special Collect'], '')
        self.assertEqual(rows[1]['Remembrance'], 'The Annunciation')
        self.assertIn('announced by an angel to the Virgin Mary', rows[1]['Special Collect'])

    def test_annunciation_outside_holy_week_stays_on_its_date(self):
        rows, _ = self.regenerate([self.source_row('Mar 25', 'Lent', 'The Annunciation')], year=2028)
        self.assertEqual(rows[0]['Remembrance'], 'The Annunciation')
        self.assertIn('announced by an angel to the Virgin Mary', rows[0]['Special Collect'])

    def test_reviewed_pastor_collects_omit_bishop_for_jones_and_herbert(self):
        for year in (2027, 2028):
            for day, name in (('Feb 13', 'Absalom Jones'), ('Feb 27', 'George Herbert')):
                source = next(row for row in self.february if row['Date'] == day)
                rows, target = self.regenerate([source], year=year)
                self.assertIn(f'your faithful servant {name} to be a pastor', rows[0]['Special Collect'])
                findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
                self.assertFalse(any(item['field'] == 'Special Collect' for item in findings))

    def test_reviewed_ember_collect_selects_first_prayer_without_now(self):
        for year in (2027, 2028):
            rows, target = self.regenerate([{'Date': 'Feb 19', 'Observance': 'Lent',
                                             'Remembrance': 'Ember Day'}], year=year)
            prayer = rows[0]['Special Collect']
            self.assertTrue(prayer.startswith('Almighty God, the giver of all good gifts'))
            self.assertIn('all who are called', prayer)
            self.assertNotIn('Or this:', prayer)
            findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
            self.assertFalse(any(item['field'] == 'Special Collect' for item in findings))

    def test_janani_and_ember_day_receive_two_complete_labeled_collects(self):
        source = next(row for row in self.february if row['Date'] == 'Feb 17')
        for year in (2027, 2028):
            rows, target = self.regenerate([source], year=year)
            prayer = rows[0]['Special Collect']
            self.assertIn('Janani Luwum: Almighty God,', prayer)
            self.assertIn('your servant Janani Luwum', prayer)
            self.assertIn('Ember Day: Almighty God, the giver of all good gifts', prayer)
            self.assertIn('all who are called', prayer)
            findings = json.loads(target.with_suffix('.review.json').read_text())['findings']
            self.assertFalse(any(item['field'] == 'Special Collect' for item in findings))

    def test_single_reviewed_collect_does_not_approve_a_two_commemoration_day(self):
        rows, target = self.regenerate(self.february)
        rows[16]['Special Collect'] = rows[16]['Special Collect'].split(' Ember Day:', 1)[0].removeprefix('Janani Luwum: ')
        self.save_rows(target, rows)
        output = self.work / 'incomplete-pair'
        result = subprocess.run(
            [sys.executable, str(ROOT / 'generate.py'), '--csv', str(target), '--month', '2',
             '--publish', '--output-dir', str(output)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        findings = json.loads(output.with_suffix('.review.json').read_text())['findings']
        self.assertTrue(any(item['code'] == 'ambiguous_commemorations' for item in findings))
