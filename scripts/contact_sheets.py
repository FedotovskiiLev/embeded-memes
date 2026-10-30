#!/usr/bin/env python3
"""Rebuild labeled visual overview using current titles (Pillow required)."""
from pathlib import Path
import json,math,shutil
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
def font(n):
 for name in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']:
  if Path(name).exists():return ImageFont.truetype(name,n)
 return ImageFont.load_default(size=n)
def main():
 records=json.loads((ROOT/'catalog/catalog.json').read_text())['records'];out=ROOT/'contact_sheets';out.mkdir(exist_ok=True)
 for p in out.glob('sheet-*.jpg'):p.unlink()
 W,H,COLS,ROWS=280,335,5,6;head=60;f=font(15);small=font(12);title=font(22)
 for page,start in enumerate(range(0,len(records),COLS*ROWS),1):
  subset=records[start:start+COLS*ROWS];im=Image.new('RGB',(W*COLS,H*ROWS+head),'white');d=ImageDraw.Draw(im);d.text((18,15),f'Embeded Memes by Gliwy.dev  /  {page:02d}',font=title,fill='#333333')
  for i,r in enumerate(subset):
   x=(i%COLS)*W;y=(i//COLS)*H+head
   d.rectangle((x,y,x+W-1,y+H-1),outline='#dddddd')
   with Image.open(ROOT/r['files']['thumbnail_webp']) as a:
    a=a.convert('RGBA');a.thumbnail((256,256));bg=Image.new('RGBA',a.size,'white');bg.alpha_composite(a);im.paste(bg.convert('RGB'),(x+(W-a.width)//2,y+5))
   d.text((x+12,y+264),r['id'],font=small,fill='#777777');words=r['title'].split();lines=[];line=''
   for word in words:
    test=(line+' '+word).strip()
    if d.textlength(test,font=f)>W-24 and line:lines.append(line);line=word
    else:line=test
   if line:lines.append(line)
   for j,line in enumerate(lines[:2]):d.text((x+12,y+284+j*19),line[:45],font=f,fill='#252525')
   if r['status']!='reviewed':d.text((x+155,y+264),'QUARANTINE',font=small,fill='#9b531d')
  im.save(out/f'sheet-{page:02d}.jpg',quality=88,optimize=True)
 print(f'Wrote {math.ceil(len(records)/(COLS*ROWS))} contact sheets')
if __name__=='__main__':main()
