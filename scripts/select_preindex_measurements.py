"""Synthetic-tested baseline selection primitive; no JDAT adapter or clinical map.

Call only with explicit normalized events and contracts. No patient data logging,
file access, cohort eligibility, imputation or matching is implemented here.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable, Optional, Tuple


class SelectionError(ValueError):
    """Static errors only, never include record values."""


@dataclass(frozen=True)
class MeasurementRule:
    feature: str
    lookback_days: int
    unit: str
    mapping_version: str
    validity_version: str

    def __post_init__(self):
        if not all((self.feature, self.unit, self.mapping_version, self.validity_version)):
            raise SelectionError('unresolved_measurement_contract')
        if type(self.lookback_days) is not int or self.lookback_days < 1:
            raise SelectionError('invalid_lookback')


@dataclass(frozen=True)
class Measurement:
    patient: str
    feature: str
    observed_day: Optional[date]
    available_day: Optional[date]
    value: Optional[Decimal]
    unit: Optional[str]
    # Upstream mapping must distinguish qualified/invalid/marker values.
    value_status: str
    snapshot: str
    source_id: str
    source_row: int
    mapping_version: str
    validity_version: str

    @property
    def lineage(self):
        return (self.snapshot, self.source_id, self.source_row)


@dataclass(frozen=True)
class Selection:
    status: str
    value: Optional[Decimal] = None
    observed_day: Optional[date] = None
    provenance: Tuple[Tuple[str, str, int], ...] = ()
    issues: Tuple[str, ...] = ()


def select_measurement(events: Iterable[Measurement], *, patient: str,
                       index_day: date, rule: MeasurementRule,
                       source_status: str) -> Selection:
    """Latest observation in [index-lookback,index), with no older-value fallback.

    Input is one patient's mapped feature stream, potentially across reviewed
    sources. Events for any other patient/feature fail rather than being silently
    mixed. source_status is available/unavailable/coverage_unknown. Availability
    means source ingestion, not complete capture of care. Unknown event dates
    block selection because their position relative to index is unknowable.

    Latest-day disagreement or any invalid latest-day value blocks selection.
    Unknown/late availability of the latest observation also blocks selection;
    it does not trigger selection of an older observation. Same-day and later
    observations cannot affect the selected baseline value. Counts and detailed
    source QC should be maintained separately by the future cluster adapter.
    """
    if type(index_day) is not date or not patient:
        raise SelectionError('invalid_anchor')
    if source_status not in ('available', 'unavailable', 'coverage_unknown'):
        raise SelectionError('invalid_source_status')
    if source_status != 'available':
        return Selection('source_' + source_status)
    latest = None
    rows = {}
    unknown_day = False
    for event in events:
        if event.patient != patient or event.feature != rule.feature:
            raise SelectionError('mixed_patient_or_feature')
        if (event.mapping_version, event.validity_version) != (rule.mapping_version, rule.validity_version):
            raise SelectionError('measurement_contract_mismatch')
        if not event.snapshot or not event.source_id or type(event.source_row) is not int or event.source_row < 1:
            raise SelectionError('missing_lineage')
        if event.value_status not in ('observed', 'missing', 'invalid', 'qualified'):
            raise SelectionError('invalid_value_status')
        if event.observed_day is None:
            unknown_day = True
            continue
        if type(event.observed_day) is not date:
            raise SelectionError('invalid_observation_day')
        lag = (index_day - event.observed_day).days
        if not 1 <= lag <= rule.lookback_days:
            continue
        if latest is None or event.observed_day > latest:
            latest, rows = event.observed_day, {}
        if event.observed_day == latest:
            previous = rows.get(event.lineage)
            if previous is not None and previous != event:
                raise SelectionError('conflicting_source_row')
            rows[event.lineage] = event
    if unknown_day:
        return Selection('event_date_unresolved')
    if latest is None:
        return Selection('no_record_in_window')
    issues = set()
    values = set()
    for event in rows.values():
        if event.available_day is None:
            issues.add('availability_unknown')
        elif type(event.available_day) is not date:
            raise SelectionError('invalid_availability_day')
        elif event.available_day < event.observed_day:
            issues.add('availability_before_observation')
        elif event.available_day >= index_day:
            issues.add('not_available_before_index')
        if event.unit is None:
            issues.add('unit_unknown')
        elif event.unit != rule.unit:
            issues.add('unit_mismatch')
        if event.value_status != 'observed':
            issues.add('value_' + event.value_status)
        elif not isinstance(event.value, Decimal) or not event.value.is_finite():
            issues.add('invalid_numeric_value')
        else:
            values.add(event.value)
    if len(values) > 1:
        issues.add('latest_day_disagreement')
    provenance = tuple(sorted(rows))
    if issues:
        return Selection('latest_observation_unusable', observed_day=latest,
                         provenance=provenance, issues=tuple(sorted(issues)))
    return Selection('observed', next(iter(values)), latest, provenance)
