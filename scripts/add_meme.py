#!/usr/bin/env python3
"""Import ONE static image. Does not guess descriptions or silently mark drafts reviewed."""
from __future__ import annotations
import argparse,hashlib,json,re,shutil,sys
from pathlib import Path
from datetime import date
from PIL import Image,ImageOps,UnidentifiedImageError
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic_json(p,v):
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('image',type=Path);ap.add_argument('--collection',required=True);ap.add_argument('--collection-name');ap.add_argument('--slug',required=True);ap.add_argument('--title',required=True);ap.add_argument('--description',required=True);ap.add_argument('--reaction',required=True);ap.add_argument('--tag',action='append',default=[]);ap.add_argument('--use-case',action='append',default=[]);ap.add_argument('--warning',action='append',default=[]);ap.add_argument('--source-url',action='append',default=[]);ap.add_argument('--author',default='Не установлен');ap.add_argument('--id');ap.add_argument('--reviewed',action='store_true');ap.add_argument('--human-approved',action='store_true');a=ap.parse_args()
 for name,v in [('collection',a.collection),('slug',a.slug)]:
  if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',v) or len(v)>80:ap.error(name+' must be lower-case ASCII words separated by hyphens (max 80 characters)')
 if not a.image.is_file():ap.error('Image not found')
 if len(a.description.strip())<30:ap.error('Describe visible features in at least 30 characters')
 records=json.loads((ROOT/'data/source/memes.json').read_text());collections=json.loads((ROOT/'data/source/collections.json').read_text());ids={r['id'] for r in records}
 n=1
 while f'MEME_{n:04d}' in ids:n+=1
 ident=a.id or f'MEME_{n:04d}'
 if not re.fullmatch(r'[A-Z][A-Z0-9_]{2,39}',ident) or ident in ids:ap.error('Invalid or duplicate ID')
 if a.collection not in {c['id'] for c in collections} and not a.collection_name:ap.error('New collection requires --collection-name')
 with Image.open(a.image) as source:
  if getattr(source,'n_frames',1)>1:ap.error('This importer handles static images only; animated assets need a separate pipeline')
  source.load();ext={"JPEG":'.jpg',"PNG":'.png',"WEBP":'.webp'}.get(source.format)
  if not ext:ap.error('Supported source formats: PNG, JPEG, WebP')
  im=ImageOps.exif_transpose(source).convert('RGBA')
 stem=f'{ident}_{a.slug}';paths={'master_png':f'media/masters/{stem}.png','delivery_webp':f'media/webp/{stem}.webp','thumbnail_webp':f'media/thumbs/{ident}.webp'}
 created=[]
 try:
  raw=ROOT/f'originals/imports/{stem}{ext}';raw.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a.image,raw);created.append(raw)
  for p in paths.values():(ROOT/p).parent.mkdir(parents=True,exist_ok=True)
  im.save(ROOT/paths['master_png'],optimize=True);created.append(ROOT/paths['master_png'])
  im.save(ROOT/paths['delivery_webp'],lossless=True,method=6);created.append(ROOT/paths['delivery_webp'])
  h=sha(ROOT/paths['master_png'])
  if any(r.get('provenance',{}).get('sha256_master')==h for r in records):raise ValueError('Exact normalized duplicate of an existing master; link as a variant instead')
  thumb=im.copy();thumb.thumbnail((296,296),Image.Resampling.LANCZOS);canvas=Image.new('RGBA',(320,320),(255,255,255,0));canvas.alpha_composite(thumb,((320-thumb.width)//2,(320-thumb.height)//2));canvas.save(ROOT/paths['thumbnail_webp'],lossless=True);created.append(ROOT/paths['thumbnail_webp'])
  rec={'id':ident,'collection_id':a.collection,'slug':a.slug,'title':a.title,'visual_description':a.description,'reaction':a.reaction,'use_cases':a.use_case,'tags':a.tag,'content_warnings':a.warning,'confidence':'medium','status':'reviewed' if a.reviewed else 'draft','review':{'method':'user supplied annotation','date':date.today().isoformat(),'reviewer':'importer','human_approved':a.human_approved},'related_to':None,'relation_type':None,'width':im.width,'height':im.height,'has_alpha':im.getchannel('A').getextrema()[0]<255,'quality':'low_resolution' if min(im.size)<160 else 'standard','files':paths,'alternates':[],'provenance':{'source_urls':a.source_url,'original_file':raw.relative_to(ROOT).as_posix(),'sha256_original':sha(raw),'sha256_master':h,'sha256_delivery':sha(ROOT/paths['delivery_webp'])},'rights':{'status':'not_cleared','attribution':a.author}}
  records.append(rec)
  if a.collection not in {c['id'] for c in collections}:collections.append({'id':a.collection,'name':a.collection_name,'description':'Новая коллекция','cover_id':ident,'attribution':a.author,'rights_status':'not_cleared'})
  atomic_json(ROOT/'data/source/memes.json',records);atomic_json(ROOT/'data/source/collections.json',collections)
 except Exception:
  for p in created:p.unlink(missing_ok=True)
  raise
 print(f'Imported {ident} as {rec["status"]}. Next: python scripts/build.py --vectors && python scripts/validate.py')
if __name__=='__main__':
 try:main()
 except (ValueError,OSError,UnidentifiedImageError) as e:raise SystemExit(str(e))
