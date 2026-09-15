import copy
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/check_work.py'
spec = importlib.util.spec_from_file_location('creator_check', SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def fixture():
    # Synthetic local fixture; not a product claim or actual user performance result.
    return {
        'schema_version': 'creator-topic-script/v1',
        'context': {'mode': 'script', 'as_of': '2026-09-15T08:00:00+08:00', 'target_seconds': 90, 'topic_count': 3},
        'sources': [{'id': 'S01', 'locator': 'synthetic://fixture-A', 'kind': 'user_material', 'access': 'read',
                     'observed_at': '2026-09-15T08:00:00+08:00', 'read_scope': 'Synthetic sentence: the note lists three steps.'}],
        'claims': [{'id': 'C01', 'text': 'The supplied note lists three steps.', 'kind': 'fact', 'status': 'supported',
                    'source_ids': ['S01'], 'evidence_note': 'Synthetic note, sentence 1', 'scope': 'attributed'}],
        'topics': [{'id': 'T01', 'title': 'Explain the supplied note', 'event_key': 'fixture-note', 'angle': 'Turn the note into an explanation',
                    'audience': 'A reader of the note', 'claim_ids': ['C01'], 'decision': 'ready', 'reason': 'The note is provided',
                    'gaps': [], 'proof_visual': 'Capture the note'}],
        'selection': {'topic_id': 'T01', 'basis': 'user', 'reason': 'Test request explicitly selected T01'},
        'draft': {'topic_id': 'T01', 'segments': [{'id': 'P01', 'spoken': '这份材料列出了三个步骤。', 'seconds': 90, 'claim_ids': ['C01']}],
                  'shots': [{'segment_id': 'P01', 'visual': 'Record the note', 'source_ids': [], 'status': 'to_capture'}]}
    }


class RecordChecks(unittest.TestCase):
    def test_supported_material_to_draft(self):
        self.assertTrue(checker.check_record(fixture())['structural_valid'])

    def test_unread_source_cannot_support_claim(self):
        r = fixture(); r['sources'][0]['access'] = 'unread'
        self.assertFalse(checker.check_record(r)['structural_valid'])

    def test_link_to_missing_source(self):
        r = fixture(); r['claims'][0]['source_ids'] = ['S99']
        self.assertFalse(checker.check_record(r)['structural_valid'])

    def test_unresolved_claim_cannot_enter_spoken_script(self):
        r = fixture(); r['claims'][0]['status'] = 'conflicting'; r['topics'][0]['decision'] = 'needs_material'
        self.assertFalse(checker.check_record(r)['structural_valid'])

    def test_unknown_claim_reference(self):
        r = fixture(); r['draft']['segments'][0]['claim_ids'] = ['C99']
        self.assertFalse(checker.check_record(r)['structural_valid'])

    def test_external_source_cannot_be_personal_test(self):
        r = fixture(); r['claims'][0]['scope'] = 'personal_test'
        self.assertFalse(checker.check_record(r)['structural_valid'])

    def test_personal_test_needs_context(self):
        r = fixture(); r['sources'][0]['kind'] = 'firsthand'; r['claims'][0]['scope'] = 'personal_test'
        self.assertFalse(checker.check_record(r)['structural_valid'])
        r['sources'][0]['test_context'] = 'Synthetic local test input and procedure'
        self.assertTrue(checker.check_record(r)['structural_valid'])

    def test_pending_choice_keeps_cards_but_blocks_draft(self):
        r = fixture(); r['selection'] = {'topic_id': None, 'basis': 'pending', 'reason': ''}
        self.assertFalse(checker.check_record(r)['structural_valid'])
        r['draft'] = None
        self.assertTrue(checker.check_record(r)['structural_valid'])

    def test_delegated_choice_continues(self):
        r = fixture(); r['selection'] = {'topic_id': 'T01', 'basis': 'delegated', 'reason': 'The user asked to choose and write directly'}
        self.assertTrue(checker.check_record(r)['structural_valid'])

    def test_duplicate_ids_rejected(self):
        r = fixture(); r['sources'].append(copy.deepcopy(r['sources'][0]))
        self.assertFalse(checker.check_record(r)['structural_valid'])

    def test_shots_cover_all_segments(self):
        r = fixture(); r['draft']['shots'] = []
        self.assertFalse(checker.check_record(r)['structural_valid'])

    def test_claiming_existing_asset_needs_material(self):
        r = fixture(); r['draft']['shots'][0]['status'] = 'available'
        self.assertFalse(checker.check_record(r)['structural_valid'])
        r['draft']['shots'][0]['source_ids'] = ['S01']
        self.assertTrue(checker.check_record(r)['structural_valid'])

    def test_negative_and_nonfinite_duration(self):
        for seconds in (0, -1, True, math.nan, math.inf):
            with self.subTest(seconds=seconds):
                r = fixture(); r['draft']['segments'][0]['seconds'] = seconds
                self.assertFalse(checker.check_record(r)['structural_valid'])

    def test_same_event_is_warning_not_forced_deletion(self):
        r = fixture(); second = copy.deepcopy(r['topics'][0]); second['id'] = 'T02'; second['angle'] = 'A different audience question'; r['topics'].append(second)
        result = checker.check_record(r)
        self.assertTrue(result['structural_valid']); self.assertTrue(result['warnings'])

    def test_malformed_input_reports_errors(self):
        for value in (None, [], 'bad', {'schema_version': 'wrong'}, {'context': [], 'sources': [False], 'claims': [], 'topics': [], 'selection': [], 'draft': {}}):
            with self.subTest(value=value):
                self.assertFalse(checker.check_record(value)['structural_valid'])

    def test_date_needs_timezone(self):
        r = fixture(); r['context']['as_of'] = '2026-09-15'
        self.assertFalse(checker.check_record(r)['structural_valid'])

    def test_cli_is_read_only_and_reports_exit_codes(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'record.json'; p.write_text(json.dumps(fixture()), encoding='utf8'); before = p.read_bytes()
            ok = subprocess.run([sys.executable, '-B', str(SCRIPT), 'check', str(p)], capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0); self.assertEqual(before, p.read_bytes())
            p.write_text('{invalid', encoding='utf8')
            bad = subprocess.run([sys.executable, '-B', str(SCRIPT), 'check', str(p)], capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)


class SpeakingTime(unittest.TestCase):
    def test_known_count_and_longer_copy(self):
        short = checker.duration_estimate('你好，AI 90秒。', pause=0)
        self.assertEqual(short['han_characters'], 3); self.assertEqual(short['english_words'], 1); self.assertEqual(short['digits'], 2)
        longer = checker.duration_estimate('你好，AI 90秒。' * 10, pause=0)
        self.assertGreater(longer['estimated_seconds'], short['estimated_seconds'])

    def test_speech_rate_and_pauses_change_estimate(self):
        sample = '资料整理成脚本。' * 20
        slow = checker.duration_estimate(sample, cps=3.6, pause=0)
        fast = checker.duration_estimate(sample, cps=4.8, pause=0)
        paused = checker.duration_estimate(sample, cps=4.8, pause=10)
        self.assertGreater(slow['estimated_seconds'], fast['estimated_seconds'])
        self.assertAlmostEqual(paused['estimated_seconds'] - fast['estimated_seconds'], 10, places=1)

    def test_empty_and_invalid_rates(self):
        for sample, kwargs in [('', {}), ('...', {}), ('你好', {'cps': 0}), ('你好', {'target': -1}), ('你好', {'pause': math.nan})]:
            with self.subTest(sample=sample, kwargs=kwargs):
                with self.assertRaises(ValueError): checker.duration_estimate(sample, **kwargs)


if __name__ == '__main__':
    unittest.main(verbosity=2)
