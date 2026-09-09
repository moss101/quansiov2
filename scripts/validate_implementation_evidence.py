#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, subprocess, sys
from jsonschema import Draft202012Validator, FormatChecker
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def git(repo,*args): return subprocess.run(['git','-C',str(repo),*args],text=True,capture_output=True)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--evidence',required=True); ap.add_argument('--protected-ref',default='HEAD'); args=ap.parse_args()
 repo=Path(args.repo).resolve(); evp=Path(args.evidence).resolve(); ev=json.load(open(evp)); errs=[]
 schema=json.load(open(ROOT/'schemas/ImplementationEvidence.schema.json')); v=Draft202012Validator(schema,format_checker=FormatChecker()); errs += [f'schema: {e.message}' for e in v.iter_errors(ev)]
 tasks={t['task_id']:t for t in json.load(open(ROOT/'registries/tasks.json'))}; reqs={r['requirement_id']:r for r in json.load(open(ROOT/'registries/requirements.json'))}
 t=tasks.get(ev.get('task_id'))
 if not t: errs.append('unknown task_id')
 if t:
  expected_req=set(t['requirement_ids']); expected_ta={a['assertion_id'] for a in t['assertions'] if a.get('blocking',True)}; expected_ra={reqs[r]['assertion_id'] for r in t['requirement_ids']}
  if set(ev.get('requirement_ids',[]))!=expected_req: errs.append('requirement coverage mismatch')
  if set(ev.get('task_assertion_ids',[]))!=expected_ta: errs.append('task assertion coverage mismatch')
  if set(ev.get('requirement_assertion_ids',[]))!=expected_ra: errs.append('requirement assertion coverage mismatch')
  if ev.get('status')=='PASS' and t.get('real_boundary_required') and not ev.get('real_boundary'): errs.append('real boundary required but false')
 if ev.get('status')=='BLOCKED_REAL_BOUNDARY':
  print('EVIDENCE VALIDATION: BLOCKED_REAL_BOUNDARY (non-completing)'); return 2
 commit=ev.get('git_commit','')
 if git(repo,'cat-file','-e',commit+'^{commit}').returncode!=0: errs.append('commit does not exist')
 elif git(repo,'merge-base','--is-ancestor',commit,args.protected_ref).returncode!=0: errs.append('commit is not reachable from protected ref')
 rp=repo/ev.get('report_path','')
 if not rp.is_file(): errs.append('verification report missing')
 else:
  if sha(rp)!=ev.get('report_digest'): errs.append('report digest mismatch')
  try: report=json.load(open(rp))
  except Exception as e: report=None; errs.append('report is not valid JSON')
  if report:
   rv=Draft202012Validator(json.load(open(ROOT/'schemas/VerificationReport.schema.json')),format_checker=FormatChecker())
   errs += [f'report schema: {e.message}' for e in rv.iter_errors(report)]
   if report.get('task_id')!=ev.get('task_id') or report.get('git_commit')!=commit: errs.append('report task/commit mismatch')
   if report.get('repository_id')!=ev.get('repository_id'): errs.append('report repository identity mismatch')
   if report.get('protected_ref')!=args.protected_ref: errs.append('report protected-ref mismatch')
   if report.get('real_boundary')!=ev.get('real_boundary'): errs.append('report/evidence real-boundary mismatch')
   if ev.get('status')=='PASS' and report.get('status')!='PASS': errs.append('outer PASS cannot wrap non-PASS report')
   ars={a['assertion_id']:a for a in report.get('assertion_results',[])}
   blocking_report_ids={a['assertion_id'] for a in report.get('assertion_results',[]) if a.get('blocking',True)}
   if t:
    if blocking_report_ids != (expected_ta|expected_ra): errs.append('blocking report assertion set mismatch')
    for aid in expected_ta|expected_ra:
     if aid not in ars: errs.append(f'missing report assertion {aid}')
     elif ars[aid].get('blocking',True) and ars[aid].get('status')!='PASS': errs.append(f'blocking assertion not PASS: {aid}')
   report_artifacts={ar.get('path_or_uri'):ar.get('digest') for ar in report.get('artifact_records',[])}
   if report_artifacts != ev.get('artifact_digests',{}): errs.append('evidence/report artifact set mismatch')
   for ar in report.get('artifact_records',[]):
    method=ar.get('verification_method'); loc=ar.get('path_or_uri',''); digest=ar.get('digest')
    if method=='LOCAL_HASH':
     p=repo/loc
     if not p.is_file() or sha(p)!=digest: errs.append(f'local artifact mismatch: {loc}')
    elif method in {'REMOTE_DIGEST_LOOKUP','TRUSTED_BUILD_ATTESTATION'}:
     ref=ar.get('verification_receipt_ref')
     if not ref:
      errs.append(f'remote artifact lacks verification receipt: {loc}')
     else:
      receipt=(repo/ref).resolve()
      try:
       receipt.relative_to(repo)
      except ValueError:
       errs.append(f'remote verification receipt escapes repository: {loc}')
       receipt=None
      if receipt is not None:
       if not receipt.is_file():
        errs.append(f'remote verification receipt missing: {loc}')
       else:
        try: rr=json.load(open(receipt))
        except Exception:
         rr=None; errs.append(f'remote verification receipt invalid JSON: {loc}')
        if rr is not None:
         rrs=json.load(open(ROOT/'schemas/RemoteArtifactVerification.schema.json'))
         rrv=Draft202012Validator(rrs,format_checker=FormatChecker())
         errs += [f'remote receipt schema {loc}: {e.message}' for e in rrv.iter_errors(rr)]
         if rr.get('path_or_uri')!=loc or rr.get('expected_digest')!=digest or rr.get('observed_digest')!=digest: errs.append(f'remote verification receipt identity/digest mismatch: {loc}')
         if rr.get('verification_method')!=method or rr.get('status')!='PASS': errs.append(f'remote verification receipt did not prove PASS with requested method: {loc}')
         if method=='TRUSTED_BUILD_ATTESTATION' and rr.get('attestation_path'):
          apath=(repo/rr['attestation_path']).resolve()
          try: apath.relative_to(repo)
          except ValueError: errs.append(f'attestation path escapes repository: {loc}'); apath=None
          if apath is not None and (not apath.is_file() or sha(apath)!=rr.get('attestation_digest')): errs.append(f'attestation artifact mismatch: {loc}')
    else: errs.append(f'unknown artifact verification method: {method}')
 if errs:
  print('EVIDENCE VALIDATION: FAIL'); [print('- '+e) for e in errs]; return 1
 if ev.get('status')!='PASS': print('EVIDENCE VALIDATION: NON-PASS'); return 1
 print('EVIDENCE VALIDATION: PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
