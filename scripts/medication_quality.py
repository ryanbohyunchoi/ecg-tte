"""Aggregate-only profiling helpers; no clinical semantics or eligibility inferred."""
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re

DATES = ('ORDER_INST', 'START_DATE', 'END_DATE', 'DISCONTINUE_TIME')
NUMBERS = ('QUANTITY_DISPENSED', 'REFILLS', 'REFILLS_REMAINING')
IDENTIFIERS = ('PAT_MRN_ID', 'ORDER_MED_ID', 'MEDICATION_ID')
DETAIL_CATEGORIES = ('ORDERING_MODE', 'ORDER_MODE', 'ORDER_SOURCE',
                     'ORDER_CLASS', 'ORDER_STATUS', 'DISPENSED_UNIT',
                     'REORDERED_YN', 'MODIFIED_YN')
MARKERS = {'NULL', 'NONE', 'N/A', 'NA', 'NAN', 'NAT', 'UNKNOWN', '\\N'}
ISO = re.compile(r'^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})?)?$')
MDY = re.compile(r'^\d{1,2}/\d{1,2}/\d{4}(?: \d{1,2}:\d{2}:\d{2}(?: [AP]M)?)?$')
NUMBER = re.compile(r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d{1,3})?$')


def missing_kind(value):
    value = value.strip()
    if not value:
        return 'blank'
    if value.upper() in MARKERS:
        return 'candidate_marker_' + value.upper()
    return None


def date_kind(value):
    """Calendar validity under explicit format hypotheses; no dates returned."""
    value = value.strip()
    missing = missing_kind(value)
    if missing:
        return missing
    try:
        if ISO.fullmatch(value):
            datetime.fromisoformat(value.replace('Z', '+00:00'))
            return 'parseable_iso'
        if MDY.fullmatch(value):
            fmt = '%m/%d/%Y'
            if ' ' in value:
                fmt += ' %I:%M:%S %p' if value.endswith(('AM', 'PM')) else ' %H:%M:%S'
            datetime.strptime(value, fmt)
            return 'parseable_month_first_hypothesis'
    except ValueError:
        return 'invalid_calendar_or_clock'
    return 'unrecognized_format'


def number_kind(value, integer=False):
    value = value.strip()
    missing = missing_kind(value)
    if missing:
        return missing
    if len(value) > 128 or not NUMBER.fullmatch(value):
        return 'unrecognized_numeric_format'
    try:
        number = Decimal(value)
        if not number.is_finite():
            return 'nonfinite'
        if number < 0:
            return 'negative'
        if integer and number != number.to_integral_value():
            return 'noninteger'
        return 'zero' if number == 0 else 'positive'
    except InvalidOperation:
        return 'unrecognized_numeric_format'


class QualityAudit:
    def __init__(self, connection, index):
        self.db, self.index = connection, index
        self.fields = {name: Counter() for name in (*DATES, *NUMBERS, *IDENTIFIERS) if name in index}
        self.present = sorted(set((*DATES, *NUMBERS, *IDENTIFIERS, *DETAIL_CATEGORIES)) & index.keys())
        self.order_fields = sorted((set(self.present) | ({'DOSE', 'DOSE_UNIT',
            'MEDICATION_ROUTE', 'FREQUENCY'} & index.keys())) - {'PAT_MRN_ID'})
        self.missing_orders = 0
        self.db.execute('CREATE TABLE order_audit (id TEXT PRIMARY KEY, patient TEXT, fingerprint TEXT, n INTEGER, changed INTEGER, patient_conflict INTEGER) WITHOUT ROWID')

    def add(self, row):
        def get(name):
            return row[self.index[name]].strip() if name in self.index else ''
        for name, counts in self.fields.items():
            value = get(name)
            if name in DATES:
                kind = date_kind(value)
            elif name in NUMBERS:
                kind = number_kind(value, integer=name != 'QUANTITY_DISPENSED')
            else:
                kind = missing_kind(value) or ('quoted_nonempty_key' if '"' in value else 'other_nonempty_key')
            counts[kind] += 1
        if 'ORDER_MED_ID' not in self.index:
            return
        order = get('ORDER_MED_ID')
        if missing_kind(order):
            self.missing_orders += 1
            return
        patient = get('PAT_MRN_ID')
        patient = None if missing_kind(patient) else patient
        # Hash only the disclosed audit projection, never SIG/free-text instructions.
        fingerprint = hashlib.sha256(json.dumps([get(n) for n in self.order_fields]).encode()).hexdigest()
        self.db.execute('''INSERT INTO order_audit VALUES (?, ?, ?, 1, 0, 0)
            ON CONFLICT(id) DO UPDATE SET
                n=n+1,
                changed=MAX(changed, fingerprint != excluded.fingerprint),
                patient_conflict=MAX(patient_conflict, CASE WHEN patient IS NOT NULL
                    AND excluded.patient IS NOT NULL AND patient != excluded.patient THEN 1 ELSE 0 END),
                patient=COALESCE(patient, excluded.patient)''', (order, patient, fingerprint))

    def result(self):
        counts = self.db.execute('''SELECT COUNT(*), COALESCE(SUM(n),0),
            COALESCE(SUM(n>1),0), COALESCE(SUM(n-1),0), COALESCE(SUM(changed),0),
            COALESCE(SUM(patient_conflict),0) FROM order_audit''').fetchone()
        order = None
        if 'ORDER_MED_ID' in self.index:
            order = dict(zip(('distinct_nonmarker_order_keys', 'rows_with_nonmarker_order_key',
                              'repeated_order_keys', 'rows_beyond_first_per_order_key',
                              'order_keys_with_differing_audit_fields', 'order_keys_linked_to_multiple_nonmarker_patient_keys'), counts))
            order['rows_blank_or_candidate_marker_order_key'] = self.missing_orders
        return {'fields_present': self.present,
                'field_quality': {name: dict(counts) for name, counts in self.fields.items()},
                'candidate_null_markers': sorted(MARKERS),
                'null_policy': 'Candidate markers reported separately; semantics not frozen. Excluded from order-key comparison only.',
                'date_policy': 'ISO or explicit month-first hypothesis; parseability is not clinical validity, availability time, or dispensing.',
                'number_policy': 'Finite decimal notation; no unit conversion or dose-derived supply. Refills checked for nonnegative integers.',
                'order_key_audit': order,
                'order_comparison_fields': self.order_fields,
                'duplicate_policy': 'Repeated order keys are not automatically duplicate events. Changed audited fields may represent updates; no records removed.',
                'verified_outpatient_fill_patients': None}
