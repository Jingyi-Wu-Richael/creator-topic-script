#!/usr/bin/env python3
"""Read-only consistency checks and rough speaking-time estimates. Python 3.9+."""

import argparse
from collections import Counter
from datetime import datetime
import json
import math
from pathlib import Path
import re
import sys


def positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def text(value):
    return isinstance(value, str) and bool(value.strip())


def aware_time(value):
    if not isinstance(value, str):
        return False
    try:
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return stamp.utcoffset() is not None
    except ValueError:
        return False


def check_record(record):
    errors, warnings = [], []
    if not isinstance(record, dict):
        return {'structural_valid': False, 'errors': ['record must be an object'], 'warnings': []}

    def error(message):
        errors.append(message)

    def obj(value, where):
        if not isinstance(value, dict):
            error(f'{where} must be an object')
            return {}
        return value

    def strings(value, where):
        if not isinstance(value, list) or any(not text(v) for v in value):
            error(f'{where} must be an array of nonempty strings')
            return []
        return value

    def require_fields(row, fields, where):
        for field in fields:
            if not text(row.get(field)):
                error(f'{where}.{field} must be nonempty text')

    def choice(row, field, options, where):
        value = row.get(field)
        if not isinstance(value, str) or value not in options:
            error(f'{where}.{field} must be one of {", ".join(sorted(options))}')

    def index(value, where):
        if not isinstance(value, list):
            error(f'{where} must be an array')
            return {}
        result = {}
        for pos, value_row in enumerate(value):
            row = obj(value_row, f'{where}[{pos}]')
            item_id = row.get('id')
            if not text(item_id):
                error(f'{where}[{pos}] needs a nonempty id')
            elif item_id in result:
                error(f'{where}: duplicate id {item_id}')
            else:
                result[item_id] = row
        return result

    if record.get('schema_version') != 'creator-topic-script/v1':
        error('unsupported schema_version')
    context = obj(record.get('context'), 'context')
    choice(context, 'mode', {'scout', 'research', 'materials', 'script'}, 'context')
    if not aware_time(context.get('as_of')):
        error('context.as_of needs an ISO timestamp with timezone')
    target = context.get('target_seconds')
    if target is not None and not positive(target):
        error('context.target_seconds must be positive or null')
    count = context.get('topic_count')
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        error('context.topic_count must be a positive integer')

    sources = index(record.get('sources'), 'sources')
    claims = index(record.get('claims'), 'claims')
    topics = index(record.get('topics'), 'topics')

    for sid, source in sources.items():
        where = f'source {sid}'
        require_fields(source, ['locator', 'read_scope'], where)
        choice(source, 'kind', {'official', 'paper', 'repository', 'firsthand', 'secondary', 'social', 'user_material'}, where)
        choice(source, 'access', {'read', 'partial', 'unread'}, where)
        if not aware_time(source.get('observed_at')):
            error(f'{where}.observed_at needs an ISO timestamp with timezone')
        if source.get('kind') == 'firsthand' and not text(source.get('test_context')):
            error(f'{where} needs test_context for firsthand evidence')

    def readable_refs(ids, where):
        usable = []
        for sid in ids:
            if sid not in sources:
                error(f'{where} references unknown source {sid}')
            elif sources[sid].get('access') in ('read', 'partial'):
                usable.append(sources[sid])
        return usable

    for cid, claim in claims.items():
        where = f'claim {cid}'
        require_fields(claim, ['text', 'evidence_note'], where)
        choice(claim, 'kind', {'fact', 'inference', 'unverified'}, where)
        choice(claim, 'status', {'supported', 'conflicting', 'missing'}, where)
        choice(claim, 'scope', {'attributed', 'independent', 'personal_test'}, where)
        refs = strings(claim.get('source_ids'), f'{where}.source_ids')
        usable = readable_refs(refs, where)
        if claim.get('status') == 'supported':
            if not usable:
                error(f'{where}: supported claim needs readable evidence')
            if any(sid in sources and sources[sid].get('access') == 'unread' for sid in refs):
                error(f'{where}: unread source cannot be supporting evidence')
            if claim.get('kind') == 'unverified':
                error(f'{where}: unverified claim cannot be marked supported')
        if claim.get('scope') == 'personal_test' and not any(s.get('kind') == 'firsthand' for s in usable):
            error(f'{where}: personal_test requires readable firsthand evidence')
        if any(s.get('access') == 'partial' for s in usable):
            warnings.append(f'{where}: verify the claim is limited to the portion actually read')

    def claim_refs(ids, where, require_supported=False):
        for cid in ids:
            if cid not in claims:
                error(f'{where} references unknown claim {cid}')
            elif require_supported and (claims[cid].get('status') != 'supported' or claims[cid].get('kind') == 'unverified'):
                error(f'{where} uses unresolved claim {cid}')

    event_keys = []
    for tid, topic in topics.items():
        where = f'topic {tid}'
        require_fields(topic, ['title', 'event_key', 'angle', 'audience', 'reason', 'proof_visual'], where)
        choice(topic, 'decision', {'ready', 'needs_material', 'hold'}, where)
        strings(topic.get('gaps'), f'{where}.gaps')
        refs = strings(topic.get('claim_ids'), f'{where}.claim_ids')
        claim_refs(refs, where, topic.get('decision') == 'ready')
        if text(topic.get('event_key')):
            event_keys.append(topic['event_key'])
    for event, total in Counter(event_keys).items():
        if total > 1:
            warnings.append(f'{event}: {total} topic cards share an event; check that the angles are distinct')

    selection = obj(record.get('selection'), 'selection')
    choice(selection, 'basis', {'pending', 'user', 'delegated'}, 'selection')
    picked = selection.get('topic_id')
    if picked is not None and (not isinstance(picked, str) or picked not in topics):
        error('selection.topic_id must reference an existing topic or be null')
    if selection.get('basis') == 'pending':
        if picked is not None:
            error('pending selection cannot have a selected topic')
    elif not text(picked) or not text(selection.get('reason')):
        error('user/delegated selection needs topic_id and the actual selection/authorization reason')

    if 'draft' not in record:
        error('draft is required; use null before writing')
    draft_value = record.get('draft')
    if draft_value is not None:
        draft = obj(draft_value, 'draft')
        if selection.get('basis') not in ('user', 'delegated') or not text(picked):
            error('draft requires user selection or delegated selection')
        if draft.get('topic_id') != picked:
            error('draft.topic_id does not match the selected topic')
        segments = index(draft.get('segments'), 'segments')
        if not segments:
            error('draft needs at least one segment')
        total_seconds = 0.0
        for segid, seg in segments.items():
            where = f'segment {segid}'
            require_fields(seg, ['spoken'], where)
            if not positive(seg.get('seconds')):
                error(f'{where}.seconds must be a finite positive number')
            else:
                total_seconds += seg['seconds']
            refs = strings(seg.get('claim_ids'), f'{where}.claim_ids')
            claim_refs(refs, where, True)
            for cid in refs:
                if cid in claims and claims[cid].get('kind') == 'inference':
                    warnings.append(f'{where}: express {cid} as a judgment, not an established fact')
        if positive(target) and abs(total_seconds - target) > max(3, target * 0.05):
            warnings.append(f'planned segment total {total_seconds:g}s differs from target {target:g}s')
        shots = draft.get('shots')
        if not isinstance(shots, list):
            error('draft.shots must be an array')
            shots = []
        covered = set()
        for pos, shot_value in enumerate(shots):
            where = f'shot {pos + 1}'
            shot = obj(shot_value, where)
            segid = shot.get('segment_id')
            if not text(segid) or segid not in segments:
                error(f'{where} references an unknown segment')
            else:
                covered.add(segid)
            require_fields(shot, ['visual'], where)
            choice(shot, 'status', {'available', 'to_capture', 'illustration'}, where)
            refs = strings(shot.get('source_ids'), f'{where}.source_ids')
            usable = readable_refs(refs, where)
            if shot.get('status') == 'available' and not usable:
                error(f'{where}: available asset needs a readable material reference')
        for segid in segments.keys() - covered:
            error(f'segment {segid} has no matching shot')

    return {'structural_valid': not errors, 'errors': errors, 'warnings': warnings,
            'limits': 'Checks declared structure and references only; verify source meaning, truth, timing and publication requirements separately.'}


def duration_estimate(script, target=90.0, cps=4.2, pause=10.0):
    if not positive(target) or not positive(cps) or not isinstance(pause, (int, float)) or isinstance(pause, bool) or not math.isfinite(pause) or pause < 0:
        raise ValueError('target/cps must be finite positive numbers and pause must be finite and nonnegative')
    if not text(script):
        raise ValueError('spoken text is empty')
    han = len(re.findall(r'[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0002fa1f]', script))
    words = len(re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)*", script))
    digits = len(re.findall(r'\d', script))
    units = han + words * 1.8 + digits
    if units == 0:
        raise ValueError('no supported spoken units; estimate Chinese/English text only')
    seconds = units / cps + pause
    return {'han_characters': han, 'english_words': words, 'digits': digits, 'equivalent_units': round(units, 1),
            'estimated_seconds': round(seconds, 1), 'reference_range_seconds': [round(units / 4.8 + pause, 1), round(units / 3.6 + pause, 1)],
            'target_seconds': target, 'over_target_at_selected_rate': seconds > target,
            'note': 'Rough Chinese/English estimate including specified pause budget; read aloud to verify actual duration.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    check = commands.add_parser('check', help='Check a record without changing it')
    check.add_argument('record')
    duration = commands.add_parser('duration', help='Estimate duration of plain spoken text')
    duration.add_argument('script')
    duration.add_argument('--target', type=float, default=90)
    duration.add_argument('--cps', type=float, default=4.2)
    duration.add_argument('--pause', type=float, default=10)
    args = parser.parse_args()
    try:
        if args.command == 'check':
            result = check_record(json.loads(Path(args.record).read_text(encoding='utf-8-sig')))
            code = 0 if result['structural_valid'] else 1
        else:
            result = duration_estimate(Path(args.script).read_text(encoding='utf-8-sig'), args.target, args.cps, args.pause)
            code = 0
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    except (OSError, ValueError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
