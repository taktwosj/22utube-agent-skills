# -*- coding: utf-8 -*-
"""쇼츠 삽화 3장 — 불꽃 톤, 1080x1415. 글자·숫자·로고·얼굴 없음. Canvas 로 불꽃을 그리고 SVG 로 사물을 얹어 Playwright 로 찍는다."""
import sys, pathlib
from playwright.sync_api import sync_playwright

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).parent
OUT.mkdir(parents=True, exist_ok=True)

FLAME_JS = r"""
const W=1080,H=1415;const c=document.getElementById('fire');const g=c.getContext('2d');
let seed=SEED;function rnd(){seed=(seed*1103515245+12345)&0x7fffffff;return seed/0x7fffffff;}
// 배경: 검붉은 바닥에서 위로 어두워지는 그라데이션
let bg=g.createLinearGradient(0,0,0,H);bg.addColorStop(0,'#07060a');bg.addColorStop(.55,'#160907');bg.addColorStop(1,'#3a0f05');
g.fillStyle=bg;g.fillRect(0,0,W,H);
// 불꽃 기둥: 오프스크린에 그리고 합성할 때 한 번만 블러
function flameLayer(specs, blur){
  const oc=document.createElement('canvas');oc.width=W;oc.height=H;const o=oc.getContext('2d');o.globalCompositeOperation='lighter';
  for(const [cx,baseY,height,width,hue0,alpha] of specs){
    for(let i=0;i<2400;i++){
      const t=Math.pow(rnd(),1.6);const y=baseY-t*height;const spread=width*(1-t*0.75);
      const x=cx+(rnd()-0.5)*spread*(0.6+0.8*Math.sin(t*9+cx))*1.2;
      const r=(1-t)*26+6+rnd()*10;const hue=hue0+t*38+rnd()*8;const light=35+t*30+rnd()*15;
      o.globalAlpha=alpha*(1-t*0.7)*(0.35+rnd()*0.65);o.fillStyle=`hsl(${hue} 100% ${light}%)`;
      o.beginPath();o.ellipse(x,y,r*0.7,r*1.5,(rnd()-0.5)*0.6,0,Math.PI*2);o.fill();
    }
  }
  g.filter=blur?`blur(${blur}px)`:'none';g.drawImage(oc,0,0);g.filter='none';
}
g.globalCompositeOperation='lighter';
flameLayer([[540,H+40,1250,1700,2,0.22],[300,H+60,1000,800,8,0.20],[800,H+60,1080,840,6,0.20],[540,H+80,700,1300,14,0.24]],22);
flameLayer([[540,H+30,900,1300,6,0.16],[540,H+20,420,1400,24,0.26]],8);
flameLayer([[540,H+30,760,1000,10,0.10],[540,H+10,300,1200,28,0.16]],0);
// 불티
for(let i=0;i<900;i++){const x=rnd()*W,y=rnd()*H;const t=1-y/H;g.globalAlpha=0.25+rnd()*0.7*t;g.fillStyle=`hsl(${30+rnd()*25} 100% ${70+rnd()*25}%)`;g.beginPath();g.arc(x,y,0.8+rnd()*2.4*(0.4+t),0,Math.PI*2);g.fill();}
g.globalCompositeOperation='source-over';g.globalAlpha=1;
// 위쪽 연기·어둠
let topG=g.createLinearGradient(0,0,0,H*0.5);topG.addColorStop(0,'rgba(5,4,8,0.9)');topG.addColorStop(1,'rgba(5,4,8,0)');g.fillStyle=topG;g.fillRect(0,0,W,H*0.5);
// 종이 질감 노이즈
g.globalAlpha=0.05;for(let i=0;i<40000;i++){g.fillStyle=rnd()>0.5?'#fff':'#000';g.fillRect(rnd()*W,rnd()*H,1.2,1.2);}g.globalAlpha=1;
"""

def page(seed, svg):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:1080px;height:1415px;overflow:hidden;background:#07060a}}
canvas,svg{{position:absolute;left:0;top:0;width:1080px;height:1415px}}
</style></head><body><canvas id="fire" width="1080" height="1415"></canvas>
<svg viewBox="0 0 1080 1415" xmlns="http://www.w3.org/2000/svg">
<defs>
 <filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="18" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
 <filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6"/></filter>
 <linearGradient id="hot" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#ff3d00"/><stop offset=".5" stop-color="#ff9a1f"/><stop offset="1" stop-color="#ffe27a"/></linearGradient>
 <linearGradient id="paper" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f3ead6"/><stop offset="1" stop-color="#cbbfa4"/></linearGradient>
 <linearGradient id="char" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#1a0d08"/><stop offset="1" stop-color="#3b1a0c"/></linearGradient>
</defs>
{svg}
</svg>
<script>(()=>{{const SEED={seed};{FLAME_JS}}})();</script></body></html>"""

# 1) 지운 문장 — 문서 한 장, 가운데 한 줄이 불에 타 사라진다
svg1 = """
<g transform="rotate(-6 540 700)">
 <rect x="250" y="330" width="580" height="760" rx="10" fill="url(#paper)" stroke="#8a7a5a" stroke-width="3"/>
 <!-- 문장 줄들 -->
 <g fill="#2b2622" opacity=".85">
  <rect x="300" y="400" width="460" height="16" rx="8"/><rect x="300" y="440" width="380" height="16" rx="8"/>
  <rect x="300" y="480" width="470" height="16" rx="8"/><rect x="300" y="520" width="410" height="16" rx="8"/>
  <rect x="300" y="560" width="450" height="16" rx="8"/>
  <rect x="300" y="760" width="430" height="16" rx="8"/><rect x="300" y="800" width="470" height="16" rx="8"/>
  <rect x="300" y="840" width="360" height="16" rx="8"/><rect x="300" y="880" width="450" height="16" rx="8"/>
  <rect x="300" y="920" width="400" height="16" rx="8"/><rect x="300" y="960" width="460" height="16" rx="8"/>
 </g>
 <!-- 타서 사라진 한 줄: 검게 그을린 구멍 -->
 <path d="M285 640 C 340 600, 420 690, 520 630 S 700 700, 800 640 L 810 700 C 720 740, 640 680, 540 720 S 360 690, 280 710 Z" fill="url(#char)"/>
 <path d="M285 640 C 340 600, 420 690, 520 630 S 700 700, 800 640" fill="none" stroke="#ff6a00" stroke-width="7" filter="url(#glow)" opacity=".95"/>
 <path d="M280 710 C 360 690, 440 720, 540 720 S 720 740, 810 700" fill="none" stroke="#ffb020" stroke-width="5" filter="url(#glow)" opacity=".9"/>
 <!-- 구멍 가장자리 불꽃 -->
 <g fill="url(#hot)" filter="url(#glow)" opacity=".95">
  <path d="M330 630 q10 -60 30 -20 q10 -40 25 0 q5 40 -25 45 q-30 5 -30 -25z"/>
  <path d="M470 618 q8 -70 28 -25 q12 -50 30 -5 q8 45 -28 52 q-35 8 -30 -22z"/>
  <path d="M620 650 q12 -55 30 -18 q10 -35 26 2 q6 38 -26 44 q-30 4 -30 -28z"/>
  <path d="M740 632 q10 -65 28 -22 q10 -45 26 -2 q6 42 -26 48 q-30 6 -28 -24z"/>
 </g>
</g>
<!-- 종이 위로 튀는 재 -->
<g fill="#ffd27a" filter="url(#soft)" opacity=".8"><circle cx="360" cy="560" r="4"/><circle cx="700" cy="590" r="3"/><circle cx="520" cy="540" r="5"/><circle cx="640" cy="500" r="3"/></g>
"""

# 2) 거꾸로 된 날짜 — 벽걸이 달력 한 장, 두 날짜 칸 사이가 불타며 뒤집힌다
svg2 = """
<g transform="rotate(4 540 720)">
 <rect x="230" y="300" width="620" height="800" rx="14" fill="url(#paper)" stroke="#8a7a5a" stroke-width="3"/>
 <rect x="230" y="300" width="620" height="120" rx="14" fill="#1f2c48"/>
 <circle cx="330" cy="300" r="14" fill="#2b2622"/><circle cx="750" cy="300" r="14" fill="#2b2622"/>
 <line x1="330" y1="230" x2="330" y2="300" stroke="#2b2622" stroke-width="8"/><line x1="750" y1="230" x2="750" y2="300" stroke="#2b2622" stroke-width="8"/>
 <!-- 날짜 격자 (숫자 없이 칸만) -->
 <g stroke="#b3a688" stroke-width="2" fill="none">
  <path d="M260 480 H820 M260 590 H820 M260 700 H820 M260 810 H820 M260 920 H820"/>
  <path d="M340 450 V1080 M420 450 V1080 M500 450 V1080 M580 450 V1080 M660 450 V1080 M740 450 V1080"/>
 </g>
 <!-- 앞선 칸: 시안 표식 (기소유예안 보고) -->
 <rect x="424" y="594" width="72" height="102" fill="#1d7fb8" opacity=".85"/>
 <!-- 뒤 칸: 붉게 타는 칸 (계엄) -->
 <rect x="664" y="924" width="72" height="102" fill="#7a0e02"/>
 <!-- 순서를 거꾸로 가리키는 불타는 화살: 뒤 칸에서 앞 칸으로 -->
 <path d="M700 970 C 760 780, 560 720, 460 645" fill="none" stroke="url(#hot)" stroke-width="22" stroke-linecap="round" filter="url(#glow)"/>
 <path d="M460 645 l 70 -10 l -20 70 z" fill="#ffd54a" filter="url(#glow)"/>
 <!-- 타들어가는 아래쪽 모서리 -->
 <path d="M230 1010 C 320 980, 380 1060, 470 1030 S 640 1090, 760 1040 L 850 1100 L 230 1100 Z" fill="url(#char)"/>
 <g fill="url(#hot)" filter="url(#glow)" opacity=".95">
  <path d="M300 1010 q12 -80 34 -30 q14 -55 34 -6 q10 55 -30 62 q-40 8 -38 -26z"/>
  <path d="M520 1030 q10 -95 36 -34 q12 -60 36 -4 q10 60 -34 66 q-42 8 -38 -28z"/>
  <path d="M700 1040 q12 -70 32 -24 q12 -48 30 -2 q8 50 -30 56 q-36 6 -32 -30z"/>
 </g>
</g>
"""

# 3) 뭐가 편집됐죠 — 기자회견 마이크 묶음이 불길 속에 서 있고, 정면 마이크 하나만 검게 식어 있다
svg3 = """
<g>
 <!-- 연단 -->
 <path d="M200 1230 L880 1230 L830 1415 L250 1415 Z" fill="#14100e" stroke="#3a2a1c" stroke-width="4"/>
 <!-- 마이크 스탠드들 -->
 <g stroke="#1b1512" stroke-width="16" stroke-linecap="round" fill="none">
  <path d="M400 1230 L440 760"/><path d="M500 1230 L510 720"/><path d="M640 1230 L610 740"/><path d="M720 1230 L680 790"/>
 </g>
 <!-- 마이크 머리: 불붙은 것들 -->
 <g filter="url(#glow)">
  <ellipse cx="444" cy="700" rx="46" ry="66" fill="#ff7a12"/><rect x="424" y="740" width="40" height="70" rx="10" fill="#c4470a"/>
  <ellipse cx="512" cy="660" rx="46" ry="66" fill="#ffa62b"/><rect x="492" y="700" width="40" height="70" rx="10" fill="#c4470a"/>
  <ellipse cx="608" cy="680" rx="46" ry="66" fill="#ff8f1f"/><rect x="588" y="720" width="40" height="70" rx="10" fill="#c4470a"/>
  <ellipse cx="684" cy="730" rx="46" ry="66" fill="#ff6a12"/><rect x="664" y="770" width="40" height="70" rx="10" fill="#c4470a"/>
 </g>
 <!-- 마이크 위 불꽃 -->
 <g fill="url(#hot)" filter="url(#glow)" opacity=".95">
  <path d="M420 640 q20 -140 48 -60 q16 -90 46 -10 q14 90 -44 100 q-70 10 -50 -30z"/>
  <path d="M488 600 q22 -150 50 -70 q18 -95 48 -8 q12 95 -46 104 q-72 10 -52 -26z"/>
  <path d="M584 620 q20 -140 48 -64 q16 -90 46 -12 q14 90 -44 100 q-70 10 -50 -24z"/>
  <path d="M660 670 q20 -130 48 -60 q16 -85 46 -10 q14 85 -44 96 q-70 10 -50 -26z"/>
 </g>
 <!-- 정면 마이크: 식어 검다 -->
 <path d="M560 1230 L556 800" stroke="#0b0908" stroke-width="20" stroke-linecap="round"/>
 <ellipse cx="556" cy="740" rx="60" ry="84" fill="#0b0908" stroke="#3a2a1c" stroke-width="4"/>
 <rect x="530" y="790" width="52" height="90" rx="12" fill="#0b0908" stroke="#3a2a1c" stroke-width="3"/>
 <!-- 마이크 그릴 선 -->
 <g stroke="#2a1c14" stroke-width="3" fill="none"><path d="M510 700 H602 M506 730 H606 M508 760 H604 M516 790 H596"/></g>
</g>
"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1415}, device_scale_factor=1)
    for name, seed, svg in (("01_지운문장", 11, svg1), ("02_날짜", 23, svg2), ("03_회견", 37, svg3)):
        pg.set_content(page(seed, svg), wait_until="load", timeout=120000)
        pg.wait_for_timeout(300)
        out = OUT / f"{name}.png"
        pg.screenshot(path=str(out), full_page=False)
        print(out, out.stat().st_size)
    b.close()
