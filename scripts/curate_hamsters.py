#!/usr/bin/env python3
"""Curate the single white meme-hamster collection without generative image models.

Conservative selection and traceable image operations: flood-fill/matting, selective
palette correction, Lanczos resizing and light unsharp masking.  The script does
NOT invent resolution, detail, or copyright rights; it preserves old source hashes.
Run from repository root: python scripts/curate_hamsters.py
"""
from __future__ import annotations
import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/source/memes.json'

# Explicit visual review. Not an automatic keyword filter: e.g. an actual HAMSTER
# holding two cats remains in the collection, while a stand-alone cat is excluded.
EXCLUDE = {
  21: 'realistic rodent with hands, not the white mascot drawing',
  27: 'standalone dog character',
  32: 'Neco-Arc cat character, not a hamster redraw',
  42: 'Christmas couple illustration with no recognizable meme hamster',
  43: 'standalone cat close-up',
  44: 'Neco-Arc cat character, not a hamster redraw',
  46: 'red creature unrelated to the hamster mascot',
  50: 'red creature plus a real human face',
  88: 'reposted photograph/montage of rodents, not the white mascot',
  103: 'photographic montage of rodents, not the white mascot',
  105: 'standalone white kitten',
  106: 'standalone white kitten',
  128: 'Neco-Arc cat on all fours',
  155: 'green alien kitten, not the hamster drawing',
  221: 'illustrated pair of real hamsters, not the white meme mascot',
  222: 'vertical crop of the real-hamster illustration',
  223: 'near-blank invalid asset, previously quarantined',
  235: 'rodent in human hand from a different artwork',
  236: 'standalone pixel-art green cat',
  248: 'Ghostface mask alone, no identifiable hamster',
  261: 'standalone drawing of a human with curly hair',
  309: 'crop of the unrelated illustrated pair of real hamsters',
  324: 'standalone cat with turquoise pigtails (Miku cosplay)',
  388: 'photograph of a hanging tree ornament',
  389: 'photograph of a hanging snowman ornament',
  433: 'standalone human caricature with purple afro',
}

# Retain related versions only if the compositional changes actually introduce new
# content (not resized versions, tighter crops, re-uploads, or letterboxed copies).
RETAIN_DISTINCT_VARIANTS={431,432}

# Only these larger edits are known to preserve the same complete composition.
# Black-bar vertical stickers, stylized pixelation and tighter/different crops
# are never promoted even when their canvas has more pixels.
PROMOTION_ALLOW={(1,270),(22,291),(34,287),(65,288),(87,391),(91,290),
                 (156,279),(162,274),(182,278),(185,277),(209,276),
                 (216,275),(231,272)}

# Positive identifiers grounded in the costume/recognizable drawn cues.
# A source *inspired by* a copyrighted character is not that character's official art.
CHARACTERS={
 68: ('Duo (possible inspiration)', 'Duolingo', 'low', ['дуолинго','duolingo','дуо']),
 78: ('Punk', 'punk style / subculture', 'medium', ['панк','punk']),
 89: ('Link', 'The Legend of Zelda', 'high', ['линк','link','zelda','зельда']),
 104: ('Super Saiyan', 'Dragon Ball', 'medium', ['суперсайян','dragon ball','драгонбол']),
 110: ('Batman', 'DC Comics', 'high', ['бэтмен','batman','dc']),
 112: ('Chewbacca', 'Star Wars', 'medium', ['чубакка','chewbacca','star wars']),
 114: ('Naruto Uzumaki', 'Naruto', 'high', ['наруто','naruto','узумаки']),
 119: ('Spider-Man', 'Marvel', 'high', ['человек-паук','spider man','marvel']),
 120: ('Superman', 'DC Comics', 'high', ['супермен','superman','dc']),
 126: ('Peter Parker / Spider-Man', 'Marvel', 'medium', ['питер паркер','spider-man','marvel']),
 131: ('Sans', 'Undertale', 'high', ['санс','sans','undertale']),
 137: ('Hatsune Miku', 'Vocaloid', 'high', ['мику','miku','vocaloid']),
 138: ('Duo (possible inspiration)', 'Duolingo', 'low', ['дуолинго','duolingo','duo']),
 147: ('Minion', 'Despicable Me', 'high', ['миньон','minion','гадкий я']),
 160: ('Geralt of Rivia', 'The Witcher', 'medium', ['геральт','witcher','ведьмак']),
 188: ('Edward Elric', 'Fullmetal Alchemist', 'medium', ['эдвард элрик','fma','стальной алхимик']),
 211: ('Propeller-hat mascot', 'internet meme', 'low', ['propeller hat']),
 225: ('Zombie', 'zombie genre', 'medium', ['зомби','zombie']),
 238: ('Dracula', 'vampire archetype', 'medium', ['дракула','dracula','вампир']),
 243: ('Joker', 'DC Comics', 'medium', ['джокер','joker']),
 247: ('Jack Sparrow', 'Pirates of the Caribbean', 'medium', ['джек воробей','jack sparrow']),
 265: ('The Grinch', 'Dr. Seuss', 'high', ['гринч','grinch']),
 281: ('Snowman', 'winter character', 'high', ['снеговик','snowman']),
 283: ('Rudolph', 'Rudolph the Red-Nosed Reindeer', 'medium', ['рудольф','rudolph']),
 295: ('Phoenix Wright', 'Ace Attorney', 'medium', ['феникс райт','phoenix wright','ace attorney']),
 325: ('Superhero', 'animated superhero', 'low', ['супергерой','superhero']),
 345: ('Kris', 'Deltarune', 'medium', ['крис','kris','дельтарун','deltarune']),
 346: ('Ralsei', 'Deltarune', 'high', ['ральзей','ralsei','дельтарун','deltarune']),
 347: ('Susie', 'Deltarune', 'high', ['сьюзи','susie','дельтарун','deltarune']),
 370: ('Che Guevara', 'historical-person parody', 'medium', ['че гевара','che guevara']),
 379: ('Spider-Man', 'Marvel', 'high', ['человек-паук','spider man','marvel']),
 441: ('Pikachu', 'Pokémon', 'high', ['пикачу','pikachu','покемон','pokemon']),
}

# Programmatic work applied only to unique originals, with no AI re-rendering.
# Source colors are immutable; only the external background is removed.
RESTORE = {
  6: 'background extraction and contour cleanup',
  68: 'light-green background removal and original green fill preserved',
  70: 'green hamster facial/outline cleanup; preserve alien antennae',
  89: 'matte removal for Link costume',
  119: 'matte removal for Spider-Man costume',
  138: 'black background removal, original green fill preserved',
  147: 'original yellow character preserved, keep overalls and goggles',
  152: 'original yellow face preserved, keep orange sweatshirt',
  239: 'green alien body -> white, keep green antennae',
  334: 'bright-original green fill preserved',
  345: 'original cyan face preserved, preserve Kris hair and scarf',
  346: 'matte removal for Ralsei costume',
  347: 'original purple face preserved, preserve Susie hair and dark clothing',
  441: 'original yellow character preserved, preserve ears, cheeks and tail',
  460: 'repair open silhouette, isolate against transparency, resize conservatively',
}


def num(record):
    return int(record['id'].split('_')[-1])


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bg_remove(im: Image.Image, image_id:int):
    """Separate contiguous near-background regions without erasing enclosed white fur."""
    rgb=np.asarray(im.convert('RGB')).copy()
    h,w=rgb.shape[:2]
    k=max(5,min(w,h)//20)
    samples=np.concatenate((rgb[:k,:k].reshape(-1,3),rgb[:k,-k:].reshape(-1,3)))
    bg=np.median(samples,axis=0).astype(np.float32)
    dist=np.linalg.norm(rgb.astype(np.float32)-bg,axis=2)
    tol=58 if image_id==68 else (30 if np.mean(bg)<80 else 23)
    ink=(dist>tol).astype('uint8')
    ink=cv2.morphologyEx(ink,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    # An open-bottom outline can leak; bridge the visible ends if they approach frame.
    for y in range(h-1,max(0,h-35),-1):
        xs=np.flatnonzero(ink[y])
        if len(xs)>10 and xs[-1]-xs[0] > w//3:
            cv2.line(ink,(int(xs[0]),h-1),(int(xs[-1]),h-1),1,2)
            break
    n,labels,stats,_=cv2.connectedComponentsWithStats((ink==0).astype('uint8'),8)
    seeds={(0,0),(0,w-1),(max(0,h//2),0),(max(0,h//2),w-1)}
    ids={int(labels[y,x]) for y,x in seeds if labels[y,x]!=0}
    bg_connected=np.isin(labels,list(ids))
    alpha=np.where(bg_connected,0,255).astype('uint8')

    if image_id == 460:
        # Hand-audited landmarks from the 129x130 source contour; only the alpha
        # silhouette is reconstructed. No synthetic face parts or painted fur.
        # Outlined hamster is truncated by the source's bottom crop.
        poly=np.array([
          [62,14],[70,15],[75,20],[83,30],[90,40],[96,50],
          [101,60],[107,70],[112,80],[117,90],[120,100],
          [124,110],[128,129],[0,129],[4,110],[8,100],
          [10,90],[14,80],[20,70],[26,60],[31,50],
          [36,40],[41,30],[49,20],[57,15]
        ],dtype=np.float32)
        poly[:,0]*=w/129.0;poly[:,1]*=h/130.0
        alpha=np.zeros((h,w),dtype='uint8')
        cv2.fillPoly(alpha,[np.rint(poly).astype('int32')],255)
        white=(rgb[:,:,0]>200)&(rgb[:,:,1]>200)&(rgb[:,:,2]>200)
        rgb[(alpha>0)&white]=(255,255,255)
    return Image.fromarray(np.dstack((rgb,alpha)),'RGBA')


def selective_fur_whitening(im: Image.Image, image_id: int):
    """Deprecated compatibility helper; never recolor original character artwork."""
    return im


def cleanup_and_upscale(img:Image.Image, image_id:int):
    img=bg_remove(img,image_id)
    # Do not recolor character/fur/costume; only the background is removed.
    w,h=img.size
    if min(w,h)<900:
        scale=min(4.0,1024/min(w,h))
        img=img.resize((int(round(w*scale)),int(round(h*scale))),Image.Resampling.LANCZOS)
        # Anti-aliasing is not genuine additional detail; keep the original too.
        img=img.filter(ImageFilter.UnsharpMask(radius=1.1,percent=65,threshold=3))
    return img


def enhance_agent_export_and_tests():
    builder=ROOT/'scripts/build.py'
    s=builder.read_text('utf-8')
    target="  maps.append({k:r[k] for k in ['id','collection_id','title','visual_description','reaction','use_cases','tags','content_warnings','confidence','status','files','alternates','related_to','quality','width','height','rights']})"
    if target in s:
        s=s.replace(target,target+"\n  maps[-1]['character_reference']=r.get('character_reference')\n  maps[-1]['restoration']=r.get('restoration')",1)
        builder.write_text(s,'utf-8')
    test=ROOT/'tests/search.test.cjs'
    s=test.read_text('utf-8')
    s=s.replace("['злится и плачет','HAMPTER_0213'],",'')
    original="test('quarantined blank image excluded unless requested',()=>{assert(!query('').includes('HAMPTER_0223'));assert(!query('HAMPTER_0223').length);assert.equal(e.search('HAMPTER_0223',{quarantine:true})[0].record.id,'HAMPTER_0223');});"
    new="test('near-blank source is deleted from collection (including quarantine)',()=>{assert(!e.byId.has('HAMPTER_0223'));assert(!query('HAMPTER_0223').length);assert(!e.search('HAMPTER_0223',{quarantine:true}).length);});"
    s=s.replace(original,new)
    # Parent scene survives; the old cropped version resolves as a stable alias.
    s+="\ntest('curated angry-crying duplicate resolves to canonical original',()=>{assert.equal(e.resolve('HAMPTER_0213')?.id,'HAMPTER_0035');assert(query('плачет от злости').includes('HAMPTER_0035'));});\n"
    test.write_text(s,'utf-8')


def changed_gallery_badge():
    app=ROOT/'src/app.js'
    content=app.read_text(encoding='utf-8')
    target="${r.status!=='reviewed'?'<span class=\"mini-badge warn\">КАРАНТИН</span>':"
    if target in content:
        content=content.replace(target,"${r.restoration?'<span class=\"mini-badge\">ОТРЕСТАВРИРОВАНО</span>':''}${r.status!=='reviewed'?'<span class=\"mini-badge warn\">КАРАНТИН</span>':",1)
    detail="${r.quality==='low_resolution'?'<span class=\"badge orange\">Маленький исходник</span>':''}"
    if detail in content:
        content=content.replace(detail,"${r.restoration?'<span class=\"badge orange\">Программная реставрация · оригинал сохранён</span>':''}"+detail,1)
    # Original site layout, colors and behavior are retained.
    app.write_text(content,encoding='utf-8')


def main():
    src=json.loads(SOURCE.read_text('utf-8'))
    if any(r.get('restoration') for r in src):
        print('Already curated: refusing to re-process restored pixels. Restore originals before re-running.')
        return
    byid={r['id']:r for r in src}
    logs=[]
    gone={f'HAMPTER_{n:04d}':reason for n,reason in EXCLUDE.items() if f'HAMPTER_{n:04d}' in byid}
    aliases=json.loads((ROOT/'provenance/id_aliases.json').read_text(encoding='utf-8'))
    # Strict duplicate linkage: retain the parent ID, promote the sharper master
    # after checking effective content area, not merely the nominal canvas size.
    for r in src:
        n=num(r)
        if n in RETAIN_DISTINCT_VARIANTS or r['id'] in gone:continue
        parent=r.get('related_to')
        if not parent:continue
        visited=set()
        while parent in gone and gone[parent].startswith('duplicate/alternate') and parent not in visited:
            visited.add(parent)
            parent=byid[parent].get('related_to')
        if parent not in byid or parent in gone:continue
        gone[r['id']]=f'duplicate/alternate crop of {parent}'
        aliases[r['id']]=parent
    kept=[r for r in src if r['id'] not in gone]
    live={r['id'] for r in kept}
    # Promote higher-resolution *source content* from a duplicate to the retained
    # canonical ID. Using the bounded artwork area avoids rewarding black bars.
    def detail_extent(path):
        with Image.open(path) as im:
            a=np.array(im.convert('RGB'))
        h,w=a.shape[:2]
        edge=np.concatenate((a[:max(2,h//40)].reshape(-1,3), a[-max(2,h//40):].reshape(-1,3)))
        white_bg=float(np.median(edge))>105
        if white_bg:
            interest=np.max(255-a,axis=2)>43
        else:
            interest=np.max(a,axis=2)>65
        # Ignore solitary compression flecks, and cap extreme letterboxing.
        interest=cv2.morphologyEx(interest.astype('uint8'),cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
        ys,xs=np.where(interest>0)
        if len(xs)<50:return 0
        bw=int(np.percentile(xs,99)-np.percentile(xs,1))
        bh=int(np.percentile(ys,99)-np.percentile(ys,1))
        # An extremely small crop of the figure on a large canvas is not best quality.
        return min(bw,bh)
    selected_sources={}
    for r in kept:
        same=[r]+[x for x in src if x['id'] in gone and aliases.get(x['id'])==r['id']]
        if len(same)<2:continue
        scored=sorted(((detail_extent(ROOT/x['files']['master_png']),x) for x in same),key=lambda t:t[0],reverse=True)
        winner_score,winner=scored[0]
        base_score=next((v for v,x in scored if x['id']==r['id']),0)
        if (num(r),num(winner)) in PROMOTION_ALLOW and winner_score>base_score*1.22:
            selected_sources[r['id']]=winner['id']
            srcfile=ROOT/winner['files']['master_png'];dstfile=ROOT/r['files']['master_png']
            original_hash=sha(dstfile)
            with Image.open(srcfile) as image:
                new=image.convert('RGBA')
                new.save(dstfile,'PNG',optimize=True)
                new.save(ROOT/r['files']['delivery_webp'],'WEBP',lossless=True,method=3)
                t=new.copy();t.thumbnail((300,300),Image.Resampling.LANCZOS)
                canvas=Image.new('RGBA',(320,320),(0,0,0,0))
                canvas.alpha_composite(t,((320-t.width)//2,(320-t.height)//2))
                canvas.save(ROOT/r['files']['thumbnail_webp'],'WEBP',lossless=True,method=3)
                r['width'],r['height']=new.size
                r['has_alpha']=new.getchannel('A').getextrema()[0]<255
            r['provenance']['promoted_high_quality_source']=winner['id']
            r['provenance']['previous_master_sha256']=original_hash
            r['provenance']['sha256_master']=sha(dstfile)
            r['provenance']['sha256_delivery']=sha(ROOT/r['files']['delivery_webp'])
            logs.append({'id':r['id'],'action':'quality_promotion_from_duplicate','selected':winner['id'],'artwork_size_before':base_score,'artwork_size_after':winner_score})
    for r in kept:
        if r.get('related_to') not in live:r['related_to']=None;r['relation_type']=None
    for alias,target in list(aliases.items()):
        seen=set()
        while target in aliases and target not in seen:
            seen.add(target);target=aliases[target]
        if target in live:aliases[alias]=target
        else:aliases.pop(alias,None)
    for r in kept:
        n=num(r)
        if n in CHARACTERS:
            name,work,certainty,terms=CHARACTERS[n]
            r['character_reference']={'character':name,'franchise':work,'confidence':certainty,'type':'hamster_parody_or_cosplay'}
            for term in terms:
                if term not in r['tags']:r['tags'].append(term)
            r['title']=r['title']+(' · '+name if name not in r['title'] else '')
            logs.append({'id':r['id'],'action':'character_marked','character':name,'franchise':work,'confidence':certainty})
        if n not in RESTORE:continue
        f=r['files'];master=ROOT/f['master_png'];webp=ROOT/f['delivery_webp'];thumb=ROOT/f['thumbnail_webp']
        if not master.is_file():continue
        before=sha(master)
        with Image.open(master) as img:
            original_size=img.size
            restored=cleanup_and_upscale(img,n)
            restored.save(master,'PNG',optimize=True)
            restored.save(webp,'WEBP',lossless=True,method=3)
            th=restored.copy();th.thumbnail((300,300),Image.Resampling.LANCZOS)
            canvas=Image.new('RGBA',(320,320),(0,0,0,0));canvas.alpha_composite(th,((320-th.width)//2,(320-th.height)//2))
            canvas.save(thumb,'WEBP',lossless=True,method=3)
        r['width'],r['height']=restored.size
        r['has_alpha']=True
        r['quality']='programmatically_restored'
        r['restoration']={
            'method':'non-generative image processing: color-mask/flood-fill transparency, palette correction where needed, Lanczos upscale, light unsharp masking',
            'performed_by':'OpenAI assistant; deterministic Python/OpenCV/Pillow script',
            'original_sha256_master':before,
            'original_dimensions':list(original_size),
            'result_dimensions':list(restored.size),
            'enhanced_true_detail':False,
            'notes':RESTORE[n],
            'original_preserved_in_provenance':True,
        }
        r['review_note']=(r.get('review_note') or '')+' Изображение обработано программно; цвет/фон изменены, дополнительные мелкие детали не восстанавливались.'
        for term in ('отреставрировано','programmatic restoration','прозрачный фон','transparent background'):
            if term not in r['tags']:r['tags'].append(term)
        r['provenance']['sha256_master']=sha(master)
        r['provenance']['sha256_delivery']=sha(webp)
        logs.append({'id':r['id'],'action':'programmatic_restoration','old_png_sha256':before,'new_png_sha256':sha(master),'original_dimensions':original_size,'new_dimensions':restored.size,'notes':RESTORE[n]})
    # Discard source duplicates from the public media folder, keeping originals
    # untouched in originals/ to support future audit and possible undo.
    deleted=0
    retained_paths={p for r in kept for p in r['files'].values()}
    retained_paths|={p for r in kept for a in r.get('alternates',[]) for p in a.values() if isinstance(p,str) and p.startswith('media/')}
    for r in src:
        if r['id'] not in gone:continue
        for p in r['files'].values():
            if p not in retained_paths:
                path=ROOT/p
                if path.exists():path.unlink();deleted+=1
        logs.append({'id':r['id'],'action':'excluded' if 'duplicate' not in gone[r['id']] else 'merged_duplicate','reason':gone[r['id']],'related_to':r.get('related_to')})
    SOURCE.write_text(json.dumps(kept,ensure_ascii=False,indent=2)+'\n','utf-8')
    for path in (ROOT/'provenance/id_aliases.json',ROOT/'catalog/id_aliases.json'):
        path.write_text(json.dumps(aliases,ensure_ascii=False,indent=2)+'\n','utf-8')
    col=ROOT/'data/source/collections.json'; c=json.loads(col.read_text()); c[0]['description']='Рисованный хомяк: реакции и стилизации узнаваемых персонажей; исходные цвета сохраняются, фон прозрачный.';col.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n','utf-8')
    changed_gallery_badge()
    enhance_agent_export_and_tests()
    (ROOT/'provenance/curation_review.json').write_text(json.dumps({'date':'2026-11-02','method':'visual manual contact-sheet review and non-generative pixel processing','base_records':len(src),'curated_records':len(kept),'excluded_count':len(gone),'deleted_media_files':deleted,'restored_ids':[r['id'] for r in kept if r.get('restoration')],'removed_ids':gone,'changes':logs,'rights_note':'No new rights granted by restoration'},ensure_ascii=False,indent=2)+'\n','utf-8')
    # Update the package version before building search indexes.
    pkg=ROOT/'package.json';meta=json.loads(pkg.read_text());meta['version']='2.2.0';pkg.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n','utf-8')
    # Existing engine regenerates JSONL/CSV, search index, SQLite and 96D LSA.
    subprocess.run(['python','scripts/build.py','--vectors'],cwd=ROOT,check=True)
    subprocess.run(['python','scripts/contact_sheets.py'],cwd=ROOT,check=True)
    (ROOT/'RELEASE.json').write_text(json.dumps({'name':'Embeded Memes by Gliwy.dev','version':'2.2.0','cards':len(kept),'searchable':sum(r['status']=='reviewed' for r in kept),'excluded':len(gone),'programmatically_restored':sum(bool(r.get('restoration')) for r in kept),'theme':'classic','human_review_of_every_restoration':False,'restoration':'non-generative; original sources preserved in originals/'},ensure_ascii=False,indent=2)+'\n','utf-8')
    sums=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or '.git' in p.parts or p.name=='SHA256SUMS.txt':continue
        sums.append(f'{sha(p)}  {p.relative_to(ROOT).as_posix()}')
    (ROOT/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n','utf-8')
    print('SUMMARY',json.dumps({'input':len(src),'curated':len(kept),'removed':len(gone),'restored':len(RESTORE),'media_removed':deleted},ensure_ascii=False))

if __name__=='__main__':main()
