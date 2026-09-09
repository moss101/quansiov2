#!/usr/bin/env python3
from pathlib import Path
import json, tempfile, subprocess, hashlib, sys, os
ROOT=Path(__file__).resolve().parents[1]
def run(*a,**kw): return subprocess.run(list(a),text=True,capture_output=True,**kw)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(cond,msg,errs):
 if not cond: errs.append(msg)
errs=[]
# Placeholder scanner: production marker must fail, test marker must not.
with tempfile.TemporaryDirectory() as td:
 p=Path(td); (p/'app').mkdir(); (p/'tests').mkdir(); (p/'app/x.py').write_text('def f():\n    raise NotImplementedError()\n'); (p/'tests/x.py').write_text('def f():\n    raise NotImplementedError()\n')
 q=run(sys.executable,str(ROOT/'scripts/scan_production_placeholders.py'),td); check(q.returncode!=0,'placeholder scanner accepted production NotImplementedError',errs)
 (p/'app/x.py').write_text('def f():\n    return 1\n'); q=run(sys.executable,str(ROOT/'scripts/scan_production_placeholders.py'),td); check(q.returncode==0,'placeholder scanner rejected clean production tree/test fixture',errs)
# Evidence validator adversarial tests in a real disposable git repo.
with tempfile.TemporaryDirectory() as td:
 repo=Path(td); run('git','init','-q',td); run('git','-C',td,'config','user.email','test@example.invalid'); run('git','-C',td,'config','user.name','test'); (repo/'artifact.bin').write_bytes(b'abc'); run('git','-C',td,'add','.'); run('git','-C',td,'commit','-qm','init'); commit=run('git','-C',td,'rev-parse','HEAD').stdout.strip()
 t=next(x for x in json.load(open(ROOT/'registries/tasks.json')) if x['task_id']=='GOV-001'); R={r['requirement_id']:r for r in json.load(open(ROOT/'registries/requirements.json'))}
 aids=[a['assertion_id'] for a in t['assertions'] if a.get('blocking',True)]; raids=[R[r]['assertion_id'] for r in t['requirement_ids']]
 report={'schema_revision':'9.0.0','report_id':'rep-1','task_id':'GOV-001','repository_id':'repo-test','git_commit':commit,'protected_ref':'HEAD','ci_run_id':'ci-1','ci_pipeline_id':'pipe-1','environment_id':'env-1','configuration_digest':'0'*64,'status':'PASS','assertion_results':[{'assertion_id':a,'blocking':True,'status':'PASS'} for a in aids+raids],'artifact_records':[{'path_or_uri':'artifact.bin','digest':sha(repo/'artifact.bin'),'verification_method':'LOCAL_HASH','verification_receipt_ref':None}],'real_boundary':False,'executed_at':'2026-01-01T00:00:00Z'}
 rp=repo/'report.json'; rp.write_text(json.dumps(report)); ev={'schema_revision':'9.0.0','evidence_id':'ev-1','task_id':'GOV-001','requirement_ids':t['requirement_ids'],'task_assertion_ids':aids,'requirement_assertion_ids':raids,'repository_id':'repo-test','git_commit':commit,'report_path':'report.json','report_digest':sha(rp),'status':'PASS','real_boundary':False,'artifact_digests':{'artifact.bin':sha(repo/'artifact.bin')},'rollback_verified':True,'created_at':'2026-01-01T00:00:00Z'}; ep=repo/'ev.json'; ep.write_text(json.dumps(ev))
 cmd=[sys.executable,str(ROOT/'scripts/validate_implementation_evidence.py'),'--repo',str(repo),'--evidence',str(ep),'--protected-ref','HEAD']
 check(run(*cmd).returncode==0,'evidence validator rejected valid evidence',errs)
 # Embedded FAIL with outer PASS.
 bad=json.loads(json.dumps(report)); bad['assertion_results'][0]['status']='FAIL'; rp.write_text(json.dumps(bad)); ev['report_digest']=sha(rp); ep.write_text(json.dumps(ev)); check(run(*cmd).returncode!=0,'evidence validator accepted blocking FAIL inside outer PASS',errs)
 # Artifact substitution.
 rp.write_text(json.dumps(report)); ev['report_digest']=sha(rp); ep.write_text(json.dumps(ev)); (repo/'artifact.bin').write_bytes(b'changed'); check(run(*cmd).returncode!=0,'evidence validator accepted substituted artifact',errs)
 # Report repository and protected-ref identity must match the selected evidence context.
 (repo/'artifact.bin').write_bytes(b'abc')
 bad=json.loads(json.dumps(report)); bad['repository_id']='other-repo'; rp.write_text(json.dumps(bad)); ev['report_digest']=sha(rp); ep.write_text(json.dumps(ev)); check(run(*cmd).returncode!=0,'evidence validator accepted report repository substitution',errs)
 bad=json.loads(json.dumps(report)); bad['protected_ref']='refs/heads/not-selected'; rp.write_text(json.dumps(bad)); ev['report_digest']=sha(rp); ep.write_text(json.dumps(ev)); check(run(*cmd).returncode!=0,'evidence validator accepted protected-ref substitution',errs)
 # Remote artifacts require a concrete verification receipt; a descriptor alone is insufficient.
 uri='oci://registry.example/artifact@sha256:'+('a'*64)
 remote=json.loads(json.dumps(report)); remote['artifact_records']=[{'path_or_uri':uri,'digest':'a'*64,'verification_method':'REMOTE_DIGEST_LOOKUP','verification_receipt_ref':'remote-receipt.json'}]; rp.write_text(json.dumps(remote)); ev['artifact_digests']={uri:'a'*64}; ev['report_digest']=sha(rp); ep.write_text(json.dumps(ev)); check(run(*cmd).returncode!=0,'evidence validator accepted unchecked remote artifact',errs)
 receipt={'schema_revision':'9.0.0','verification_id':'rav-1','path_or_uri':uri,'expected_digest':'a'*64,'observed_digest':'a'*64,'verification_method':'REMOTE_DIGEST_LOOKUP','status':'PASS','verifier_identity':'ci','environment_id':'env-1','observed_at':'2026-01-01T00:00:00Z','attestation_path':None,'attestation_digest':None}; (repo/'remote-receipt.json').write_text(json.dumps(receipt)); check(run(*cmd).returncode==0,'evidence validator rejected valid remote verification receipt',errs)
 receipt['observed_digest']='b'*64; (repo/'remote-receipt.json').write_text(json.dumps(receipt)); check(run(*cmd).returncode!=0,'evidence validator accepted remote digest mismatch',errs)
 # Restore local report/evidence then test nonexistent commit.
 rp.write_text(json.dumps(report)); ev['artifact_digests']={'artifact.bin':sha(repo/'artifact.bin')}; ev['report_digest']=sha(rp); ev['git_commit']='f'*40; ep.write_text(json.dumps(ev)); check(run(*cmd).returncode!=0,'evidence validator accepted nonexistent commit',errs)
 # BLOCKED remains non-completing.
 ev['git_commit']=commit; ev['status']='BLOCKED_REAL_BOUNDARY'; ep.write_text(json.dumps(ev)); check(run(*cmd).returncode==2,'BLOCKED_REAL_BOUNDARY did not return non-completing status',errs)
if errs:
 print('VALIDATOR SELF-TEST: FAIL'); [print('- '+e) for e in errs]; sys.exit(1)
print('VALIDATOR SELF-TEST: PASS')
