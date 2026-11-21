"""Render a deterministic, printed travel poster for the island of Velmaris."""
from pathlib import Path
import math
import os
import random
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
_wheel_dir = None
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    wheels = sorted((ROOT / "vendor").glob("pillow-*.whl"))
    if not wheels:
        raise RuntimeError("Pillow is missing and no bundled wheel was found") from None
    _wheel_dir = tempfile.TemporaryDirectory(prefix="velmaris-pillow-")
    with zipfile.ZipFile(wheels[0]) as archive:
        archive.extractall(_wheel_dir.name)
    sys.path.insert(0, _wheel_dir.name)
    from PIL import Image, ImageDraw, ImageFont, ImageFilter

SIZE = 1024
SCALE = 2
randomizer = random.Random(284611)


def blend(a, b, amount):
    amount = max(0.0, min(1.0, amount))
    return tuple(round(x + (y - x) * amount) for x, y in zip(a, b))


def ramp(stops, y):
    for (ya, ca), (yb, cb) in zip(stops, stops[1:]):
        if y <= yb:
            return blend(ca, cb, (y - ya) / (yb - ya))
    return stops[-1][1]


sky_stops = [(0, (17, 39, 59)), (170, (38, 65, 83)), (275, (85, 83, 107)),
             (365, (153, 100, 117)), (445, (218, 132, 116)),
             (510, (247, 181, 123)), (551, (247, 205, 151))]
water_stops = [(540, (119, 143, 139)), (591, (57, 105, 117)),
               (690, (29, 76, 94)), (820, (20, 56, 76)), (1024, (16, 43, 60))]
canvas = Image.new("RGB", (SIZE, SIZE))
px = canvas.load()
for y in range(SIZE):
    for x in range(SIZE):
        if y < 551:
            color = ramp(sky_stops, y)
            radius = ((x - 653) / 295) ** 2 + ((y - 501) / 174) ** 2
            corona = math.exp(-radius * .55) * .28 + math.exp(-radius * 3.2) * .36
            color = blend(color, (255, 203, 136), corona)
            # Slow pigment tides and suspended vapour, not visible gradient steps.
            vapour = (math.sin(x*.013 + y*.031) +
                      .45*math.sin(x*.037 - y*.017) + math.sin(y*.071)) / 2.45
            color = blend(color, (117, 107, 134), max(0, vapour)*.055)
            haze = math.exp(-((y - 532)/27)**2)
            color = blend(color, (255, 216, 168), haze*.21)
        else:
            color = ramp(water_stops, y)
            mottling = (math.sin(x * .012 + math.sin(y * .009) * 1.2) *
                        math.sin(y * .017 - x * .004) +
                        .48 * math.sin(x * .006 + y * .011))
            color = blend(color, (105, 135, 132), .035 + max(0, mottling) * .035)
            undulation = math.sin(y * .075 + math.sin(x * .009) * 1.1 + math.sin(x * .021) * .28)
            color = blend(color, (133, 151, 137), max(0, undulation) * .105)
            depth = (y - 545) / 479
            center = 654 + depth * 14
            path = math.exp(-((x - center) / (15 + depth * 92)) ** 2)
            color = blend(color, (231, 168, 103), path * .36)
        # Low-amplitude pigment variation is added before the finer drawn marks.
        grain = randomizer.uniform(-1.5, 1.5)
        px[x, y] = tuple(max(0, min(255, round(v + grain))) for v in color)

im = canvas.resize((SIZE * SCALE, SIZE * SCALE), Image.Resampling.BICUBIC)
draw = ImageDraw.Draw(im)


def polygon(points, color):
    draw.polygon([(round(x * SCALE), round(y * SCALE)) for x, y in points], fill=color)


def stroke(points, color, width=1):
    draw.line([(round(x * SCALE), round(y * SCALE)) for x, y in points],
              fill=color, width=max(1, round(width * SCALE)))


def oval(box, color):
    draw.ellipse(tuple(round(n * SCALE) for n in box), fill=color)


def bezier(a, b, c, d, count=120):
    points = []
    for i in range(count + 1):
        t = i / count
        u = 1 - t
        points.append((u**3*a[0] + 3*u*u*t*b[0] + 3*u*t*t*c[0] + t**3*d[0],
                       u**3*a[1] + 3*u*u*t*b[1] + 3*u*t*t*c[1] + t**3*d[1]))
    return points


# Wind-shaped cloud banks: soft bodies with broken, sunlit lower hems.
# Each bank has its own silhouette and optical depth; the title has open sky.
weather_rng = random.Random(48217)
cloud = Image.new("RGBA", im.size, (0, 0, 0, 0))
cd = ImageDraw.Draw(cloud)
cloud_banks = [(-90, 254, 420, 24, (38, 61, 79), 88),
               (736, 234, 390, 27, (43, 62, 83), 96),
               (23, 321, 455, 24, (76, 75, 99), 112),
               (753, 362, 399, 21, (100, 76, 98), 116),
               (-114, 411, 480, 17, (119, 83, 103), 112),
               (347, 438, 221, 10, (151, 97, 110), 85),
               (813, 472, 316, 12, (157, 105, 115), 93)]
for left, y, width, height, tint, opacity in cloud_banks:
    ridge, hem = [], []
    for i in range(39):
        t = i/38
        envelope = math.sin(math.pi*t)**.7
        wave = math.sin(t*23+left)*.24 + math.sin(t*53)*.11
        ridge.append(((left+t*width)*SCALE,
                      (y-height*envelope*(.76+wave))*SCALE))
        hem.append(((left+t*width)*SCALE,
                    (y+height*envelope*(.19+.09*math.sin(t*29)))*SCALE))
    cd.polygon(ridge+hem[::-1], fill=(*tint, opacity))
    # Gold lies only on the scalloped underside facing the low sun.
    for i in range(5, 34):
        if weather_rng.random() < .73:
            cd.line([hem[i], hem[i+1]], fill=(255, 180, 139, int(opacity*.62)),
                    width=max(1, round(1.1*SCALE)))
cloud = cloud.filter(ImageFilter.GaussianBlur(2.8*SCALE))
im = Image.alpha_composite(im.convert("RGBA"), cloud).convert("RGB")
# Thin veils drift across the glow, at a softer scale than the cloud banks.
veil = Image.new("RGBA", im.size, (0, 0, 0, 0))
vd = ImageDraw.Draw(veil)
for _ in range(75):
    x, y = weather_rng.uniform(-150, 1050), weather_rng.uniform(300, 530)
    width = weather_rng.uniform(35, 185)
    vd.ellipse((x*SCALE, y*SCALE, (x+width)*SCALE,
                (y+weather_rng.uniform(1, 4))*SCALE), fill=(255, 198, 163, 17))
veil = veil.filter(ImageFilter.GaussianBlur(3.5*SCALE))
im = Image.alpha_composite(im.convert("RGBA"), veil).convert("RGB")
draw = ImageDraw.Draw(im)

# The setting sun and low distant headlands define the horizon.
sun_glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
sg = ImageDraw.Draw(sun_glow)
for radius, alpha in [(172, 12), (121, 20), (82, 37), (55, 57)]:
    sg.ellipse(((654-radius)*SCALE, (499-radius*.82)*SCALE,
                (654+radius)*SCALE, (499+radius*.82)*SCALE),
               fill=(255, 199, 126, alpha))
sun_glow = sun_glow.filter(ImageFilter.GaussianBlur(31*SCALE))
im = Image.alpha_composite(im.convert("RGBA"), sun_glow).convert("RGB")
draw = ImageDraw.Draw(im)
oval((610, 455, 697, 542), (250, 205, 146))
oval((616, 461, 691, 536), (255, 219, 157))
polygon([(0, 532), (75, 520), (128, 526), (172, 514), (226, 522), (293, 540), (0, 550)], (70, 101, 104))
polygon([(836, 540), (883, 518), (925, 523), (971, 509), (1024, 520), (1024, 550)], (71, 98, 101))
stroke([(0, 550), (1024, 550)], (174, 155, 125), .8)

# Thousands of short etched wave marks; the sun-path grows broad in the foreground.
for _ in range(11500):
    y, x = randomizer.uniform(552, 1024), randomizer.uniform(0, 1024)
    depth = (y - 545) / 479
    center = 654 + depth * 14
    glint = math.exp(-((x - center) / (21 + depth * 89)) ** 2)
    if randomizer.random() < glint * .78:
        color = blend(ramp(water_stops, y), (255, 213, 141), randomizer.uniform(.32, .8))
    else:
        shadow = (14, 46, 60) if randomizer.random() < .5 else (134, 157, 145)
        color = blend(ramp(water_stops, y), shadow, randomizer.uniform(.08, .32))
    length = randomizer.uniform(1.2, 7.5) * (.45 + depth * 1.5)
    stroke([(x, y), (x + length, y)], color, randomizer.choice([.45, .55, .8]))
for _ in range(6400):
    y = randomizer.uniform(553, 904)
    depth = (y - 545) / 479
    spread = 6 + depth * 46
    x = randomizer.gauss(654 + depth * 14, spread)
    concentration = math.exp(-((x - (654 + depth * 14)) / (spread * .9)) ** 2)
    c = blend(ramp(water_stops, y), (255, 235, 177), .43 + concentration * randomizer.uniform(.22, .48))
    length = randomizer.uniform(1.2, 5.5) * (1 + depth * 1.15)
    stroke([(x, y), (x + length, y)], c, randomizer.choice([.5, .65, .8]))

# Long swell fronts sit beneath the small etched ripples. Broken bright crests
# widen with perspective and leave deep indigo troughs between them.
sea_rng = random.Random(5916)
for row in range(32):
    y = 555 + (row/31)**1.65*185
    depth = (y-550)/195
    for left in range(-25, 1050, 105):
        x = left + sea_rng.uniform(-28, 24)
        length = sea_rng.uniform(32, 92)*(0.5+depth*.7)
        curve = [(x+t*length, y+math.sin(t*math.pi)*(.3+depth*1.2))
                 for t in [i/12 for i in range(13)]]
        stroke(curve, blend(ramp(water_stops, y), (149, 164, 150), .16), .65)
        if abs(x-654) < 26+depth*74:
            stroke(curve[:8], (233, 186, 123), .8)
for _ in range(280):
    y = sea_rng.uniform(553, 731)
    spread = 3+(y-550)*.14
    x = sea_rng.gauss(654, spread)
    stroke([(x, y), (x+sea_rng.uniform(2, 10), y)],
           sea_rng.choice([(255, 223, 159), (248, 199, 128), (255, 235, 181)]), .7)

# A quiet amber ladder catches the keeper's lamp close to the island.
lamp_reflection = Image.new("RGBA", im.size, (0, 0, 0, 0))
lr = ImageDraw.Draw(lamp_reflection)
for i in range(15):
    y = 676 + i * 5
    half = 29 + i * 2.3
    alpha = max(5, 25 - i)
    lr.line(((657 - half) * SCALE, y * SCALE, (657 + half) * SCALE, y * SCALE),
            fill=(255, 180, 103, alpha), width=max(1, round((1.4 + i * .08) * SCALE)))
lamp_reflection = lamp_reflection.filter(ImageFilter.GaussianBlur(5 * SCALE))
im = Image.alpha_composite(im.convert("RGBA"), lamp_reflection).convert("RGB")
draw = ImageDraw.Draw(im)
for _ in range(260):
    y = randomizer.uniform(674, 751)
    depth = (y - 545) / 479
    x = randomizer.gauss(657, 9 + depth * 13)
    stroke([(x, y), (x + randomizer.uniform(2, 13), y)],
           blend(ramp(water_stops, y), (255, 205, 125), randomizer.uniform(.28, .62)), .65)

# Low-tide shelves: alternating bars of mud, wet sand, and shallow reflected pools.
polygon([(0, 750), (100, 729), (216, 748), (328, 721), (449, 744), (556, 721),
         (670, 733), (783, 706), (908, 726), (1024, 715), (1024, 1024), (0, 1024)], (79, 101, 96))
polygon([(0, 815), (126, 780), (249, 797), (378, 769), (515, 790), (668, 758),
         (839, 784), (1024, 759), (1024, 1024), (0, 1024)], (127, 121, 101))
polygon([(0, 884), (125, 849), (272, 855), (392, 824), (533, 850), (670, 810),
         (808, 834), (1001, 803), (1024, 1024), (0, 1024)], (157, 136, 108))
polygon([(0, 951), (175, 896), (313, 906), (464, 871), (589, 898), (756, 854),
         (914, 875), (1024, 838), (1024, 1024), (0, 1024)], (176, 144, 111))
polygon([(0, 968), (175, 915), (338, 930), (500, 894), (660, 921), (832, 883),
         (1024, 900), (1024, 956), (838, 936), (647, 962), (465, 934), (312, 968),
         (136, 949), (0, 1008)], (91, 113, 109))

# Wet sediment carries blurred rose and gold reflections rather than flat pigment.
wet_colors = {(79, 101, 96), (127, 121, 101), (157, 136, 108), (176, 144, 111), (91, 113, 109)}
wet = im.load()
for yy in range(720*SCALE, 1024*SCALE):
    y = yy / SCALE
    for xx in range(1024*SCALE):
        original = wet[xx, yy]
        if original in wet_colors:
            x = xx / SCALE
            sheen = math.exp(-((x - 650 - 45*math.sin(y*.019))/290)**2)
            ripple = .5 + .5*math.sin(y*.09 + x*.006)
            color = blend(original, (215, 153, 126), sheen*(.08 + .19*ripple))
            damp = .5 + .5*math.sin(x*.014 + math.sin(y*.023)*2)
            wet[xx, yy] = blend(color, (54, 83, 85), damp*.11)

# Scattered pools catch the rose sky and a little lamplight.
pools = Image.new("RGBA", im.size, (0, 0, 0, 0))
pd = ImageDraw.Draw(pools)
for x, y, rx, ry, tint, alpha in [
        (128, 834, 77, 12, (213, 153, 139), 36),
        (333, 790, 92, 10, (231, 171, 131), 34),
        (474, 858, 105, 15, (197, 139, 128), 39),
        (914, 810, 84, 12, (224, 161, 126), 35),
        (765, 775, 90, 11, (246, 183, 119), 44),
        (190, 948, 123, 17, (220, 157, 132), 31),
        (553, 975, 97, 12, (229, 174, 133), 30),
        (946, 948, 107, 15, (200, 142, 128), 34)]:
    # Long irregular tidal pools reflect the sky, with a cool recessed bank.
    outline = [(x-rx, y), (x-rx*.62, y-ry*.66), (x-rx*.14, y-ry),
               (x+rx*.43, y-ry*.48), (x+rx, y-ry*.14),
               (x+rx*.71, y+ry*.51), (x+rx*.12, y+ry), (x-rx*.67, y+ry*.43)]
    pd.polygon([(a*SCALE, b*SCALE) for a,b in outline], fill=(32, 66, 77, 100))
    pd.polygon([(a*SCALE, (b+1.2)*SCALE) for a,b in outline], fill=(*tint, alpha+32))
    pd.line(((x-rx*.55)*SCALE, (y-ry*.12)*SCALE, (x+rx*.42)*SCALE, (y-ry*.12)*SCALE),
            fill=(255, 213, 169, alpha+9), width=max(1, round(.7*SCALE)))
pools = pools.filter(ImageFilter.GaussianBlur(2.2 * SCALE))
im = Image.alpha_composite(im.convert("RGBA"), pools).convert("RGB")
# Irregular dark and rose-toned damp patches interrupt the exposed sediment bands.
mud_texture = Image.new("RGBA", im.size, (0, 0, 0, 0))
md = ImageDraw.Draw(mud_texture)
mud_rng = random.Random(95720)
for _ in range(76):
    x, y = mud_rng.uniform(-20, 1040), mud_rng.uniform(764, 1024)
    rx, ry = mud_rng.uniform(18, 78), mud_rng.uniform(3, 13)
    tint = mud_rng.choice([(37, 68, 72), (45, 74, 77), (211, 139, 130), (230, 165, 130)])
    alpha = mud_rng.randint(12, 27) if tint[0] < 100 else mud_rng.randint(9, 19)
    points = []
    for i in range(8):
        angle = math.tau * i / 8
        jitter = mud_rng.uniform(.72, 1.18)
        points.append(((x + math.cos(angle)*rx*jitter)*SCALE,
                       (y + math.sin(angle)*ry*jitter)*SCALE))
    md.polygon(points, fill=(*tint, alpha))
mud_texture = mud_texture.filter(ImageFilter.GaussianBlur(4.5 * SCALE))
im = Image.alpha_composite(im.convert("RGBA"), mud_texture).convert("RGB")
draw = ImageDraw.Draw(im)

# Tidal runnels: dark recessed cuts paired with a slim reflected-sky lip.
# Marks gather in horizontal seams rather than covering every surface in noise.
for _ in range(2100):
    y, x = randomizer.uniform(752, 1024), randomizer.uniform(0, 1024)
    depth = (y-740)/284
    seam = math.sin(y*.069 + math.sin(x*.009)*2.1)
    if seam < .2:
        continue
    length = randomizer.uniform(3, 22)*(0.6+depth)
    c = blend((70, 101, 107), (194, 163, 139), randomizer.random()*.65)
    stroke([(x, y), (x+length, y-.3)], c, .5)
    if seam > .92:
        stroke([(x+2, y-1), (x+length*.8, y-1.3)], (205, 174, 144), .55)
for _ in range(190):
    y = randomizer.uniform(718, 984)
    x = randomizer.gauss(657, 8+(y-718)*.15)
    stroke([(x, y), (x+randomizer.uniform(2, 17), y)],
           randomizer.choice([(219, 176, 119), (192, 154, 113), (236, 194, 137)]), .65)

# Suspended sea mist reveals a broad, feathered lantern wash toward the tide.
spill = Image.new("RGBA", im.size, (0, 0, 0, 0))
spd = ImageDraw.Draw(spill)
spd.polygon([(650*SCALE, 317*SCALE), (750*SCALE, 693*SCALE),
             (593*SCALE, 723*SCALE)], fill=(255, 192, 108, 12))
spd.ellipse((588*SCALE, 654*SCALE, 760*SCALE, 754*SCALE),
            fill=(255, 190, 105, 23))
spill = spill.filter(ImageFilter.GaussianBlur(24*SCALE))
im = Image.alpha_composite(im.convert("RGBA"), spill).convert("RGB")
draw = ImageDraw.Draw(im)

# The rocky tidal island has sunward ochre faces and cool cut-shadow planes.
polygon([(505, 682), (533, 632), (565, 607), (605, 596), (651, 601), (698, 588),
         (744, 614), (776, 659), (811, 688), (747, 715), (656, 722), (554, 710)], (35, 59, 61))
polygon([(512, 679), (541, 634), (572, 613), (615, 605), (599, 649), (572, 666), (551, 697)], (139, 125, 100))
polygon([(572, 613), (620, 604), (663, 615), (635, 655), (599, 649)], (181, 147, 104))
polygon([(635, 655), (663, 615), (705, 599), (729, 632), (689, 674), (666, 704), (609, 701)], (79, 91, 82))
polygon([(729, 632), (751, 638), (775, 673), (798, 689), (726, 705), (689, 674)], (46, 70, 69))
polygon([(539, 625), (584, 600), (628, 591), (672, 600), (711, 587), (739, 615),
         (690, 632), (626, 626), (574, 638)], (86, 102, 82))
polygon([(723, 642), (757, 653), (792, 686), (731, 701), (700, 683)], (35, 57, 59))
# Broken facets catch the last light along the island's near slope.
polygon([(662, 671), (690, 641), (720, 634), (757, 670), (783, 685),
         (733, 704), (681, 699)], (104, 100, 78))
polygon([(516, 679), (546, 644), (568, 651), (550, 692)], (79, 91, 80))
# A warm spill from the lantern washes the island's near face and cottage wall.
rock_light = Image.new("RGBA", im.size, (0, 0, 0, 0))
rld = ImageDraw.Draw(rock_light)
rld.polygon([(636*SCALE, 605*SCALE), (694*SCALE, 595*SCALE),
             (770*SCALE, 678*SCALE), (698*SCALE, 703*SCALE),
             (608*SCALE, 667*SCALE)], fill=(255, 186, 103, 45))
rld.ellipse((613*SCALE, 600*SCALE, 713*SCALE, 659*SCALE), fill=(255, 212, 139, 52))
rock_light = rock_light.filter(ImageFilter.GaussianBlur(18*SCALE))
im = Image.alpha_composite(im.convert("RGBA"), rock_light).convert("RGB")
draw = ImageDraw.Draw(im)
# Angular fractures give the rock shelf coherent lit caps and deep clefts.
for points, tint in [
    ([(521,677),(544,644),(557,650),(546,677)], (165,137,98)),
    ([(546,677),(557,650),(574,666),(559,694)], (61,79,75)),
    ([(562,638),(583,621),(605,624),(588,645)], (204,163,111)),
    ([(588,645),(605,624),(601,652),(580,667)], (101,103,83)),
    ([(602,662),(629,642),(654,646),(633,667)], (165,139,98)),
    ([(633,667),(654,646),(648,683),(619,698)], (56,77,72)),
    ([(662,650),(688,628),(708,637),(688,657)], (186,150,101)),
    ([(688,657),(708,637),(720,663),(700,682)], (81,90,75)),
    ([(710,677),(730,656),(752,672),(739,688)], (151,125,88)),
    ([(739,688),(752,672),(778,689),(745,703)], (59,77,70)),
    ([(569,684),(590,675),(609,687),(590,703)], (121,115,88))]:
    polygon(points, tint)
    stroke(points[:2], blend(tint, (249,197,128), .35), .8)
for a,b in [((551,696),(578,670)), ((600,653),(590,674)),
            ((648,684),(664,660)), ((710,643),(729,661)), ((731,702),(709,690))]:
    stroke([a,b], (38,61,61), 1.4)

# A curved, tapering stone causeway approaches from the lower-left foreground.
inner = bezier((-72, 1048), (42, 823), (414, 865), (606, 687))
outer = bezier((105, 1048), (156, 868), (461, 892), (624, 692))
road_edge = bezier((-49, 1024), (81, 799), (431, 853), (612, 681))
polygon(inner + outer[::-1], (43, 59, 58))
polygon(road_edge + outer[::-1], (159, 139, 108))
stroke(road_edge, (221, 181, 125), 2.6)
stroke(outer, (68, 79, 73), 3.5)
# Every sett has a top plane, a dark joint and a sunward bevel.
stone_rng = random.Random(7318)
for i in range(1, 118, 3):
    a, b = road_edge[i], outer[i]
    an, bn = road_edge[min(i+3,120)], outer[min(i+3,120)]
    boundaries = [0, .23, .51, .77, 1] if i % 2 else [0, .16, .42, .7, 1]
    for low, high in zip(boundaries, boundaries[1:]):
        def across(c,d,t):
            return (c[0]*(1-t)+d[0]*t, c[1]*(1-t)+d[1]*t)
        q = [across(a,b,low+.008), across(a,b,high-.008),
             across(an,bn,high-.008), across(an,bn,low+.008)]
        tint = blend((121,119,101), (205,172,125), stone_rng.uniform(.15,.83))
        polygon(q, tint)
        stroke(q[:2], (82,91,83), .7)
        stroke([q[3],q[0]], blend(tint,(255,213,148),.48), .85)
        if i < 65:
            stroke([q[2],q[3]], blend(tint,(48,68,66),.42), .7)

# Keeper's cottage, pitched tile roof, chimney, door and amber-lit windows.
polygon([(684, 581), (745, 583), (745, 625), (684, 619)], (211, 174, 119))
polygon([(745, 583), (765, 570), (765, 614), (745, 625)], (126, 119, 94))
# Lantern warmth pools unevenly over the shore-facing plaster.
wall_glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
wgd = ImageDraw.Draw(wall_glow)
wgd.ellipse((674*SCALE, 574*SCALE, 754*SCALE, 635*SCALE), fill=(255, 188, 101, 46))
wall_glow = wall_glow.filter(ImageFilter.GaussianBlur(10*SCALE))
im = Image.alpha_composite(im.convert("RGBA"), wall_glow).convert("RGB")
draw = ImageDraw.Draw(im)
polygon([(675, 583), (709, 553), (779, 568), (745, 590)], (68, 64, 58))
polygon([(678, 581), (709, 557), (745, 568), (716, 590)], (151, 85, 59))
stroke([(681, 581), (711, 560), (772, 571)], (203, 125, 75), 1.7)
polygon([(750, 552), (758, 554), (758, 571), (750, 569)], (134, 116, 91))
for x, y in [(696, 595), (723, 598)]:
    polygon([(x-2, y-2), (x+10, y-2), (x+10, y+14), (x-2, y+14)], (75, 73, 61))
    polygon([(x, y), (x+8, y), (x+8, y+11), (x, y+11)], (255, 199, 104))
    stroke([(x+4, y), (x+4, y+11)], (138, 105, 68), .8)
polygon([(751, 591), (758, 588), (758, 604), (751, 606)], (244, 179, 89))

# The cottage's eaves and sun-facing corner catch a narrow, warm bounce.
stroke([(684, 589), (684, 617), (743, 624)], (247, 196, 129), 1.2)
stroke([(679, 582), (709, 555), (745, 564)], (246, 173, 103), 1.2)
stroke([(750, 552), (750, 567)], (233, 174, 108), .85)

# Tall tapered lighthouse in alternating red and ivory masonry courses.
top, foot = 333, 616
for y in range(top, foot):
    t = (y - top) / (foot - top)
    half = 17 + 14 * t
    red_band = int((y - 333) / 48) % 2 == 1
    for offset in range(-round(half), round(half) + 1):
        u = (offset + half) / (2 * half)
        light = .5 + .5 * math.cos((u - .17) * math.pi)
        dark, bright = ((102, 49, 46), (204, 95, 62)) if red_band else ((126, 130, 115), (248, 219, 166))
        color = blend(dark, bright, light)
        stroke([(654 + offset, y), (655 + offset, y)], color, 1)
# Narrow rims preserve the masonry's volume and alternating courses.
for y in range(top+9, foot-2):
    t = (y-top)/(foot-top)
    half = 17+14*t
    red_band = int((y-333)/48) % 2 == 1
    stroke([(654-half+1, y), (654-half+2.2, y)],
           (241, 151, 91) if red_band else (255, 231, 173), .85)
    if y < 378:
        strength = (378-y)/45
        stroke([(653+half-1, y), (654+half-1, y)],
               blend((137, 131, 107), (255, 201, 119), strength*.8), .8)
stroke([(624, 614), (684, 614)], (49, 70, 67), 3)
for y in (379, 475, 570):
    polygon([(648, y), (655, y-1), (655, y+13), (648, y+14)], (45, 68, 69))
    stroke([(647, y+15), (657, y+14)], (226, 194, 146), .8)

# Nested optical scales: amber air, luminous glass, then a nearly white flame.
halo = Image.new("RGBA", im.size, (0, 0, 0, 0))
hd = ImageDraw.Draw(halo)
for radius, alpha in [(106, 4), (79, 8), (54, 15), (34, 31), (19, 60)]:
    hd.ellipse(((654-radius)*SCALE, (316-radius*.84)*SCALE,
                (654+radius)*SCALE, (316+radius*.84)*SCALE),
               fill=(255, 192, 105, alpha))
halo = halo.filter(ImageFilter.GaussianBlur(11*SCALE))
im = Image.alpha_composite(im.convert("RGBA"), halo).convert("RGB")
draw = ImageDraw.Draw(im)
polygon([(630, 333), (678, 333), (684, 343), (625, 343)], (48, 71, 68))
polygon([(635, 299), (674, 299), (674, 332), (635, 332)], (243, 183, 87))
for x in range(636, 674):
    color = blend((255, 222, 135), (214, 133, 65), abs(x - 652) / 24)
    stroke([(x, 302), (x, 329)], color, 1)
oval((644, 305, 665, 327), (255, 233, 154))
oval((649, 308, 660, 324), (255, 250, 212))
stroke([(638, 315), (671, 315)], (255, 237, 174), 1.1)
for x in (635, 645, 664, 674):
    stroke([(x, 299), (x, 333)], (46, 67, 66), 1.8)
polygon([(627, 300), (654, 274), (682, 300)], (43, 66, 65))
polygon([(630, 298), (654, 278), (654, 298)], (114, 109, 83))
stroke([(654, 274), (654, 262)], (39, 59, 59), 1.6)
oval((651, 259, 657, 266), (60, 70, 63))
stroke([(625, 335), (682, 335)], (218, 165, 96), 1.6)
stroke([(624, 341), (624, 323), (684, 323), (684, 341)], (40, 63, 62), 1)
for x in range(626, 685, 8):
    stroke([(x, 324), (x, 340)], (49, 68, 64), .8)

# Small hot edges link the lantern to the cottage and sun-facing rock crown.
stroke([(630, 298), (653, 278)], (200, 157, 98), 1)
stroke([(630, 332), (676, 332)], (255, 209, 129), 1.1)
stroke([(574, 610), (620, 599), (649, 607)], (219, 171, 108), 1.3)
stroke([(681, 605), (709, 590), (735, 615)], (232, 178, 109), 1.2)

# A stranded rowing skiff with a dark underside, plank highlights and oars.
# A quiet reflected silhouette grounds the hull in the wet silt.
boat_shadow = Image.new("RGBA", im.size, (0,0,0,0))
bsd = ImageDraw.Draw(boat_shadow)
bsd.ellipse((715*SCALE, 941*SCALE, 902*SCALE, 966*SCALE), fill=(26,58,65,110))
bsd.polygon([(741*SCALE,957*SCALE),(866*SCALE,973*SCALE),
             (891*SCALE,966*SCALE),(760*SCALE,948*SCALE)], fill=(194,133,91,35))
boat_shadow = boat_shadow.filter(ImageFilter.GaussianBlur(3*SCALE))
im = Image.alpha_composite(im.convert("RGBA"), boat_shadow).convert("RGB")
draw = ImageDraw.Draw(im)
polygon([(718, 916), (758, 900), (859, 918), (895, 934), (867, 951), (756, 937)], (58, 61, 55))
polygon([(725, 916), (760, 907), (855, 923), (885, 934), (862, 941), (758, 929)], (181, 113, 66))
polygon([(738, 917), (764, 912), (850, 927), (870, 934), (859, 936), (763, 925)], (40, 59, 56))
polygon([(727, 920), (759, 934), (869, 948), (888, 936), (865, 954), (756, 940)], (105, 72, 52))
stroke([(728, 917), (760, 932), (866, 947), (886, 936)], (224, 159, 89), 1.6)
# Curving strakes give the outside its volume; the upper rail holds the light.
stroke([(734,925),(759,936),(865,951),(882,941)], (66,64,54), .9)
stroke([(742,926),(761,932),(865,945)], (184,120,73), .9)
stroke([(719,916),(758,901),(858,918),(893,933)], (246,190,119), 1.9)
stroke([(760,904),(853,921)], (218,155,94), .8)
for x, y in [(773, 920), (811, 926), (843, 930)]:
    stroke([(x-3, y+5), (x+5, y-4)], (174, 124, 76), 3)
stroke([(781, 900), (849, 959)], (59, 62, 53), 2.5)
stroke([(780, 899), (850, 957)], (207, 157, 94), .9)

# Gulls are tiny winged cuts of ink, kept clear of the title.
for x, y, size in [(155, 323, 12), (201, 354, 8), (842, 369, 12), (872, 396, 7), (792, 408, 6)]:
    stroke([(x-size, y-3), (x-size*.48, y-4), (x, y), (x+size*.45, y-6), (x+size, y-7)], (38, 60, 65), 1.25)

# Only lettering: the original tracked serif, printed into the evening palette.
font = ImageFont.truetype(str(ROOT / "fonts" / "LiberationSerif-Bold.ttf"), 108*SCALE)
letters = "VELMARIS"
tracking = 11*SCALE
advances = [draw.textlength(char, font=font) for char in letters]
start = (SIZE*SCALE-sum(advances)-tracking*(len(letters)-1))/2
letter_mask = Image.new("L", im.size, 0)
lmd = ImageDraw.Draw(letter_mask)
x = start
for char, advance in zip(letters, advances):
    lmd.text((round(x), 91*SCALE), char, font=font, fill=255)
    x += advance+tracking
# The depression is softer and smaller than a floating drop shadow.
shadow = Image.new("RGBA", im.size, (0,0,0,0))
shadow_alpha = letter_mask.point(lambda v: round(v*.53))
shadow.putalpha(shadow_alpha)
shifted_shadow = Image.new("RGBA", im.size, (0,0,0,0))
shifted_shadow.paste(shadow, (0, round(1.15*SCALE)))
shifted_shadow = shifted_shadow.filter(ImageFilter.GaussianBlur(.85*SCALE))
im = Image.alpha_composite(im.convert("RGBA"), shifted_shadow).convert("RGB")
# A hairline of compressed, lighter paper at the upper edge of the impression.
emboss_mask = Image.new("L", im.size, 0)
emboss_mask.paste(letter_mask, (0, -1))
im.paste((211, 184, 144), (0,0,im.width,im.height), emboss_mask)
ink = Image.new("RGB", im.size, (242, 216, 170))
ipx, mpx = ink.load(), letter_mask.load()
ink_rng = random.Random(19914)
box = letter_mask.getbbox()
for yy in range(box[1],box[3]):
    for xx in range(box[0],box[2]):
        if mpx[xx,yy]:
            pressure = math.sin(xx*.015+yy*.019)*1.6
            fibre = ink_rng.gauss(0, 1.6)
            dry = ink_rng.random() < .015
            variation = pressure+fibre-(10 if dry else 0)
            ipx[xx,yy] = tuple(round(c+variation) for c in (244,218,172))
im.paste(ink, (0,0), letter_mask)
draw = ImageDraw.Draw(im)

# Printed stock has fibres at two scales, with quiet ink stipple rather than
# a visible dot grid. Warm paper binds the copper sky and the blue tidal water.
im = im.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
paper_rng = random.Random(62840)
stock = Image.new("L", (256,256))
stock.putdata([max(0,min(255,round(paper_rng.gauss(128,13))))
               for _ in range(256*256)])
stock = stock.resize((SIZE,SIZE), Image.Resampling.BICUBIC)
stock = stock.filter(ImageFilter.GaussianBlur(.5))
stock_px = stock.load()
pixels = im.load()
for y in range(SIZE):
    for x in range(SIZE):
        r,g,b = pixels[x,y]
        radial = ((x-511.5)/650)**2 + ((y-490)/755)**2
        # The falloff lives at the corners, leaving the lantern and title clear.
        vignette = max(0, (radial-.17)/1.35)**1.65
        shade = 1-.115*vignette
        tooth = (stock_px[x,y]-128)*.15
        fibre = randomizer.gauss(0,1.35)
        stipple = -2.4 if randomizer.random() < .08 else .2
        noise = tooth+fibre+stipple
        # Denser stock detail remains low-contrast enough for the image to breathe.
        pixels[x,y] = tuple(max(0,min(255,round(channel*shade+noise)))
                            for channel in (r+1.8,g+1.1,b+.35))

output = Path(os.environ.get("VELMARIS_OUTPUT", "/output/entry.png"))
output.parent.mkdir(parents=True, exist_ok=True)
im = im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
im.save(output, format="PNG", optimize=True, compress_level=9)
if output.stat().st_size > 1_048_576:
    raise RuntimeError(f"PNG exceeds 1,048,576-byte limit: {output.stat().st_size}")
print(f"{output}: 1024x1024, {output.stat().st_size:,} bytes")
if _wheel_dir is not None:
    _wheel_dir.cleanup()
