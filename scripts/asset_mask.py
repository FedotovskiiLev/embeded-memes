"""Deterministic alpha masks for cartoon meme cutouts. Never recolors source artwork.

Selectively reconstructs the white opaque hamster silhouette (including open-bottom
outlines). Special scene masks avoid interpreting caption/energy/decor as background.
Requires NumPy, SciPy, Pillow and OpenCV; no generative model or network access.
"""
from __future__ import annotations
import numpy as np
import cv2
from scipy.ndimage import binary_closing, label
from PIL import Image


def _polygon(shape, points):
    h,w=shape[:2]
    p=np.array([[round(x*w/320),round(y*h/320)] for x,y in points],np.int32)
    m=np.zeros((h,w),np.uint8)
    cv2.fillPoly(m,[p],255)
    return m


def _outlined_scene(im: Image.Image, image_id:int)->Image.Image:
    src=np.asarray(im.convert('RGBA')).copy()
    rgb=src[:,:,:3]
    if image_id==71:
        # Giant YARG caption above pirate hat; letter ink and costume kept.
        body=_polygon(src.shape,[(157,90),(193,94),(218,128),(254,208),(308,320),(27,320),(56,225),(87,164),(122,110)])
    elif image_id==94:
        # Pointed hat, open mouth, arms and lightning bolts remain foreground.
        body=_polygon(src.shape,[(187,2),(218,88),(269,155),(282,251),(289,320),(22,320),(34,253),(64,174),(113,102)])
    else:raise ValueError(image_id)
    # Preserve original dark line art outside the body (lettering and lightning).
    ink=(np.min(rgb,axis=2)<140).astype('uint8')
    line=cv2.dilate(ink,np.ones((2,2),np.uint8),iterations=1)
    alpha=np.maximum(body,np.uint8(line*255))
    src[...,3]=alpha
    return Image.fromarray(src,'RGBA')


def _aura(im: Image.Image)->Image.Image:
    """White hamster with green costume hair and yellow power aura; transparent gaps."""
    src=np.asarray(im.convert('RGBA')).copy()
    rgb=src[:,:,:3]
    body=_polygon(src.shape,[(131,94),(175,90),(222,138),(258,213),(307,320),(29,320),(58,223),(90,160)])
    color=rgb.astype('int16')
    chrom=color.max(axis=2)-color.min(axis=2)
    saturated=(chrom>=75)&(color.max(axis=2)>=130)&(color.min(axis=2)<210)
    saturated=cv2.morphologyEx(saturated.astype('uint8'),cv2.MORPH_OPEN,np.ones((2,2),np.uint8))>0
    black=cv2.dilate((rgb.max(axis=2)<110).astype('uint8'),np.ones((2,2),np.uint8),iterations=1)>0
    src[...,3]=np.where((body>0)|saturated|black,255,0).astype('uint8')
    return Image.fromarray(src,'RGBA')


def _bubble_bath(im: Image.Image)->Image.Image:
    """Guided grabcut: preserve white hamster, rubber duck, colored soap and showerhead."""
    src=np.asarray(im.convert('RGBA')).copy()
    rgb=src[:,:,:3]
    h,w=rgb.shape[:2]
    mask=np.full((h,w),cv2.GC_PR_BGD,np.uint8)
    border=max(4,int(min(h,w)*.017))
    mask[:border,:]=cv2.GC_BGD
    mask[:,:border]=cv2.GC_BGD
    mask[:,-border:]=cv2.GC_BGD
    mask[-border:,:]=cv2.GC_PR_BGD
    body=_polygon(src.shape,[(144,92),(177,116),(207,165),(247,235),(284,320),(32,320),(63,244),(94,170),(119,115)])
    mask[body>0]=cv2.GC_FGD
    shower=_polygon(src.shape,[(218,48),(247,27),(267,8),(298,0),(320,0),(320,48),(305,54),(286,72),(261,96),(224,80)])
    soap=_polygon(src.shape,[(263,178),(279,165),(307,181),(315,207),(296,226),(260,208)])
    mask[(shower>0)|(soap>0)]=cv2.GC_FGD
    a=rgb.astype('int16')
    pink=(a[:,:,0]-a[:,:,1]>14)&(a[:,:,0]-a[:,:,2]>5)&(a[:,:,0]>115)&(a[:,:,1]>80)
    pink=cv2.dilate(pink.astype('uint8'),np.ones((3,3),np.uint8),iterations=1)
    mask[(pink>0)&(mask==cv2.GC_PR_BGD)]=cv2.GC_PR_FGD
    bgd=np.zeros((1,65),np.float64)
    fgd=np.zeros((1,65),np.float64)
    cv2.grabCut(rgb,mask,None,bgd,fgd,6,cv2.GC_INIT_WITH_MASK)
    src[...,3]=np.where((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD),255,0).astype('uint8')
    return Image.fromarray(src,'RGBA')


def _background_color(rgb: np.ndarray):
    h,w=rgb.shape[:2]
    k=max(4,min(h,w)//30)
    corners=np.array([np.median(rgb[:k,:k],axis=(0,1)),np.median(rgb[:k,-k:],axis=(0,1)),
                      np.median(rgb[-k:,:k],axis=(0,1)),np.median(rgb[-k:,-k:],axis=(0,1))])
    scored=[]
    for i in range(4):
        matches=int(np.sum(np.max(np.abs(corners-corners[i]),axis=1)<28))
        scored.append((matches,float(corners[i].mean()),i))
    return corners[max(scored)[2]]


def restore_alpha(im: Image.Image,image_id:int)->Image.Image:
    if image_id in (71,94):return _outlined_scene(im,image_id)
    if image_id==104:return _aura(im)
    if image_id==431:return _bubble_bath(im)
    src=np.asarray(im.convert('RGBA')).copy()
    rgb=src[:,:,:3]
    h,w=rgb.shape[:2]
    bg=_background_color(rgb)
    distance=np.max(np.abs(rgb.astype('float32')-bg[None,None,:]),axis=2)
    tol=29 if bg.mean()>100 else 33
    mask=(distance>tol).astype('uint8')
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
    n,regions,stats,_=cv2.connectedComponentsWithStats((mask==0).astype('uint8'),8)
    seeds=[]
    for y,x in ((0,0),(0,w-1),(h-1,0),(h-1,w-1),(h//2,0),(h//2,w-1)):
        if np.max(np.abs(rgb[y,x].astype(float)-bg))<tol*1.25:seeds.append(int(regions[y,x]))
    bg_regions={k for k in seeds if k>0}
    if not bg_regions:
        border=np.r_[regions[0],regions[-1],regions[:,0],regions[:,-1]]
        hist=np.bincount(border[border>0])
        if len(hist)>1:bg_regions={int(hist.argmax())}
    alpha=np.where(np.isin(regions,list(bg_regions)),0,255).astype('uint8')
    # Many hamsters are white on white, with unfinished silhouettes at the
    # bottom edge. Flood-fill would mistake their *interior* for background.
    if bg.mean()>150:
        ink=rgb.max(axis=2)<180
        valid=binary_closing(ink.sum(axis=1)>=2,np.ones(max(5,int(h*.025)),bool))
        groups,count=label(valid)
        sizes=np.bincount(groups)[1:]
        if len(sizes):
            main=int(np.argmax(sizes))+1
            yr=np.flatnonzero(groups==main)
            start=int(yr[0]) if len(yr) else h
            end=int(yr[-1]) if len(yr) else 0
            if end-start>h*.18:
                left=np.full(h,w-1,np.int32)
                right=np.zeros(h,np.int32)
                for y in range(start,min(h,end+1)):
                    xs=np.flatnonzero(ink[y])
                    if len(xs):left[y]=int(xs[0]);right[y]=int(xs[-1])
                lx=np.minimum.accumulate(left[start:])
                rx=np.maximum.accumulate(right[start:])
                silhouette=np.zeros((h,w),bool)
                for iy,y in enumerate(range(start,h)):
                    l=int(lx[iy]);r=int(rx[iy])
                    if l<r and r-l>=w*.03:silhouette[y,l:r+1]=True
                missing=silhouette&(rgb.min(axis=2)>=211)&(alpha<255)
                if missing.sum()/max(1,silhouette.sum())>.075:
                    alpha[missing]=255
    if alpha.min()==255:
        # Fallback for non-white scenes lacking a separable border.
        m=np.zeros((h,w),np.uint8);k=max(3,min(h,w)//65)
        bgd=np.zeros((1,65),np.float64);fgd=np.zeros((1,65),np.float64)
        cv2.grabCut(rgb,m,(k,k,w-2*k,h-2*k),bgd,fgd,4,cv2.GC_INIT_WITH_RECT)
        alpha=np.where((m==0)|(m==2),0,255).astype('uint8')
    src[...,3]=np.minimum(src[...,3],alpha) if src[...,3].min()<255 else alpha
    return Image.fromarray(src,'RGBA')
