import argparse as ap
import re
import datetime as dt
import math
import os
import shutil as sh
import sys
from pilmoji import Pilmoji as pm
from PIL import Image as Im, ImageFont as F, ImageDraw as D
from moviepy.editor import ImageSequenceClip as isc, AudioFileClip as ac, concatenate_videoclips as cv, CompositeAudioClip as cac

W = 1777
MH = 231
LH = 80
LMW = 7

PPW = 120

BGC = (54,57,63,255)
BGC_M = (68,64,57)
LMC = (239,177,50)
MFC = (220,220,220)
MC = (201,205,251)
MBC = (65,70,118)
LLC = (239,177,50)
UC = (5,168,252)

MX = 190
MY = 130
MDY = LH

NP = (MX,53)
NC = (255,255,255,255)
NS = 50
NF = F.truetype('fonts/whitneymedium.otf', NS)

TY = 67
TC = (180,180,180)
TS = 30
TF = F.truetype('fonts/whitneymedium.otf', TS)

MS = 50
MF = F.truetype('fonts/whitneybook.otf', MS)

IN = 0

FPS = 2
NA = os.path.join('audios', 'notification.mp3')
mv = False
cs = []

# Set usernames for join notifications
join_notifications = {
    "ProBot": "just slid into the server.",
    "MEE6": "appeared.",
    "Dyno": "Yay you made it!",
    "Ticket Tool": "is here.",
    "Carl-bot": "A wild appeared.",
    "Arcane": "joined the party.",
    "Mimu": "Yay you made it!",
    "OwO": "just landed.",
    "Truth or Dare": "just landed.",
    "Nekotina": "hopped into the server.",
    "Dank Memer": "just showed up!",
    "Tupperbox": "just slid into the server.",
    "Bloxlink": "just landed."
}

def main():
    global mv

    parser = ap.ArgumentParser(description='CLI to read parameters')
    parser.add_argument('-i', '--input', help='Input file path', required=True)
    parser.add_argument('-c', '--clear', help='Delete output folder', action='store_true')
    parser.add_argument('-m', '--movie', help='Generate movie', action='store_true')
    
    args = parser.parse_args()

    pn = os.path.splitext(os.path.basename(args.input))[0]
    inf = args.input
    of = os.path.join('output', pn)
    cl = args.clear
    mv = args.movie

    if not os.path.exists(inf):
        print(f"Error: Input file '{inf}' not found.")
        return

    if cl and os.path.exists(of):
        sh.rmtree(of)
    if not os.path.exists(of):
        os.makedirs(of)

    with open(inf, encoding="utf8") as f:
        ls = f.read().splitlines()

    mbs = get_mbs(ls)

    for i, mb in enumerate(mbs):
        gen_img(i, mb, of)

    if mv:
        gen_mv(pn, of)

def gen_mv(pn, of):
    v = cv(cs, method="compose")
    v.write_videofile(os.path.join(of, f'{pn}.mp4'), codec="libx264", audio_codec="aac")

def gen_img_for_block(bn, mb, of):
    ls = []
    u = mb[0].split(':')[1]
    t = mb[1]
    for i, l in enumerate(mb[2:]):
        ls.append(l)
        gen_img(bn, u, t, ls, of)

def gen_img(bn, u, t, ls, of):
    global IN
    global mv
    global cs

    fm = is_fm(ls)
    tmpl = Im.new(mode='RGBA', 
                  size=(W, MH + (LH * (len(ls) - 1)) + calc_ii_h(ls)), 
                  color=def_bg_c(ls))
    
    mp = [MX, MY]

    for i, l in enumerate(ls):
        l = l.split('-->')[0]
        if l[0] == '@':
            gen_lwm(mp, tmpl, i, l, fm)
            mp[1] += MDY
        elif l.startswith('[image:'):
            mp = gen_ii(mp, tmpl, i, l)
        elif l.startswith('[url:'):
            with pm(tmpl) as pmoji:
                u = l[5:len(l)-1]
                pmoji.text(mp, u, UC, font=MF)
            mp[1] += MDY
        else:
            with pm(tmpl) as pmoji:
                pmoji.text(mp, l.strip(), MFC, font=MF)
            mp[1] += MDY
    
    gen_pnt(tmpl, u, t)

    # Add a join notification if username exists
    join_msg = get_join_msg(u)
    if join_msg:
        add_join_msg(tmpl, join_msg)

    dr = D.Draw(tmpl)
    if fm:
        dr.rectangle((0, 0, LMW, mp[1] + (MDY * 0.25)), fill=LMC)

    ip = f'{of}/{bn:03d}-{IN:03d}{u}.png'
    print(f'Generating image {ip}')
    tmpl.save(ip)
    IN += 1

    if mv:
        add_clip(ls, ip)

def add_join_msg(tmpl, msg):
    dr = D.Draw(tmpl)
    msg_pos = (MX, MY + LH * 2)  # Position the join message below the main content
    dr.text(msg_pos, msg, MFC, font=MF)

def get_join_msg(username):
    if username in join_notifications:
        return f"{username} {join_notifications[username]} — Today at {dt.datetime.now().strftime('%H:%M')}"
    return None

def add_clip(ls, ip):
    f = FPS
    if "-->" in ls[-1]:
        f = float(ls[-1].split('-->')[1].strip())
    clp = isc([ip], fps=1/f)
    ac1 = ac(NA)
    cs.append(clp.set_audio(ac1))

def gen_ii(mp, tmpl, i, l):
    mr = 12
    im = Im.open(os.path.join('images', l[7:len(l.strip())-1]))
    msk = Im.new("L", im.size, 0)
    dr = D.Draw(msk)
    im_alpha = im.convert("RGBA")
    im_alpha.putalpha(msk)
    im.thumbnail(im_alpha.size, Im.Resampling.LANCZOS)
    dr.rounded_rectangle([(mr, 0), (im.width - mr, im.height)], radius=mr, fill=255)
    tmpl.paste(im, (mp[0], mp[1]), msk)
    mp[0] = MX
    mp[1] += math.floor(im.size[1])
    return mp[0:2]

def gen_lwm(mp, tmpl, i, l, fm):
    dr = D.Draw(tmpl)
    ur = l.split(' ')[0]
    c = l[len(ur):]
    bbox = dr.textbbox((0, 0), ur, font=MF)
    uw = bbox[2] - bbox[0]
    uh = bbox[3] - bbox[1]
    x, y = mp
    
    dr.rectangle((LMW,  mp[1], 
                  W, mp[1] + (MDY * 0.85)), fill=BGC_M)
    dr.rectangle((0,  mp[1], LMW, mp[1] + (MDY * 0.85)), fill=LLC)
    
    up = (x, y + 10, x + uw, y + uh + 12)
    dr.rectangle(up, fill=MBC)
    
    with pm(tmpl) as pmoji:
        pmoji.text(mp, ur, MC, font=NF)
        pmoji.text((mp[0] + uw, mp[1]), c, MFC, font=MF)

def gen_pnt(tmpl, u, t):
    pf = "profiles"
    fs = os.listdir(pf)   
    pat = re.compile(rf'{u}-(\w+\_\w+\_\w+)\.jpeg')
    match_files = [f for f in fs if pat.match(f)]
    if match_files:
        fn = match_files[0]
        nc = tuple(map(int, fn.split('-')[1].split('.')[0].split('_')))
    else:
        fn = f'{u}.jpeg'
        nc = NC

    pp = Im.open(os.path.join(pf, fn))
    pp.thumbnail([sys.maxsize, PPW], Im.Resampling.LANCZOS)
    msk = Im.new("L", pp.size, 0)
    dr = D.Draw(msk)
    dr.ellipse([(0, 0), (PPW, PPW)], fill=255)
    tmpl.paste(pp, (36, 45), msk)

    dr_name = D.Draw(tmpl)
    dr_name.text(NP, u, nc, font=NF)

    dr_time = D.Draw(tmpl)
    tp = (NP[0] + NF.getlength(u) + 25, TY)  
    dr_time.text(tp, f'Today at {t}')
