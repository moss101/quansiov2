#!/usr/bin/env python3
from pathlib import Path
import json, sys
from jsonschema import Draft202012Validator, FormatChecker
ROOT=Path(__file__).resolve().parents[1]
errors=[]
registry=json.load(open(ROOT/'registries/schema-registry.json'))
registered={x['name']:ROOT/x['path'] for x in registry}
actual={json.load(open(p))['title']:p for p in ROOT.glob('schemas/*.schema.json')}
if set(registered)!=set(actual): errors.append(f'schema registry mismatch registered={sorted(registered)} actual={sorted(actual)}')
for name,p in actual.items():
    try: Draft202012Validator.check_schema(json.load(open(p)))
    except Exception as e: errors.append(f'{name}: invalid schema: {e}')
valid_names={p.stem for p in (ROOT/'tests/fixtures/valid').glob('*.json')}
invalid_names={p.stem for p in (ROOT/'tests/fixtures/invalid').glob('*.json')}
if valid_names!=set(actual): errors.append(f'valid fixture coverage mismatch missing={sorted(set(actual)-valid_names)} extra={sorted(valid_names-set(actual))}')
if invalid_names!=set(actual): errors.append(f'invalid fixture coverage mismatch missing={sorted(set(actual)-invalid_names)} extra={sorted(invalid_names-set(actual))}')
for p in sorted((ROOT/'tests/fixtures/valid').glob('*.json')):
    name=p.stem
    if name not in actual: errors.append(f'valid fixture has unknown schema {name}'); continue
    v=Draft202012Validator(json.load(open(actual[name])),format_checker=FormatChecker())
    es=list(v.iter_errors(json.load(open(p))))
    if es: errors.append(f'valid fixture {p.name} rejected: {es[0].message}')
for p in sorted((ROOT/'tests/fixtures/invalid').glob('*.json')):
    name=p.stem
    if name not in actual: errors.append(f'invalid fixture has unknown schema {name}'); continue
    v=Draft202012Validator(json.load(open(actual[name])),format_checker=FormatChecker())
    if not list(v.iter_errors(json.load(open(p)))): errors.append(f'invalid fixture {p.name} was accepted')
if errors:
    print('CONTRACT VALIDATION: FAIL'); [print('- '+e) for e in errors]; sys.exit(1)
print(f'CONTRACT VALIDATION: PASS ({len(actual)} schemas, {len(list((ROOT/"tests/fixtures/valid").glob("*.json")))} valid and {len(list((ROOT/"tests/fixtures/invalid").glob("*.json")))} invalid fixtures)')
