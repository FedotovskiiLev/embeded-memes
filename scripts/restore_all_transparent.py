#!/usr/bin/env python3
"""v3.2.0: derive lossless transparent production assets without recoloring art.

Maintains 374 stable IDs, all v3 descriptions, browser design, and 15 previously
restored transparent-color assets. Originals remain untouched under originals/.
"""
from __future__ import annotations
import hashlib, json, os, tempfile
from pathlib import Path
from PIL import Image
from asset_mask import restore_alpha

ROOT=Path(__file__).resolve().parents[1]
VERSION='3.2.0'

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def write_image(im:Image.Image,path:Path,kind:str)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.temp-',suffix='.tmp')
    os.close(fd)
    try:
        if kind=='PNG':im.save(tmp,format='PNG',compress_level=3)
        elif kind=='WEBP':im.save(tmp,format='WEBP',lossless=True,method=0)
        else:raise ValueError(kind)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def main()->None:
    src=ROOT/'data/source/memes.json'
    records=json.loads(src.read_text(encoding='utf-8'))
    assert len(records)==374, 'Expected the 374-card reviewed v3 collection'
    assert len({r['id'] for r in records})==len(records)
    assert all(r.get('status')=='reviewed' for r in records)
    if all(r.get('has_alpha') and r.get('restoration') for r in records):
        print('Already curated: 374 transparent production assets present; no changes needed.',flush=True)
        return
    if (ROOT/'data/source/annotations.json').exists():
        annotations=json.loads((ROOT/'data/source/annotations.json').read_text(encoding='utf-8'))
        assert len(annotations)==374, 'Do not drop individual emotional annotations'
    changed=[];kept=[]
    for i,r in enumerate(records,1):
        id_=r['id'];n=int(id_.split('_')[-1]);f=r['files']
        master=ROOT/f['master_png'];webp=ROOT/f['delivery_webp'];thumb=ROOT/f['thumbnail_webp']
        if r.get('has_alpha') and r.get('restoration'):
            # Preserve the 15 individually approved color-faithful cutouts exactly.
            kept.append(id_)
            continue
        before=sha(master)
        with Image.open(master) as image:
            orig=image.convert('RGBA');old_size=list(orig.size)
            restored=restore_alpha(orig,n)
        assert restored.getchannel('A').getextrema()==(0,255),f'{id_}: alpha should have empty background and solid object'
        # Lanczos is resizing only, not AI upscaling or invented texture.
        if min(restored.size)<900:
            factor=min(4.,1024/min(restored.size))
            restored=restored.resize((round(restored.width*factor),round(restored.height*factor)),Image.Resampling.LANCZOS)
        write_image(restored,master,'PNG')
        write_image(restored,webp,'WEBP')
        t=restored.copy();t.thumbnail((300,300),Image.Resampling.LANCZOS)
        board=Image.new('RGBA',(320,320),(0,0,0,0))
        board.alpha_composite(t,((320-t.width)//2,(320-t.height)//2))
        write_image(board,thumb,'WEBP')
        newsha=sha(master);websha=sha(webp)
        r['width'],r['height']=restored.size
        r['has_alpha']=True
        r['quality']='programmatically_restored'
        r['restoration']={
            'version':VERSION,
            'method':'original RGB/alpha-preserving contour matting, fur silhouette fill and selective guided masks',
            'performed_by':'OpenAI assistant; deterministic Pillow/OpenCV/SciPy code',
            'original_sha256_master':before,
            'result_sha256_master':newsha,
            'original_dimensions':old_size,
            'result_dimensions':list(restored.size),
            'palette_policy':'preserve_original_character_colors',
            'background_policy':'outside subject transparent; hamster, costume and props opaque',
            'enhanced_true_detail':False,
            'human_reviewed_individually':False,
            'manual_mask_exception':n in (71,94,104,431),
            'notes':'Только внешний фон удалён. Исходные цвета персонажа, костюма и предметов сохранены.'
        }
        r['provenance']['sha256_master']=newsha
        r['provenance']['sha256_delivery']=websha
        changed.append({'id':id_,'master':f['master_png'],'original_sha256':before,'result_sha256':newsha,'original_size':old_size,'result_size':list(restored.size),'manual_mask_exception':n in (71,94,104,431)})
        if i%25==0:print(f'Processed {i}/{len(records)} (new {len(changed)}, preserved {len(kept)})',flush=True)
    assert len(changed)==359 and len(kept)==15,(len(changed),len(kept))
    assert all(r.get('has_alpha') for r in records)
    src.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    package=ROOT/'package.json';pkg=json.loads(package.read_text(encoding='utf-8'));pkg['version']=VERSION
    package.write_text(json.dumps(pkg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'provenance/mass_transparent_restoration.json').write_text(json.dumps({
        'version':VERSION,'total_records':374,'newly_restored':len(changed),'preserved_previous':len(kept),
        'color_policy':'all source RGB kept; never whiten colored costumes',
        'human_review_of_every_cutout':False,'manual_mask_exceptions':['HAMPTER_0071','HAMPTER_0094','HAMPTER_0104','HAMPTER_0431'],
        'changes':changed,'preserved_previous_ids':kept
    },ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    release=ROOT/'RELEASE.json';metadata=json.loads(release.read_text(encoding='utf-8'))
    metadata.update({'version':VERSION,'cards':374,'searchable':374,'newly_restored':len(changed),'restored_total':374,'theme':'classic','individual_annotations':374,'color_policy':'original_character_colors_preserved','transparent_background':True,'human_review_of_every_cutout':False})
    release.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('RESTORATION_COMPLETE',json.dumps({'total':374,'newly_restored':len(changed),'kept_existing':len(kept)},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
