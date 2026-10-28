#!/usr/bin/env python3
"""Original printable Titanic YouTube cover art; no unauthorized film imagery.
All PNG/JPG images are original vector-like Pillow illustrations.
"""
import pathlib,math,json
from PIL import Image,ImageDraw,ImageFont,ImageFilter
P=pathlib.Path(__file__).resolve().parent/"publishing_art"
P.mkdir(parents=True,exist_ok=True)
GOLD=(245,204,121);WHITE=(254,251,244);NAVY=(5,19,33);ICE=(172,225,243)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SERIF="/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
def ft(n,serif=False):return ImageFont.truetype(SERIF if serif else FONT,n)
def text(d,xy,t,sz,c=WHITE,serif=False,stroke=0):
    d.text(xy,t,font=ft(sz,serif),fill=c,stroke_width=stroke,stroke_fill=(0,0,0))
def paint(width,height):
    im=Image.new("RGB",(width,height))
    d=ImageDraw.Draw(im)
    for y in range(height):
        u=y/height;d.line((0,y,width,y),fill=(int(6+2*u),int(18+9*u),int(33+17*u)))
    for j in range(85):
        x=100+(j*733)%max(width-130,150)
        y=50+(j*119)%max(height//2,100)
        if (j%3):d.ellipse((x,y,x+2,y+2),fill=(120,149,166))
    for j in range(16):
        yy=int(height*.77+j*height*.016)
        points=[(x,int(yy+3*math.sin(x/35+j))) for x in range(0,width,12)]
        d.line(points,fill=(23+j*2,67+j*2,99+j*2),width=2)
    return im,d
def ship(d,w,h,x,y,s):
    def px(v):return x+v*s
    def py(v):return y+v*s
    d.polygon([(px(0),py(0)),(px(1300),py(-14)),(px(1190),py(186)),(px(150),py(186))],fill=(8,21,28),outline=(222,209,170))
    d.polygon([(px(130),py(-55)),(px(1175),py(-55)),(px(1132),py(0)),(px(162),py(0))],fill=(185,172,143))
    d.rectangle((px(255),py(-115),px(1056),py(-56)),fill=(204,187,148))
    for k in range(4):
        xx=330+k*186
        d.polygon([(px(xx),py(-307)),(px(xx+82),py(-307)),(px(xx+92),py(-115)),(px(xx-8),py(-115))],fill=(198,135,79),outline=GOLD)
        d.rectangle((px(xx),py(-307),px(xx+82),py(-275)),fill=(11,15,20))
    for j in range(16):
        xx=202+j*59
        d.ellipse((px(xx),py(83),px(xx+8),py(91)),fill=GOLD)
def iceberg(d,w,h):
    x=w*.78;y=h*.77
    d.polygon([(x-160,y+15),(x-70,y-175),(x+20,y-73),(x+92,y-144),(x+190,y+19)],fill=ICE,outline=(229,246,252))
    d.polygon([(x-115,y+15),(x-62,y-100),(x+40,y-31),(x+120,y-80),(x+178,y+10)],fill=(68,139,168))
def main():
    w,h=1280,720
    im,d=paint(w,h);ship(d,w,h,-30,522,.72);iceberg(d,w,h)
    overlay=Image.new("RGBA",(w,h))
    q=ImageDraw.Draw(overlay)
    for y in range(280):
        alpha=int(209*(1-y/300))
        q.line((0,y,w,y),fill=(3,14,27,max(0,alpha)))
    im=Image.alpha_composite(im.convert("RGBA"),overlay).convert("RGB");d=ImageDraw.Draw(im)
    text(d,(65,50),"TITANIC'S",84,WHITE,True,3)
    text(d,(65,151),"FINAL NIGHT",91,GOLD,True,3)
    text(d,(69,274),"THE WARNINGS • THE EVIDENCE • THE WRECK",26,WHITE)
    d.rectangle((69,324,340,332),fill=GOLD)
    text(d,(40,669),"FACTS UNCOVERED  |  STORIES & EVIDENCE",18,WHITE)
    im.save(P/"titanic_documentary_thumbnail.jpg",quality=95,optimize=True)
    for n,title,big in [(1,"WHY ONLY 20 BOATS?","1,178 PLACES"),(2,"THE WRECK IS CHANGING","2024 DISCOVERIES")]:
        iw,ih=1080,1920
        im,d=paint(iw,ih)
        if n==1:
            for j in range(20):
                x=110+(j%5)*184;y=770+(j//5)*167
                d.polygon([(x,y),(x+127,y),(x+103,y+37),(x+24,y+37)],fill=(39,80,100),outline=GOLD)
        else:
            d.polygon([(150,1230),(820,1170),(755,1495),(310,1511)],fill=(65,96,108),outline=GOLD)
            d.line((259,1241,470,1222),fill=(227,125,109),width=18)
        text(d,(74,204),"FACTS UNCOVERED",44,WHITE)
        text(d,(72,340),title,54,GOLD,True,2)
        text(d,(70,1510),big,66,WHITE,True,3)
        text(d,(74,1640),"TITANIC • EVIDENCE-BASED HISTORY",30,GOLD)
        d.rectangle((72,1713,396,1722),fill=GOLD)
        im.save(P/f"titanic_short_0{n}_cover.jpg",quality=95,optimize=True)
    (P/"ARTWORK_RIGHTS.json").write_text(json.dumps({"creator":"Facts Uncovered original editorial diagrams",
      "archival_photos_in_cover_art":False,"third_party_film_frames":False,
      "all_covers_original":True,"publication_quality_full_viewing":"NOT REVIEWED",
      "intended_use":"YouTube thumbnail and original Shorts cover compositions"},indent=2))
    print("THREE_ORIGINAL_TITANIC_YOUTUBE_COVERS_CREATED",flush=True)
if __name__=="__main__":main()
