"""Apply individually researched/visually reviewed cultural and emotional annotations.

Sources under data/source are the editable truth; generated catalogs are derived.
Do not infer authorship, canonical emotions or legal clearance from fan-meme context.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

FIELDS = (
    'НАЗВАНИЕ', 'ВИДНО', 'РЕАКЦИЯ', 'ПОДТЕКСТ', 'МЕХАНИКА',
    'КОНТЕКСТ', 'ПОДХОДИТ', 'НЕ ПУТАТЬ', 'ПОИСК',
)


def split_choices(value: str) -> list[str]:
    return [s.strip() for s in str(value or '').split('||') if s.strip()]


def split_semicolons(value: str) -> list[str]:
    return [s.strip() for s in str(value or '').split(';') if s.strip()]


def apply_annotations(records: list[dict], root: Path) -> tuple[list[dict], dict, dict]:
    annotation_path = root / 'data/source/annotations.json'
    sources_path = root / 'data/source/reference_sources.json'
    if not annotation_path.is_file():
        # Older snapshots and newly initialized collections still build without annotations.
        return records, {}, {}
    annotations = json.loads(annotation_path.read_text(encoding='utf-8'))
    sources = json.loads(sources_path.read_text(encoding='utf-8')) if sources_path.exists() else {}
    available = {int(r['id'].split('_')[-1]) for r in records}
    assert available == {int(k) for k in annotations}, (
        'Every public meme must have its own annotation; review additions before publishing',
        sorted(available - {int(k) for k in annotations}),
        sorted({int(k) for k in annotations} - available),
    )
    for r in records:
        raw = annotations[str(int(r['id'].split('_')[-1]))]
        missing = [k for k in FIELDS if not isinstance(raw.get(k), str) or not raw[k].strip()]
        assert not missing, (r['id'], missing)
        phrase_list = split_semicolons(raw['ПОИСК'])
        use_cases = split_choices(raw['ПОДХОДИТ'])
        subtext = split_choices(raw['ПОДТЕКСТ'])
        key_list = split_semicolons(raw.get('ИСТОЧНИКИ', ''))
        for key in key_list:
            assert key in sources, ('Unknown reference source', r['id'], key)
            assert sources[key]['url'].startswith('https://'), (r['id'], key)
        if raw.get('ПЕРСОНАЖ'):
            parts = [p.strip() for p in raw['ПЕРСОНАЖ'].split('|')]
            assert len(parts) == 3 and parts[2] in ('high', 'medium', 'low'), (r['id'], parts)
            character = {
                'character': parts[0], 'franchise': parts[1], 'confidence': parts[2],
                'type': 'hamster_parody_or_cosplay',
            }
            r['character_reference'] = character
        # Accurate, per-image tags replace old generic descriptors in the search corpus.
        # Old values are retained for provenance only; they do not cause false matches.
        r['title'] = raw['НАЗВАНИЕ'].strip()
        r['visual_description'] = raw['ВИДНО'].strip()
        r['reaction'] = raw['РЕАКЦИЯ'].strip()
        r['use_cases'] = use_cases
        new_terms = phrase_list[:]
        if r.get('character_reference'):
            new_terms += [r['character_reference']['character'], r['character_reference']['franchise']]
        if r.get('restoration'):
            new_terms += ['отреставрировано', 'прозрачный фон']
        # Preserve order; avoid duplicate or invisible tags.
        r['tags'] = list(dict.fromkeys(t for t in new_terms if t.strip()))
        r['analysis'] = {
            'version': '3.0.0',
            'provenance': 'individual_curated_visual_reading',
            'visible_details': raw['ВИДНО'].strip(),
            'nuanced_emotion': raw['РЕАКЦИЯ'].strip(),
            'subtext': subtext,
            'humor_mechanism': raw['МЕХАНИКА'].strip(),
            'cultural_context': raw['КОНТЕКСТ'].strip(),
            'suggested_situations': use_cases,
            'not_to_confuse_with': raw['НЕ ПУТАТЬ'].strip(),
            'search_phrases': phrase_list,
            'visible_text': raw.get('ТЕКСТ', '').strip(),
            'source_keys': key_list,
            'sources': [{'id': key, **sources[key]} for key in key_list],
            'interpretation_not_canonical': True,
        }
        # Explicit visible_text is evidence, not an inferred conversational quote.
        assert r['visual_description'] and r['reaction'] and r['tags'], r['id']
    return records, annotations, sources
