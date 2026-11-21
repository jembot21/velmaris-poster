"""Velmaris: a deterministic, procedurally painted travel lithograph."""
from pathlib import Path
import sys
import tempfile
import zipfile
import os

ROOT = Path(__file__).resolve().parent
_BOOTSTRAP = None
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    wheels = sorted((ROOT / 'vendor').glob('pillow-*.whl'))
    if not wheels:
        raise FileNotFoundError(
            'Pillow is not installed and no bundled pillow-*.whl was found in vendor/'
        ) from None
    wheel = wheels[0]
    _BOOTSTRAP = tempfile.TemporaryDirectory(prefix='velmaris-pillow-')
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(_BOOTSTRAP.name)
    sys.path.insert(0, _BOOTSTRAP.name)
    from PIL import Image, ImageDraw, ImageFont, ImageFilter

import math
import random

W = H = 1024
S = 2
rng = random.Random(17391)

def mix(a, b, t):
    return tuple(round(x + (y-x)*t) for x,y in zip(a,b))

def gradient(stops, y):
    for (ya,a),(yb,b) in zip(stops,stops[1:]):
        if y <= yb:
            return mix(a,b,max(0,min(1,(y-ya)/(yb-ya))))
    return stops[-1][1]

sky = [(0,(20,48,65)),(200,(46,77,88)),(350,(153,111,113)),(465,(224,155,116)),(558,(248,193,119)),(1024,(41,77,78))]
sea = [(516,(109,132,125)),(590,(56,105,111)),(760,(29,77,88)),(1024,(15,46,59))]
im = Image.new('RGB',(W,H))
pixels = im.load()
for y in range(H):
    base = gradient(sky if y < 523 else sea,y)
    for x in range(W):
        glow = (math.exp(-(((x-390)/240)**2+((y-496)/139)**2))*.30
                + math.exp(-(((x-390)/83)**2+((y-494)/76)**2))*.25) if y < 523 else 0
        c = mix(base,(255,211,144),glow)
        if y >= 523:
            # Broad currents under the small engraved wave marks.
            swell = math.sin(y*.105+math.sin(x*.008)*1.6)
            mottle = math.sin(x*.017+y*.021)*math.sin(x*.006-y*.037)
            c = mix(c, (156,163,139) if swell+mottle > 0 else (12,48,63),
                    abs(swell*.065+mottle*.10))
            reflection = math.exp(-((x-668)/(19+(y-523)*.14))**2-((y-693)/105)**2)
            c = mix(c,(232,173,99),reflection*.32)
        n = rng.uniform(-1.5,1.5)
        pixels[x,y] = tuple(max(0,min(255,round(v+n))) for v in c)
im = im.resize((W*S,H*S),Image.Resampling.BICUBIC)
d = ImageDraw.Draw(im)
def poly(p,c): d.polygon([(int(x*S),int(y*S)) for x,y in p],fill=c)
def line(p,c,w=1): d.line([(int(x*S),int(y*S)) for x,y in p],fill=c,width=max(1,int(w*S)))
def ellipse(box,c): d.ellipse(tuple(int(v*S) for v in box),fill=c)
def curve(points,steps=100):
    a,b,c,e=points
    return [((1-t)**3*a[0]+3*(1-t)**2*t*b[0]+3*(1-t)*t*t*c[0]+t**3*e[0],(1-t)**3*a[1]+3*(1-t)**2*t*b[1]+3*(1-t)*t*t*c[1]+t**3*e[1]) for t in [i/steps for i in range(steps+1)]]
# Translucent cloud veils have soft edges, beneath the fine printed wisps.
clouds=Image.new('RGBA',im.size); cd=ImageDraw.Draw(clouds)
for x,y,rx in [(160,287,125),(480,373,165),(865,432,145),(230,410,94)]:
    cd.ellipse(((x-rx)*S,(y-2)*S,(x+rx)*S,(y+3)*S),fill=(238,168,153,36))
clouds=clouds.filter(ImageFilter.GaussianBlur(5*S))
im=Image.alpha_composite(im.convert('RGBA'),clouds).convert('RGB'); d=ImageDraw.Draw(im)
# Wisps of rose-coloured cloud, printed in broken horizontal strokes.
for i in range(90):
    y=rng.uniform(260,487); x=rng.uniform(-150,1050)
    color=mix(gradient(sky,y),(236,170,139),rng.uniform(.08,.24))
    line([(x,y),(x+rng.uniform(35,210),y-rng.uniform(0,3))],color,rng.uniform(.5,2))
ellipse((347,451,433,537),(250,211,145))
ellipse((352,456,428,532),(255,220,154))
# Distant headlands hold the horizon.
poly([(0,510),(75,501),(121,504),(164,493),(206,503),(264,516),(310,525),(0,530)],(80,111,112))
poly([(828,520),(885,505),(922,508),(962,497),(1024,505),(1024,535)],(81,105,106))
line([(0,530),(1024,530)],(179,163,127),.7)
# Thousands of fine sea marks; sun glitter gets wider towards the viewer.
for i in range(11500):
    y=rng.uniform(532,1024); x=rng.uniform(0,1024)
    depth=(y-520)/504
    base=gradient(sea,y)
    lit=math.exp(-((x-(390+depth*20))/(24+depth*116))**2)
    if rng.random()<lit*.79:
        c=mix(base,(246,195,119),rng.uniform(.35,.95))
    else:
        c=mix(base,(156,178,163) if rng.random()<.54 else (12,52,67),rng.uniform(.10,.40))
    length=rng.uniform(1,8)*(0.5+depth*1.8)
    line([(x,y),(x+length,y)],c,rng.choice([.5,.5,1]))
# The brightest glitter is sampled around the reflection, not uniformly at sea.
for i in range(2800):
    y=rng.uniform(534,918); depth=(y-520)/504
    x=rng.gauss(390+depth*20,9+depth*62)
    strength=math.exp(-((x-390-depth*20)/(20+depth*85))**2)
    c=mix(gradient(sea,y),(255,222,158),rng.uniform(.4,.75)+strength*.22)
    line([(x,y),(x+rng.uniform(.6,6)*(1+depth),y)],c,rng.choice([.4,.6,.8]))
# Low tide: sinuous sandbars and reflective tidal pools.
poly([(0,735),(91,718),(198,735),(322,713),(450,736),(526,713),(592,722),(687,692),(780,712),(897,697),(1024,726),(1024,1024),(0,1024)],(87,102,96))
poly([(0,805),(140,769),(264,786),(376,754),(510,779),(668,747),(854,774),(1024,747),(1024,1024),(0,1024)],(135,125,104))
poly([(0,873),(111,836),(263,840),(384,811),(503,838),(667,794),(771,815),(1005,785),(1024,1024),(0,1024)],(163,138,108))
poly([(0,945),(188,875),(315,884),(471,855),(579,887),(767,836),(911,858),(1024,820),(1024,1024),(0,1024)],(180,146,110))
poly([(0,961),(176,906),(334,921),(492,884),(651,912),(826,872),(1024,893),(1024,949),(838,923),(650,955),(463,921),(318,962),(140,946),(0,1008)],(95,117,112))
# Glazed wet sediment: continuous rose/amber reflections and irregular dampness.
# Work at final resolution, before foreground objects, so the light stays on sand.
wet=im.resize((W,H),Image.Resampling.LANCZOS); wp=wet.load()
for y in range(724,H):
    for x in range(W):
        if wp[x,y] not in [(87,102,96),(135,125,104),(163,138,108),(180,146,110),(95,117,112)]:
            continue
        field=math.sin(x*.016+math.sin(y*.031)*2)+math.sin(y*.072+x*.005)
        damp=max(0,field)*.12
        c=mix(wp[x,y],(47,75,78),damp)
        sheen=math.exp(-((x-390-65*math.sin(y*.024))/260)**2)
        sheen*=.12+.19*(.5+.5*math.sin(y*.085+x*.009))
        c=mix(c,mix((178,124,124),(231,173,112),(y-724)/300),sheen)
        wp[x,y]=c
im=wet.resize((W*S,H*S),Image.Resampling.BICUBIC); d=ImageDraw.Draw(im)
# Thin, broken pools follow tidal contours; dark lips make their sheen readable.
for i in range(115):
    x=rng.uniform(-30,1040); y=rng.uniform(759,1024)
    length=rng.uniform(12,95); height=rng.uniform(1.2,4.5)*(y/850)
    points=[(x,y),(x+length*.22,y-height),(x+length*.7,y-height*.7),
            (x+length,y),(x+length*.65,y+height*.5),(x+length*.13,y+height*.6)]
    color=mix((75,105,109),(193,147,129),rng.uniform(.12,.65))
    poly(points,color)
    line([(x+length*.13,y+height*.6),(x+length*.65,y+height*.5)],(77,91,85),.5)
    line([(x+length*.22,y-height),(x+length*.65,y-height*.7)],mix(color,(235,183,132),.30),.5)
for i in range(5800):
    y=rng.uniform(739,1024); x=rng.uniform(0,1024)
    c=rng.choice([(183,155,117),(129,127,108),(195,161,119),(108,123,112)])
    line([(x,y),(x+rng.uniform(2,24),y-rng.uniform(0,.5))],c,.5)
# Reflected beacon, broken by shallow water.
for i in range(180):
    y=rng.uniform(714,976); spread=7+(y-710)*.15
    x=rng.gauss(670,spread)
    line([(x,y),(x+rng.uniform(2,17),y)],rng.choice([(208,166,104),(181,150,104),(221,173,100)]),.6)
# Island silhouette and stratified, hand-cut rock faces.
poly([(513,675),(541,620),(571,602),(613,591),(660,599),(706,585),(749,617),(775,661),(807,688),(743,710),(654,719),(562,704)],(37,64,65))
poly([(520,675),(547,626),(576,612),(614,606),(594,649),(568,659),(556,690)],(146,130,100))
poly([(576,612),(636,602),(662,616),(632,655),(594,649)],(177,147,104))
poly([(632,655),(662,616),(706,600),(727,632),(688,670),(667,702),(609,700)],(83,93,81))
poly([(727,632),(749,639),(769,675),(790,688),(724,701),(688,670)],(48,76,73))
poly([(541,620),(584,596),(627,590),(672,598),(710,586),(739,616),(690,631),(626,623),(573,634)],(89,105,79))
# Paint only existing rock colours, preserving the silhouette and face boundaries.
rock_colors={(37,64,65),(146,130,100),(177,147,104),(83,93,81),(48,76,73),(89,105,79)}
rock=im.load()
for y in range(585*S,720*S):
    for x in range(513*S,808*S):
        c=rock[x,y]
        if c not in rock_colors:
            continue
        xx,yy=x/S,y/S
        strata=math.sin(yy*.65+xx*.18)*math.sin(xx*.09-yy*.13)
        c=mix(c,(29,51,53) if strata<0 else (201,166,111),abs(strata)*.17)
        c=mix(c,(25,48,53),max(0,(xx-684)/124)*.22)
        pool=math.exp(-((xx-661)/67)**2-((yy-620)/38)**2)
        rock[x,y]=mix(c,(241,180,93),pool*.30)
for i in range(125):
    x=rng.uniform(550,751); y=rng.uniform(639,695)
    if 550+(y-640)*.15<x<749:
        line([(x,y),(x+rng.uniform(4,21),y-rng.uniform(1,6))],rng.choice([(65,82,75),(112,113,88),(162,135,96)]),.8)
# Causeway: a broad winding masonry ribbon tapering into the island.
left=curve([(-90,1040),(46,806),(405,870),(603,686)])
right=curve([(94,1040),(142,858),(454,879),(621,691)])
poly(left+right[::-1],(48,65,64))
upper=curve([(-58,1015),(75,791),(421,854),(606,680)])
poly(upper+right[::-1],(161,143,111))
line(upper,(214,179,125),3)
line(right,(66,78,72),4)
# Cross joints and irregular paving blocks follow the bend.
for i in range(4,100,3):
    a=upper[i]; b=right[i]
    line([a,b],(101,104,88),1.1)
    for fraction in [.28,.59,.81]:
        j=min(i+3,100)
        c=upper[j]; e=right[j]
        f=fraction+(.045 if i%2 else -.045)
        line([(a[0]*(1-f)+b[0]*f,a[1]*(1-f)+b[1]*f),(c[0]*(1-f)+e[0]*f,c[1]*(1-f)+e[1]*f)],(117,115,94),.8)
# Cottage, warm plaster and a weathered terracotta roof.
poly([(687,579),(744,582),(744,623),(687,617)],(211,176,121))
poly([(744,582),(763,571),(763,613),(744,623)],(137,126,96))
poly([(677,582),(709,554),(774,568),(744,589)],(77,67,60))
poly([(677,582),(709,554),(744,565),(716,590)],(142,83,59))
line([(684,580),(711,558),(766,570)],(195,120,73),2)
poly([(744,552),(752,554),(752,570),(744,568)],(139,119,94))
for x,y in [(697,594),(724,597)]:
    poly([(x-2,y-2),(x+10,y-2),(x+10,y+14),(x-2,y+14)],(87,80,65))
    poly([(x,y),(x+8,y),(x+8,y+11),(x,y+11)],(248,193,98))
    line([(x+4,y),(x+4,y+11)],(126,104,74),1)
poly([(750,591),(756,588),(756,602),(750,605)],(244,180,91))
# Warm reflected lantern light washes the plaster; its far corner stays cool.
for y in range(583,618):
    for x in range(688,744):
        if im.getpixel((x*S,y*S)) == (211,176,121):
            warmth=math.exp(-((x-689)/42)**2-((y-598)/30)**2)
            line([(x,y),(x+1,y)],mix((199,163,113),(255,207,130),warmth*.7),1)
# Tapered tower: each horizontal course is shaded across its circumference.
top,bottom=331,615
for y in range(top,bottom):
    t=(y-top)/(bottom-top); half=17+13*t
    red=int((y-335)//49)%2==1
    for xi in range(int(-half),int(half)+1):
        u=(xi+half)/(2*half)
        light=(math.cos((u-.20)*math.pi)*.5+.5)
        a,b=((105,52,46),(201,92,61)) if red else ((132,134,117),(246,217,165))
        c=mix(a,b,light)
        line([(654+xi,y),(654+xi+1,y)],c,1)
line([(625,614),(684,614)],(59,77,70),3)
poly([(643,586),(653,582),(653,614),(643,614)],(62,76,71))
for y in [377,477,568]:
    poly([(649,y),(655,y-1),(655,y+13),(649,y+14)],(48,71,72))
    line([(648,y+15),(657,y+14)],(240,202,146),1)
# Cornice, glass lantern and copper cap.
poly([(630,332),(678,332),(683,342),(626,342)],(53,76,72))
poly([(635,299),(674,299),(674,331),(635,331)],(247,191,96))
for x in range(636,674):
    c=mix((255,224,140),(220,145,70),abs(x-652)/24)
    line([(x,302),(x,329)],c,1)
ellipse((646,307,663,325),(255,238,173))
for x in [635,645,664,674]: line([(x,299),(x,333)],(51,72,68),2)
poly([(627,300),(654,275),(682,300)],(48,71,68))
poly([(630,298),(654,278),(654,298)],(117,115,85))
line([(654,275),(654,262)],(46,65,64),2)
ellipse((651,260,657,266),(67,75,63))
line([(625,335),(682,335)],(221,174,103),2)
line([(624,341),(624,323),(684,323),(684,341)],(44,66,63),1.4)
for x in range(626,685,8): line([(x,324),(x,340)],(53,71,66),1)
# Soft lamplight halo, kept below the grain so it belongs to the print.
halo=Image.new('RGBA',im.size)
hd=ImageDraw.Draw(halo)
hd.ellipse((620*S,282*S,690*S,350*S),fill=(255,194,85,48))
halo=halo.filter(ImageFilter.GaussianBlur(14*S))
im=Image.alpha_composite(im.convert('RGBA'),halo).convert('RGB'); d=ImageDraw.Draw(im)
# Beached rowboat, its reflection and shadow sit in the shallow pool.
ellipse((722,940,897,957),(71,90,85))
poly([(722,914),(757,899),(857,916),(894,933),(866,949),(758,935)],(65,65,55))
poly([(727,914),(760,906),(854,921),(884,932),(861,938),(758,927)],(188,121,70))
poly([(740,914),(764,911),(849,925),(870,932),(859,933),(762,923)],(43,62,59))
poly([(730,918),(759,932),(867,946),(887,934),(862,952),(757,939)],(111,75,51))
line([(730,916),(758,930),(865,945),(886,934)],(226,163,93),2)
line([(759,935),(863,949)],(58,67,58),2)
for x,y in [(774,919),(812,925),(844,930)]:
    line([(x-3,y+5),(x+5,y-4)],(179,127,77),4)
line([(780,901),(849,958)],(72,69,53),3)
line([(779,899),(849,956)],(213,164,101),1)
poly([(843,950),(852,950),(866,963),(859,966)],(131,91,56))
# Sparse marram grasses at the foot of the print.
for cluster in [20,51,984,1005]:
    for i in range(9):
        x=cluster+rng.uniform(-14,14); y=rng.uniform(1011,1036)
        line([(x,y),(x+rng.uniform(-13,10),y-rng.uniform(16,48))],(61,78,66),rng.uniform(.5,1.4))
# Small gulls, with pointed wings rather than repeated text glyphs.
for x,y,size in [(177,327,12),(215,345,8),(827,386,13),(850,365,7),(786,400,6)]:
    line([(x-size,y-3),(x-size*.5,y-4),(x,y),(x+size*.45,y-6),(x+size,y-7)],(40,63,69),1.4)
# The sole lettering, widely tracked and optically centred.
font=ImageFont.truetype(str(ROOT/'fonts/LiberationSerif-Bold.ttf'),112*S)
word='VELMARIS'; tracking=11*S
widths=[d.textlength(c,font=font) for c in word]
x=(1024*S-sum(widths)-tracking*(len(word)-1))/2
shadow=Image.new('RGBA',im.size); sd=ImageDraw.Draw(shadow)
for c,w in zip(word,widths):
    sd.text((x+1*S,91*S+2*S),c,font=font,fill=(20,43,49,150),stroke_width=0)
    x+=w+tracking
shadow=shadow.filter(ImageFilter.GaussianBlur(1.2*S))
im=Image.alpha_composite(im.convert('RGBA'),shadow).convert('RGB');d=ImageDraw.Draw(im)
x=(1024*S-sum(widths)-tracking*(len(word)-1))/2
for c,w in zip(word,widths):
    d.text((x,91*S),c,font=font,fill=(249,223,174))
    x+=w+tracking
im=im.resize((1024,1024),Image.Resampling.LANCZOS)
# A common paper substrate ties sky, type, masonry and water together.
p=im.load()
for y in range(1024):
    for x in range(1024):
        r,g,b=p[x,y]
        grain=rng.gauss(0,1.65)
        # Faint staggered ink dots and fibres, with no external noise source.
        grain += (-.85 if (x+2*(y//3))%4==0 and y%3==0 else .10)
        grain += .28*math.sin(x*1.7+y*.31)
        edge=((x-511.5)/724)**2+((y-511.5)/724)**2
        shade=1-.135*edge
        p[x,y]=tuple(max(0,min(255,round(v*shade+grain))) for v in (r+2,g+1,b))
# Indexed lithographic palette preserves fine texture within the upload budget.
out=Path(os.environ.get('VELMARIS_OUTPUT', '/output/entry.png'))
out.parent.mkdir(parents=True,exist_ok=True)
im=im.quantize(colors=256,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
im.save(out,optimize=True,compress_level=9)
if out.stat().st_size>1048576:
    raise RuntimeError('Poster exceeds the competition size cap')
print(f'{out}: {im.width}x{im.height}, {out.stat().st_size:,} bytes')

if _BOOTSTRAP is not None:
    _BOOTSTRAP.cleanup()
