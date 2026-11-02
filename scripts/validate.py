#!/usr/bin/env python3
"""Validate catalog links, hashes, source count and vector geometry. --quick needs stdlib only."""
from pathlib import Path
import argparse,base64,hashlib,json,re,sqlite3,sys,struct
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--quick',action='store_true');a=ap.parse_args();errors=[];checks=0
 def check(ok,msg):
  nonlocal checks
  checks+=1
  if not ok:errors.append(msg)
 data=json.loads((ROOT/'catalog/catalog.json').read_text());src=json.loads((ROOT/'data/source/memes.json').read_text());records=data['records'];byid={r['id']:r for r in records}
 check(len(byid)==len(records),'duplicate IDs');check(len(src)==len(records),'source/catalog counts differ')
 image_count=0
 for r in records:
  check(bool(r['title']) and len(r['visual_description'])>=30,f'{r["id"]} missing description')
  check(r['status'] in ['reviewed','draft','needs_replacement'],f'{r["id"]} invalid status')
  check(r['confidence'] in ['high','medium','low'],f'{r["id"]} invalid confidence')
  for key,rel in r['files'].items():
   p=ROOT/rel;check(p.is_file(),f'missing {rel}');check(p.resolve().is_relative_to(ROOT),f'unsafe {rel}')
   if p.is_file() and key in ['master_png','delivery_webp']:
    expected=r['provenance'].get('sha256_master' if key=='master_png' else 'sha256_delivery')
    if expected:check(hashlib.sha256(p.read_bytes()).hexdigest()==expected,f'hash mismatch {rel}')
   if not a.quick and p.is_file():
    from PIL import Image
    try:
     with Image.open(p) as im:im.verify();image_count+=1
    except Exception as e:check(False,f'bad image {rel}: {e}')
  for alt in r['alternates']:
   for k in ['png','webp','original_jpg']:
    if alt.get(k):check((ROOT/alt[k]).is_file(),f'missing alternate {alt[k]}')
  seen={r['id']};parent=r.get('related_to')
  while parent:
   if parent not in byid or parent in seen:check(False,f'invalid/cyclic relation {r["id"]}');break
   seen.add(parent);parent=byid[parent].get('related_to')
 for p in ROOT.rglob('*'):
  if p.is_file() and '.git' not in p.parts:check(p.stat().st_size<100*1024*1024,f'file exceeds 100 MiB: {p.relative_to(ROOT)}')
 r=byid['HAMPTER_0127'];joined=' '.join([r['title'],r['visual_description'],r['reaction'],*r['tags'],*r['use_cases']]).lower()
 check('блокнот' in joined and not any(x in joined for x in ['food tray','fork','поднос','вилк']),'notebook regression')
 check('death' not in byid['HAMPTER_0001']['content_warnings'],'deadpan warning regression')
 model=json.loads((ROOT/'data/embeddings/lsa.json').read_text());check(model['catalog_hash']==data['catalog_hash'],'stale LSA model');check(model['ids']==[r['id'] for r in records if r['status']=='reviewed'],'vector ordering/count')
 raw=base64.b64decode(model['vectors_b64']);dim=model['dimensions'];vals=struct.unpack('<'+'f'*(len(raw)//4),raw);check(len(vals)==len(model['ids'])*dim,'bad vector shape')
 norms=[sum(x*x for x in vals[i:i+dim])**.5 for i in range(0,len(vals),dim)];check(all(abs(n-1)<.001 for n in norms),'vectors not normalized')
 con=sqlite3.connect(ROOT/'catalog/asset_index.sqlite');check(con.execute('PRAGMA integrity_check').fetchone()[0]=='ok','sqlite integrity');check(con.execute('SELECT count(*) FROM assets').fetchone()[0]==len(records),'sqlite rows');con.close()
 report={'checks':checks,'errors':errors,'records':len(records),'active':sum(r['status']=='reviewed' for r in records),'image_files_verified':image_count,'vector_type':'TF-IDF / LSA (not neural)','dimensions':dim,'vector_norm_min':min(norms),'vector_norm_max':max(norms),'catalog_hash':data['catalog_hash'],'mode':'quick' if a.quick else 'full'}
 (ROOT/'qa/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2));return bool(errors)
if __name__=='__main__':sys.exit(main())
