"""Exploratory ICD10/EF cross-counts; never an eligibility contract."""
from collections import Counter
from datetime import date
import re

# Explicit I50 search set; code-only evidence, no source/year validation or ICD9 mapping.
HF = {'I50','I501','I502','I503','I504','I508','I509','I5081','I5082','I5083','I5084','I5089'}
HF |= {'I50'+family+suffix for family in ('2','3','4') for suffix in ('0','1','2','3')}
HF |= {'I5081'+suffix for suffix in ('0','1','2','3','4')}
SYSTOLIC = {'I502','I504'} | {'I50'+f+s for f in ('2','4') for s in ('0','1','2','3')}
VIEWS = ('DX_DATE','CALC_DX_DATE')


def evidence(cell):
    if len(cell)>4096:
        return False,False
    tokens=[t.strip().upper() for t in re.split('[,;|]',cell)]
    if not tokens or not all(re.fullmatch(r'[A-Z][0-9][A-Z0-9](?:\.?[A-Z0-9]{1,4})?',t) for t in tokens):
        return False,False
    tokens={t.replace('.','') for t in tokens}
    return bool(tokens & HF),bool(tokens & SYSTOLIC)


def init(db):
    db.execute('CREATE TABLE hf_flags(bucket TEXT, patient TEXT, view TEXT, flag TEXT, PRIMARY KEY(bucket,patient,view,flag)) WITHOUT ROWID')


def add(db,patient,cell,parsed):
    hf,systolic=evidence(cell)
    if not patient or not hf:
        return
    for bucket,anchor in db.execute('SELECT bucket,day FROM meds WHERE patient=?',(patient,)).fetchall():
        for view in VIEWS:
            day=parsed[view]
            relation='date_unusable' if day is None else 'before' if day.isoformat()<anchor else 'same_day' if day.isoformat()==anchor else 'after'
            for kind in (('hf','systolic') if systolic else ('hf',)):
                db.execute('INSERT OR IGNORE INTO hf_flags VALUES (?,?,?,?)',(bucket,patient,view,kind+'_'+relation))


def echo_state(rows,anchor,window):
    if not rows:
        return 'no_prior_echo'
    days={r[0] for r in rows}; bands={r[1] for r in rows}
    if len(days)!=1:
        raise ValueError('latest_day_invariant')
    lag=(date.fromisoformat(anchor)-date.fromisoformat(next(iter(days)))).days
    if lag<=0:
        raise ValueError('preindex_invariant')
    if lag>window:
        return 'prior_echo_outside_window'
    if len(bands)>1:
        return 'recent_latest_day_band_disagreement'
    return 'recent_'+next(iter(bands))


def report(db,arms,window):
    output={}
    for arm in arms:
        groups={v:Counter() for v in VIEWS}
        for patient,anchor in db.execute('SELECT patient,day FROM meds WHERE bucket=?',(arm,)).fetchall():
            rows=db.execute('SELECT day,band FROM latest_echo WHERE bucket=? AND patient=?',(arm,patient)).fetchall()
            state=echo_state(rows,anchor,window)
            for view in VIEWS:
                flags={r[0] for r in db.execute('SELECT flag FROM hf_flags WHERE bucket=? AND patient=? AND view=?',(arm,patient,view))}
                dx='systolic_code_before' if 'systolic_before' in flags else 'other_hf_code_before' if 'hf_before' in flags else 'no_preindex_code_found'
                groups[view][(anchor[:4],dx,state)]+=1
        output[arm]={view:[dict(anchor_year=y,diagnosis_evidence=d,latest_echo_evidence=e,patient_keys=n)
                          for (y,d,e),n in sorted(counts.items())] for view,counts in groups.items()}
        output[arm]['diagnosis_timing_flags']={v:dict(db.execute('SELECT flag,COUNT(*) FROM hf_flags WHERE bucket=? AND view=? GROUP BY flag',(arm,v))) for v in VIEWS}
    return dict(status='exploratory_only',echo_window_days=window,
        rules='Latest strictly prior echo within window; no older-value fallback; no imputed eligibility; exact keys; ICD10 I50 search only, ICD9 not assessed; code absence means not found, not disease absent; date views separate, no fallback. One prior coded record suffices for discovery only.',
        eligible_patients=None,by_arm=output)
