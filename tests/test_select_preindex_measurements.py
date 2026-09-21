from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from select_preindex_measurements import Measurement, MeasurementRule, SelectionError, select_measurement


class PreindexTests(unittest.TestCase):
    def setUp(self):
        self.index = date(2024, 4, 1)
        self.rule = MeasurementRule('synthetic_lab', 90, 'synthetic_unit', 'map_v1', 'valid_v1')
        self.event = Measurement('SYNTHETIC', 'synthetic_lab', self.index - timedelta(days=2),
                                 self.index - timedelta(days=1), Decimal('5'), 'synthetic_unit',
                                 'observed', 'snapshot_v1', 'labs_2025', 1, 'map_v1', 'valid_v1')

    def select(self, events, **kwargs):
        return select_measurement(events, patient='SYNTHETIC', index_day=self.index,
                                  rule=self.rule, source_status=kwargs.get('source_status', 'available'))

    def event_at(self, lag, value='5', row=2):
        day = self.index - timedelta(days=lag)
        return replace(self.event, observed_day=day, available_day=day, value=Decimal(value), source_row=row)

    def test_inclusive_lookback_strict_preindex_and_future_invariance(self):
        oldest = self.event_at(90)
        self.assertEqual(self.select([oldest]).status, 'observed')
        self.assertEqual(self.select([self.event_at(91)]).status, 'no_record_in_window')
        baseline = self.select([self.event])
        self.assertEqual(self.select([self.event_at(0, '99'), self.event_at(-1, '1'), self.event]), baseline)

    def test_nearest_observation_independent_of_input_order(self):
        older = self.event_at(30, '8')
        a = self.select([older, self.event]); b = self.select([self.event, older])
        self.assertEqual(a, b)
        self.assertEqual(a.value, Decimal('5'))
        self.assertEqual(a.provenance, (self.event.lineage,))

    def test_missing_latest_does_not_fall_back(self):
        latest = replace(self.event, value=None, value_status='missing')
        r = self.select([self.event_at(30), latest])
        self.assertIsNone(r.value)
        self.assertIn('value_missing', r.issues)
        self.assertEqual(r.observed_day, latest.observed_day)

    def test_unknown_or_late_availability_and_no_older_fallback(self):
        for availability, issue in [(None, 'availability_unknown'), (self.index, 'not_available_before_index'),
                                    (self.index + timedelta(days=1), 'not_available_before_index')]:
            r = self.select([self.event_at(30), replace(self.event, available_day=availability)])
            self.assertIsNone(r.value); self.assertIn(issue, r.issues)

    def test_unknown_or_mismatched_unit_not_inferred(self):
        for unit, issue in [(None, 'unit_unknown'), ('another_unit', 'unit_mismatch')]:
            r = self.select([replace(self.event, unit=unit)])
            self.assertIsNone(r.value); self.assertIn(issue, r.issues)

    def test_latest_day_conflicts_not_arbitrarily_selected(self):
        other = replace(self.event, source_id='labs_2026', value=Decimal('9'))
        a = self.select([self.event, other]); b = self.select([other, self.event])
        self.assertEqual(a, b)
        self.assertIn('latest_day_disagreement', a.issues)
        self.assertEqual(len(a.provenance), 2)

    def test_equal_values_retain_both_sources_and_duplicate_input_is_idempotent(self):
        other = replace(self.event, source_id='labs_2026')
        r = self.select([self.event, other, self.event])
        self.assertEqual(r.value, Decimal('5')); self.assertEqual(len(r.provenance), 2)

    def test_mixed_patient_feature_and_contract_fail(self):
        for change in ({'patient':'OTHER'}, {'feature':'other'}, {'mapping_version':'map_v2'},
                       {'validity_version':'valid_v2'}, {'source_row':0}):
            with self.assertRaises(SelectionError): self.select([replace(self.event, **change)])

    def test_source_missing_not_zero_or_imputed(self):
        self.assertEqual(self.select([], source_status='unavailable').status, 'source_unavailable')
        self.assertEqual(self.select([], source_status='coverage_unknown').status, 'source_coverage_unknown')
        self.assertEqual(self.select([]).status, 'no_record_in_window')

    def test_undated_event_blocks_even_with_good_dated_record(self):
        r = self.select([self.event, replace(self.event, observed_day=None, source_row=3)])
        self.assertEqual(r.status, 'event_date_unresolved'); self.assertIsNone(r.value)

    def test_qualified_and_nonfinite_numbers_not_observed(self):
        for change in ({'value_status':'qualified'}, {'value':Decimal('NaN')}, {'value':Decimal('Infinity')}, {'value':5.0}):
            self.assertIsNone(self.select([replace(self.event, **change)]).value)

    def test_conflicting_same_source_row_and_reversed_availability(self):
        with self.assertRaisesRegex(SelectionError, 'conflicting_source_row'):
            self.select([self.event, replace(self.event, value=Decimal('6'))])
        r = self.select([replace(self.event, available_day=self.index - timedelta(days=3))])
        self.assertIn('availability_before_observation', r.issues)

    def test_invalid_latest_tie_cannot_be_hidden_by_valid_tie(self):
        invalid = replace(self.event, value_status='invalid', source_row=2)
        r = self.select([self.event, invalid])
        self.assertIsNone(r.value); self.assertIn('value_invalid', r.issues)


if __name__ == '__main__': unittest.main()
