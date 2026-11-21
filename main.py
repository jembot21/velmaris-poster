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


sky_stops = [(0, (18, 47, 63)), (175, (35, 68, 80)), (310, (113, 86, 103)),
             (430, (194, 117, 106)), (530, (245, 177, 105)), (570, (245, 193, 126))]
water_stops = [(540, (93, 125, 125)), (625, (43, 95, 108)),
               (820, (24, 68, 82)), (1024, (17, 46, 59))]
canvas = Image.new("RGB", (SIZE, SIZE))
px = canvas.load()
for y in range(SIZE):
    for x in range(SIZE):
        if y < 551:
            color = ramp(sky_stops, y)
            radius = ((x - 653) / 295) ** 2 + ((y - 501) / 174) ** 2
            corona = math.exp(-radius * .78) * .36 + math.exp(-radius * 2.9) * .22
            color = blend(color, (255, 197, 128), corona)
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


# Soft, broken streaks of cloud settle between the rose band and the horizon.
cloud = Image.new("RGBA", im.size, (0, 0, 0, 0))
cd = ImageDraw.Draw(cloud)
for x, y, rx in [(116, 350, 130), (411, 391, 171), (864, 338, 149), (912, 438, 95)]:
    cd.ellipse(((x-rx)*SCALE, (y-3)*SCALE, (x+rx)*SCALE, (y+4)*SCALE), fill=(243, 166, 145, 29))
cloud = cloud.filter(ImageFilter.GaussianBlur(7 * SCALE))
im = Image.alpha_composite(im.convert("RGBA"), cloud).convert("RGB")
draw = ImageDraw.Draw(im)
for _ in range(145):
    x, y = randomizer.uniform(-120, 1050), randomizer.uniform(266, 488)
    color = blend(ramp(sky_stops, y), (243, 175, 145), randomizer.uniform(.08, .2))
    stroke([(x, y), (x + randomizer.uniform(30, 175), y - randomizer.uniform(0, 3))], color,
           randomizer.uniform(.45, 1.1))

# The setting sun and low distant headlands define the horizon.
sun_glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
sg = ImageDraw.Draw(sun_glow)
sg.ellipse((548*SCALE, 399*SCALE, 758*SCALE, 603*SCALE), fill=(255, 176, 103, 27))
sg.ellipse((577*SCALE, 427*SCALE, 730*SCALE, 577*SCALE), fill=(255, 196, 116, 49))
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
    pd.ellipse(((x-rx)*SCALE, (y-ry)*SCALE, (x+rx)*SCALE, (y+ry)*SCALE), fill=(40, 66, 69, 37))
    pd.ellipse(((x-rx+2)*SCALE, (y-ry+2)*SCALE, (x+rx-2)*SCALE, (y+ry-2)*SCALE),
               fill=(*tint, alpha))
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

# Fine etched marks in the exposed mudflats and broken lighthouse reflection.
for _ in range(7800):
    y, x = randomizer.uniform(740, 1024), randomizer.uniform(0, 1024)
    c = randomizer.choice([(176, 148, 113), (125, 124, 108), (192, 157, 117), (103, 119, 111)])
    stroke([(x, y), (x + randomizer.uniform(2, 20), y - randomizer.uniform(0, .5))], c, .45)
for _ in range(150):
    y = randomizer.uniform(718, 984)
    x = randomizer.gauss(657, 8 + (y - 718) * .13)
    stroke([(x, y), (x + randomizer.uniform(2, 14), y)],
           randomizer.choice([(210, 165, 103), (185, 148, 101), (224, 176, 106)]), .55)

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
rld.ellipse((652*SCALE, 610*SCALE, 799*SCALE, 724*SCALE), fill=(255, 174, 79, 53))
rock_light = rock_light.filter(ImageFilter.GaussianBlur(18*SCALE))
im = Image.alpha_composite(im.convert("RGBA"), rock_light).convert("RGB")
draw = ImageDraw.Draw(im)
for _ in range(560):
    x, y = randomizer.uniform(543, 760), randomizer.uniform(637, 699)
    if x < 735 - max(0, y - 648) * .35:
        c = randomizer.choice([(49, 68, 67), (58, 78, 74), (93, 99, 80), (111, 111, 89),
                               (148, 127, 96), (162, 136, 101), (183, 152, 111), (207, 169, 118)])
        stroke([(x, y), (x + randomizer.uniform(2, 18), y - randomizer.uniform(.3, 4))], c,
               randomizer.choice([.55, .8, 1.1]))

# A curved, tapering stone causeway approaches from the lower-left foreground.
inner = bezier((-72, 1048), (42, 823), (414, 865), (606, 687))
outer = bezier((105, 1048), (156, 868), (461, 892), (624, 692))
road_edge = bezier((-49, 1024), (81, 799), (431, 853), (612, 681))
polygon(inner + outer[::-1], (43, 59, 58))
polygon(road_edge + outer[::-1], (159, 139, 108))
stroke(road_edge, (221, 181, 125), 2.6)
stroke(outer, (68, 79, 73), 3.5)
for i in range(3, 117, 3):
    a, b = road_edge[i], outer[i]
    stroke([a, b], (101, 101, 86), .8)
    an, bn = road_edge[min(i + 3, 120)], outer[min(i + 3, 120)]
    for f in (.3, .62, .83):
        t = f + (.035 if i % 2 else -.035)
        stroke([(a[0]*(1-t)+b[0]*t, a[1]*(1-t)+b[1]*t),
                (an[0]*(1-t)+bn[0]*t, an[1]*(1-t)+bn[1]*t)], (116, 112, 92), .65)

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
stroke([(624, 614), (684, 614)], (49, 70, 67), 3)
for y in (379, 475, 570):
    polygon([(648, y), (655, y-1), (655, y+13), (648, y+14)], (45, 68, 69))
    stroke([(647, y+15), (657, y+14)], (226, 194, 146), .8)

# Lantern light falls softly across the rock below, behind the tower and cottage.
halo = Image.new("RGBA", im.size, (0, 0, 0, 0))
hd = ImageDraw.Draw(halo)
hd.ellipse((625*SCALE, 302*SCALE, 686*SCALE, 380*SCALE), fill=(255, 175, 73, 34))
halo = halo.filter(ImageFilter.GaussianBlur(16 * SCALE))
im = Image.alpha_composite(im.convert("RGBA"), halo).convert("RGB")
draw = ImageDraw.Draw(im)
polygon([(630, 333), (678, 333), (684, 343), (625, 343)], (48, 71, 68))
polygon([(635, 299), (674, 299), (674, 332), (635, 332)], (243, 183, 87))
for x in range(636, 674):
    color = blend((255, 222, 135), (214, 133, 65), abs(x - 652) / 24)
    stroke([(x, 302), (x, 329)], color, 1)
oval((645, 306, 664, 326), (255, 241, 177))
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

# A stranded rowing skiff with a dark underside, plank highlights and oars.
oval((714, 945, 900, 961), (68, 84, 79))
polygon([(718, 916), (758, 900), (859, 918), (895, 934), (867, 951), (756, 937)], (58, 61, 55))
polygon([(725, 916), (760, 907), (855, 923), (885, 934), (862, 941), (758, 929)], (181, 113, 66))
polygon([(738, 917), (764, 912), (850, 927), (870, 934), (859, 936), (763, 925)], (40, 59, 56))
polygon([(727, 920), (759, 934), (869, 948), (888, 936), (865, 954), (756, 940)], (105, 72, 52))
stroke([(728, 917), (760, 932), (866, 947), (886, 936)], (224, 159, 89), 1.6)
for x, y in [(773, 920), (811, 926), (843, 930)]:
    stroke([(x-3, y+5), (x+5, y-4)], (174, 124, 76), 3)
stroke([(781, 900), (849, 959)], (59, 62, 53), 2.5)
stroke([(780, 899), (850, 957)], (207, 157, 94), .9)

# Gulls are tiny winged cuts of ink, kept clear of the title.
for x, y, size in [(155, 323, 12), (201, 354, 8), (842, 369, 12), (872, 396, 7), (792, 408, 6)]:
    stroke([(x-size, y-3), (x-size*.48, y-4), (x, y), (x+size*.45, y-6), (x+size, y-7)], (38, 60, 65), 1.25)

# Only lettering: individually tracked serif capitals, centered in the upper sky.
font = ImageFont.truetype(str(ROOT / "fonts" / "LiberationSerif-Bold.ttf"), 108 * SCALE)
letters = "VELMARIS"
tracking = 11 * SCALE
advances = [draw.textlength(char, font=font) for char in letters]
start = (SIZE*SCALE - sum(advances) - tracking*(len(letters)-1)) / 2
shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
x = start
for char, advance in zip(letters, advances):
    sd.text((round(x + SCALE), 91*SCALE + 2*SCALE), char, font=font, fill=(20, 43, 49, 135))
    x += advance + tracking
shadow = shadow.filter(ImageFilter.GaussianBlur(1.1*SCALE))
im = Image.alpha_composite(im.convert("RGBA"), shadow).convert("RGB")
draw = ImageDraw.Draw(im)
x = start
for char, advance in zip(letters, advances):
    draw.text((round(x), 91*SCALE), char, font=font, fill=(249, 226, 181))
    x += advance + tracking

# Aged print finish: restrained vignette, paper flecks and deterministic grain.
im = im.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
pixels = im.load()
for y in range(SIZE):
    for x in range(SIZE):
        r, g, b = pixels[x, y]
        edge = ((x - 511.5) / 724) ** 2 + ((y - 511.5) / 724) ** 2
        shade = 1 - .13 * edge
        gx, gy = x % 7 - 3, y % 7 - 3
        halftone = -1.15 if gx*gx + gy*gy <= 2 and (x // 7 + y // 7) % 2 == 0 else 0
        noise = randomizer.gauss(0, 1.75) + (.35 if (x + y * 3) % 11 == 0 else 0) + halftone
        pixels[x, y] = tuple(max(0, min(255, round(channel * shade + noise)))
                             for channel in (r + 2, g + 1, b))

output = Path(os.environ.get("VELMARIS_OUTPUT", "/output/entry.png"))
output.parent.mkdir(parents=True, exist_ok=True)
im = im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
im.save(output, format="PNG", optimize=True, compress_level=9)
if output.stat().st_size > 1_048_576:
    raise RuntimeError(f"PNG exceeds 1,048,576-byte limit: {output.stat().st_size}")
print(f"{output}: 1024x1024, {output.stat().st_size:,} bytes")
if _wheel_dir is not None:
    _wheel_dir.cleanup()
