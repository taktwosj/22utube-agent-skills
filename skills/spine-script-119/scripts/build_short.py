# -*- coding: utf-8 -*-
"""P0_ROOT_shrt_119short_v1 근본에서 정치 쇼츠 CapCut 프로젝트를 만든다.

근본은 읽기만 한다.
- 상황설명: 1~3개. 근본의 3개 프로토타입 기울기·위치를 그대로 돌려 쓴다.
  mood="anger" 면 배경을 빨강으로, 아니면 근본의 초록 그대로.
- 영상·삽화: 배경판 바로 위에 끼운다. 텍스트는 그 위에 남는다.
- Timelines 미러를 본체와 같게 쓴다. 안 그러면 CapCut 이 근본 상태로 되돌린다.
"""
from __future__ import annotations
import copy, hashlib, json, pathlib, re, shutil, subprocess, uuid

from _common import SHORTS_CAPCUT_ROOT, SHORTS_ROOT, root_parser

CR = pathlib.Path(r"C:/Users/arajun/AppData/Local/CapCut/User Data/Projects/com.lveditor.draft")
ROOT = CR / SHORTS_CAPCUT_ROOT
US = 1_000_000
ANGER_BG = "#c81414"
UUID_RE = re.compile(r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}")


def nid():
    return str(uuid.uuid4()).upper()


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True).stdout
    d = json.loads(out.decode("utf-8", "replace"))
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    has_audio = any(s["codec_type"] == "audio" for s in d["streams"])
    raw = d.get("format", {}).get("duration") or v.get("duration")
    dur = int(round(float(raw) * US)) if raw else 0
    return dur, int(v["width"]), int(v["height"]), has_audio


def parse_srt(path):
    rows = []
    for blk in pathlib.Path(path).read_text(encoding="utf-8").strip().split("\n\n"):
        L = [x for x in blk.strip().split("\n") if x.strip()]
        if len(L) < 3:
            continue
        a, b = L[1].split(" --> ")

        def sec(t):
            h, m, rest = t.split(":")
            s, ms = rest.replace(".", ",").split(",")
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
        rows.append((int(sec(a) * US), int(sec(b) * US), " ".join(L[2:]).strip()))
    return rows


class Builder:
    def __init__(self, project_name):
        self.dst = CR / project_name
        if self.dst.exists():
            shutil.rmtree(self.dst)
        shutil.copytree(ROOT, self.dst)
        for f in list(self.dst.rglob("*.bak")) + list(self.dst.glob("template.json")):
            f.unlink()
        self.cpath = self.dst / "draft_content.json"
        self.doc = json.loads(self.cpath.read_text(encoding="utf-8"))
        self.mats = self.doc["materials"]
        self.index = {}
        for bucket, items in self.mats.items():
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict) and "id" in it:
                        self.index[it["id"]] = (bucket, it)
        self.name = project_name
        self._layer = 0

    def text_track(self, needle):
        for tr in self.doc["tracks"]:
            if tr.get("type") != "text":
                continue
            mat = self.index[tr["segments"][0]["material_id"]][1]
            if needle in json.loads(mat["content"])["text"]:
                return tr
        raise KeyError(needle)

    def clone_material(self, mid):
        bucket, obj = self.index[mid]
        new = copy.deepcopy(obj)
        new["id"] = nid()
        self.mats[bucket].append(new)
        self.index[new["id"]] = (bucket, new)
        return new

    def clone_segment(self, seg):
        new = copy.deepcopy(seg)
        new["id"] = nid()
        new["material_id"] = self.clone_material(seg["material_id"])["id"]
        new["extra_material_refs"] = [
            self.clone_material(r)["id"] for r in seg.get("extra_material_refs", []) if r in self.index
        ]
        return new

    def set_text(self, mat, text):
        c = json.loads(mat["content"])
        c["text"] = text
        for st in c.get("styles", []):
            st["range"] = [0, len(text)]
        mat["content"] = json.dumps(c, ensure_ascii=False)
        mat["base_content"] = text
        return mat

    # ---- 텍스트 트랙 ------------------------------------------------------
    def fill_full(self, needle, text):
        tr = self.text_track(needle)
        s = self.clone_segment(tr["segments"][0])
        self.set_text(self.index[s["material_id"]][1], text)
        s["target_timerange"] = {"start": 0, "duration": self.total}
        tr["segments"] = [s]

    def fill_cues(self, needle, cues):
        tr = self.text_track(needle)
        proto = tr["segments"][0]
        segs = []
        for a, b, t in cues:
            s = self.clone_segment(proto)
            self.set_text(self.index[s["material_id"]][1], t)
            s["target_timerange"] = {"start": a, "duration": max(b - a, 100_000)}
            segs.append(s)
        tr["segments"] = segs

    def fill_mentions(self, mentions):
        """mentions = [(start_s, end_s, text, mood)] — 최대 3개. mood: normal | anger"""
        tr = self.text_track("상황설명")
        protos = tr["segments"]          # 근본이 가진 기울기·위치 프로토타입 3개
        segs = []
        for i, (a, b, t, mood) in enumerate(mentions[:3]):
            s = self.clone_segment(protos[i % len(protos)])
            mat = self.index[s["material_id"]][1]
            self.set_text(mat, t)
            if mood == "anger":
                mat["background_color"] = ANGER_BG
                mat["shadow_color"] = "#ff2a2a"
            s["target_timerange"] = {"start": int(a * US), "duration": int((b - a) * US)}
            segs.append(s)
        tr["segments"] = segs

    # ---- 근본 슬롯 --------------------------------------------------------
    def plate_track(self):
        """배경판 트랙 (창이 투명한 jungch.png). 항상 맨 위에 남는다."""
        for tr in self.doc["tracks"]:
            if tr["type"] != "video" or not tr["segments"]:
                continue
            m = self.index[tr["segments"][0]["material_id"]][1]
            if str(m.get("path", "")).lower().endswith("jungch.png"):
                return tr
        raise KeyError("PLATE_TRACK_NOT_FOUND")

    def video_slot_track(self):
        """근본이 가진 영상 슬롯. 위치·크기는 사용자가 잡아 둔 값을 그대로 쓴다."""
        plate = self.plate_track()
        for tr in self.doc["tracks"]:
            if tr["type"] == "video" and tr["segments"] and tr is not plate:
                return tr
        raise KeyError("VIDEO_SLOT_NOT_FOUND")

    def sfx_track(self):
        for tr in self.doc["tracks"]:
            if tr["type"] == "audio" and tr["segments"]:
                return tr
        return None

    def align_sfx(self, starts):
        """키보드 소리를 상황설명 시작에 맞춘다."""
        tr = self.sfx_track()
        if tr is None:
            return
        proto = tr["segments"][0]
        dur = proto["target_timerange"]["duration"]
        segs = []
        for a in starts:
            s = self.clone_segment(proto)
            s["target_timerange"] = {"start": int(a * US), "duration": dur}
            segs.append(s)
        tr["segments"] = segs

    def fill_slot(self, items, scale=None):
        """근본 영상 슬롯 한 트랙에 [삽화 → 클립 → 삽화] 를 이어 붙인다.

        items = [(경로, 시작 us, 길이 us, 소리켬 bool)]
        근본 슬롯의 mp4/png 프로토타입에서 각각 위치·크기를 가져온다.
        """
        tr = self.video_slot_track()
        protos = tr["segments"]
        vid_proto = next((s for s in protos
                          if str(self.index[s["material_id"]][1].get("path", "")).lower().endswith(".mp4")),
                         protos[0])
        img_proto = next((s for s in protos
                          if not str(self.index[s["material_id"]][1].get("path", "")).lower().endswith(".mp4")),
                         protos[-1])
        segs = []
        for path, start, dur, audible in items:
            mat = self.new_media_material(path)
            proto = vid_proto if mat["type"] == "video" else img_proto
            seg = self.clone_segment(proto)
            seg["material_id"] = mat["id"]
            seg["source_timerange"] = {"start": 0, "duration": dur}
            seg["target_timerange"] = {"start": start, "duration": dur}
            if scale is not None and mat["type"] == "video":
                seg["clip"]["scale"] = {"x": scale, "y": scale}
            seg["volume"] = 1.0 if audible else 0.0
            seg["last_nonzero_volume"] = 1.0
            segs.append(seg)
        tr["segments"] = segs
        return tr

    def set_clip(self, path, volume=1.0, scale=None, start=0):
        """근본 영상 슬롯의 위치·크기만 가져오고, 슬롯 자체(영상사전설정 combination)는 버린다.

        슬롯이 CapCut 프리셋 안에 들어 있어 그대로 쓰면 이 PC 에 없는
        Presets/Combination 리소스를 계속 물고 온다.
        """
        slot = self.video_slot_track()
        geo = copy.deepcopy(slot["segments"][0].get("clip", {}))
        pos = self.doc["tracks"].index(slot)
        self.doc["tracks"].remove(slot)

        mat = self.new_media_material(path)
        dur = mat["duration"]
        donor = self.plate_track()["segments"][0]
        seg = self.clone_segment(donor)
        seg["material_id"] = mat["id"]
        seg["source_timerange"] = {"start": 0, "duration": dur}
        seg["target_timerange"] = {"start": start, "duration": dur}
        if geo:
            seg["clip"] = geo
        if scale is not None:
            seg["clip"]["scale"] = {"x": scale, "y": scale}
        seg["volume"] = volume
        seg["last_nonzero_volume"] = volume or 1.0
        tr = {"attribute": 0, "flag": 0, "id": nid(), "is_default_name": True,
              "name": "", "segments": [seg], "type": "video"}
        self.doc["tracks"].insert(pos, tr)
        self._slot_geo = geo
        return tr

    def strip_presets(self):
        """CapCut 프리셋(combination) 잔재를 걷어낸다. 없는 파일을 물고 오는 원인이다."""
        n = 0
        for bucket in ("drafts",):
            if isinstance(self.mats.get(bucket), list):
                n += len(self.mats[bucket])
                self.mats[bucket] = []
        for bucket, items in list(self.mats.items()):
            if not isinstance(items, list):
                continue
            keep = []
            for it in items:
                p = str(it.get("path", "")) if isinstance(it, dict) else ""
                if "Presets/Combination" in p.replace("\\", "/"):
                    n += 1
                    continue
                keep.append(it)
            self.mats[bucket] = keep
        sub = self.dst / "subdraft"
        if sub.is_dir():
            shutil.rmtree(sub)
            sub.mkdir()
        # CapCut 이 앞서 남긴 패치·템플릿 잔재도 같은 유령을 물고 있다
        for junk in list(self.dst.rglob("template.json")) + list(self.dst.rglob("*.bak")):
            junk.unlink()
            n += 1
        for patch in self.dst.rglob("attachment/patch"):
            if patch.is_dir():
                shutil.rmtree(patch)
                n += 1
        return n

    def add_narration(self, items):
        """items = [(wav 경로, 시작 us, 길이 us)] — 새 오디오 트랙에 얹는다."""
        sfx = self.sfx_track()
        proto = sfx["segments"][0]
        proto_mat = self.index[proto["material_id"]][1]
        media_dir = self.dst / "Resources" / "media"
        media_dir.mkdir(parents=True, exist_ok=True)
        segs = []
        for i, (src, start, dur) in enumerate(items, 1):
            local = media_dir / f"nar{i:02d}.wav"
            shutil.copy2(src, local)
            mat = copy.deepcopy(proto_mat)
            mat["id"] = nid()
            mat["path"] = local.as_posix()
            mat["name"] = local.stem
            mat["duration"] = dur
            # 근본 SFX 는 CapCut 클라우드 효과음이다. effect_id 를 물려받으면
            # CapCut 이 나레이션을 그 효과음으로 합쳐 버려 목소리가 안 난다.
            mat["type"] = "extract_music"
            mat["effect_id"] = ""
            mat["category_id"] = ""
            mat["category_name"] = "local"
            mat["app_id"] = 0
            mat["material_id"] = ""
            mat["local_material_id"] = nid()
            mat["music_id"] = nid()
            mat["unique_id"] = nid()
            mat["source_platform"] = 0
            mat["is_copyright"] = False
            mat["is_ugc"] = False
            mat["copyright_limit_type"] = "none"
            mat["check_flag"] = 1
            mat["resource_id"] = ""
            mat["third_resource_id"] = ""
            mat["request_id"] = ""
            mat["search_id"] = ""
            mat["query"] = ""
            mat["source_from"] = ""
            mat["wave_points"] = []
            self.mats["audios"].append(mat)
            self.index[mat["id"]] = ("audios", mat)

            seg = self.clone_segment(proto)
            seg["material_id"] = mat["id"]
            seg["source_timerange"] = {"start": 0, "duration": dur}
            seg["target_timerange"] = {"start": start, "duration": dur}
            seg["volume"] = 1.0
            seg["last_nonzero_volume"] = 1.0
            segs.append(seg)
        tr = {"attribute": 0, "flag": 0, "id": nid(), "is_default_name": True,
              "name": "", "segments": segs, "type": "audio"}
        self.doc["tracks"].append(tr)
        return tr

    def restack(self):
        """배경판이 맨 위에 남도록 영상 계열 render_index 를 다시 매긴다."""
        plate = self.plate_track()
        others = [tr for tr in self.doc["tracks"]
                  if tr["type"] == "video" and tr["segments"] and tr is not plate]
        for i, tr in enumerate(others, start=1):
            tr["render_index"] = i
            for s in tr["segments"]:
                s["render_index"] = i
        top = len(others) + 1
        plate["render_index"] = top
        for s in plate["segments"]:
            s["render_index"] = top

    # ---- 미디어 트랙 ------------------------------------------------------
    def new_media_material(self, path):
        src = pathlib.Path(path)
        d, w, h, has_audio = probe(src)
        media_dir = self.dst / "Resources" / "media"
        media_dir.mkdir(parents=True, exist_ok=True)
        self._media_n = getattr(self, "_media_n", 0) + 1
        local = media_dir / f"m{self._media_n:02d}{src.suffix.lower()}"
        if not local.exists():
            shutil.copy2(src, local)
        proto_seg = self.plate_track()["segments"][0]
        mat = copy.deepcopy(self.index[proto_seg["material_id"]][1])
        mat["id"] = nid()
        mat["path"] = local.as_posix()
        mat["material_name"] = local.name
        mat["width"], mat["height"] = w, h
        mat["duration"] = d if d else 10_800_000_000
        mat["type"] = "video" if has_audio else "photo"
        mat["has_audio"] = has_audio
        mat["material_id"] = ""
        mat["origin_material_id"] = ""
        mat["unique_id"] = hashlib.md5(local.read_bytes()).hexdigest()
        mat["local_material_id"] = nid()
        mat["category_id"] = ""
        mat["category_name"] = "local"
        mat["source_platform"] = 0
        mat["is_copyright"] = False
        mat["team_id"] = ""
        mat["material_url"] = ""
        mat["request_id"] = ""
        self.mats["videos"].append(mat)
        self.index[mat["id"]] = ("videos", mat)
        return mat

    def add_media(self, path, start, dur, scale=1.0, ty=0.0128, volume=1.0):
        mat = self.new_media_material(path)
        donor = self.video_slot_track()["segments"][0]
        seg = self.clone_segment(donor)
        seg["material_id"] = mat["id"]
        seg["source_timerange"] = {"start": 0, "duration": dur}
        seg["target_timerange"] = {"start": start, "duration": dur}
        seg["clip"]["scale"] = {"x": scale, "y": scale}
        seg["clip"]["transform"] = {"x": 0.0, "y": ty}
        seg["clip"]["rotation"] = 0.0
        seg["volume"] = volume
        seg["last_nonzero_volume"] = volume or 1.0
        tr = {"attribute": 0, "flag": 0, "id": nid(), "is_default_name": True,
              "name": "", "segments": [seg], "type": "video"}
        plate = self.plate_track()
        self.doc["tracks"].insert(self.doc["tracks"].index(plate), tr)
        return tr

    def _dead_add_media(self, path, start, dur, scale=1.0, ty=0.0128, volume=1.0):
        src = pathlib.Path(path)
        d, w, h, has_audio = probe(src)

        # 미디어를 프로젝트 안에 영문 이름으로 복사한다. 한글 경로 위험을 없애고
        # 프로젝트만 옮겨도 안 깨지게 한다.
        media_dir = self.dst / "Resources" / "media"
        media_dir.mkdir(parents=True, exist_ok=True)
        self._media_n = getattr(self, "_media_n", 0) + 1
        local = media_dir / f"m{self._media_n:02d}{src.suffix.lower()}"
        if not local.exists():
            shutil.copy2(src, local)

        proto_seg = self.doc["tracks"][0]["segments"][0]
        mat = copy.deepcopy(self.index[proto_seg["material_id"]][1])
        mat["id"] = nid()
        mat["path"] = local.as_posix()
        mat["material_name"] = local.name
        mat["width"], mat["height"] = w, h
        mat["duration"] = d if d else 10_800_000_000
        mat["type"] = "video" if has_audio else "photo"
        mat["has_audio"] = has_audio
        # 근본 배경판은 CapCut 클라우드 브랜드 자산이다. 그 신원을 물려받으면
        # CapCut 이 새 미디어를 같은 자산으로 합쳐 버리고 경로가 배경판으로 바뀐다.
        mat["material_id"] = ""
        mat["origin_material_id"] = ""
        mat["unique_id"] = hashlib.md5(local.read_bytes()).hexdigest()
        mat["local_material_id"] = nid()
        mat["category_id"] = ""
        mat["category_name"] = "local"
        mat["source_platform"] = 0
        mat["is_copyright"] = False
        mat["team_id"] = ""
        mat["material_url"] = ""
        mat["request_id"] = ""
        self.mats["videos"].append(mat)
        self.index[mat["id"]] = ("videos", mat)

        seg = self.clone_segment(proto_seg)
        seg["material_id"] = mat["id"]
        seg["source_timerange"] = {"start": 0, "duration": dur}
        seg["target_timerange"] = {"start": start, "duration": dur}
        seg["clip"]["scale"] = {"x": scale, "y": scale}
        seg["clip"]["transform"] = {"x": 0.0, "y": ty}
        seg["clip"]["rotation"] = 0.0
        seg["volume"] = volume
        seg["last_nonzero_volume"] = volume or 1.0
        self._layer += 1
        seg["render_index"] = self._layer
        tr = {"attribute": 0, "flag": 0, "id": nid(), "is_default_name": True,
              "name": "", "segments": [seg], "type": "video",
              "render_index": self._layer}
        # 배경판 바로 위에 끼운다
        self.doc["tracks"].insert(self._layer, tr)
        return tr

    # ---- 마무리 ----------------------------------------------------------
    def repoint_root_assets(self):
        old, new = ROOT.as_posix(), self.dst.as_posix()
        n = 0
        for bucket, items in self.mats.items():
            if not isinstance(items, list):
                continue
            for it in items:
                p = it.get("path") if isinstance(it, dict) else None
                if isinstance(p, str) and p.replace("\\", "/").startswith(old):
                    it["path"] = p.replace("\\", "/").replace(old, new, 1)
                    n += 1
        # 폰트 경로는 content 문자열 안에 있다
        raw = json.dumps(self.doc, ensure_ascii=False)
        n += raw.count(old)
        self.doc = json.loads(raw.replace(old, new))
        self.mats = self.doc["materials"]
        return n

    def prune_orphans(self):
        used = set()
        for tr in self.doc["tracks"]:
            for s in tr.get("segments", []):
                used.add(s["material_id"])
                used.update(s.get("extra_material_refs", []))
        removed = 0
        for bucket, items in self.mats.items():
            if not isinstance(items, list):
                continue
            keep = [it for it in items
                    if not isinstance(it, dict) or "id" not in it or it["id"] in used]
            removed += len(items) - len(keep)
            self.mats[bucket] = keep
        return removed

    def finish(self):
        self.doc["duration"] = self.total
        self.doc["name"] = self.name
        self.doc["path"] = self.dst.as_posix()
        bg = self.plate_track()["segments"][0]
        bg["target_timerange"] = {"start": 0, "duration": self.total}
        bg["source_timerange"] = {"start": 0, "duration": self.total}
        # 키보드 SFX 는 align_sfx 가 상황설명에 맞춰 놓는다

        self.cpath.write_text(json.dumps(self.doc, ensure_ascii=False), encoding="utf-8")

        # 근본에서 물려받은 모든 uuid 를 새로 발급한다.
        # 근본 프로젝트가 같은 폴더에 남아 있어 id 가 겹치면 CapCut 이 둘을 헷갈린다.
        old_timeline = self.doc["id"]
        files = [p for p in self.dst.rglob("*") if p.is_file() and p.suffix.lower() in {".json", ".tmp"}]
        texts = {}
        ids = set()
        for p in files:
            try:
                t = p.read_text(encoding="utf-8")
            except Exception:
                continue
            texts[p] = t
            ids.update(UUID_RE.findall(t))
        id_map = {old: nid() for old in ids}
        new_timeline = id_map.get(old_timeline)
        if not new_timeline:
            raise RuntimeError("TIMELINE_ID_REMAP_FAILED")

        def swap(t):
            return UUID_RE.sub(lambda m: id_map.get(m.group(0), m.group(0)), t)

        tl = self.dst / "Timelines"
        old_dir = tl / old_timeline
        new_dir = tl / new_timeline
        if old_dir.is_dir():
            old_dir.rename(new_dir)
        new_dir.mkdir(parents=True, exist_ok=True)
        for p, t in texts.items():
            target = p
            if old_dir in p.parents:
                target = new_dir / p.relative_to(old_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(swap(t), encoding="utf-8")

        # 정본 네 벌을 모두 같은 내용으로 쓴다. template-2.tmp 를 빠뜨리면
        # CapCut 이 타임라인을 건드리는 순간 근본 상태로 되돌린다.
        self.doc = json.loads(swap(json.dumps(self.doc, ensure_ascii=False)))
        payload = json.dumps(self.doc, ensure_ascii=False)
        for path in (self.dst / "draft_content.json", self.dst / "template-2.tmp",
                     new_dir / "draft_content.json", new_dir / "template-2.tmp"):
            path.write_text(payload, encoding="utf-8")

        meta = self.dst / "draft_meta_info.json"
        m = json.loads(meta.read_text(encoding="utf-8"))
        m["draft_name"] = self.name
        m["draft_fold_path"] = self.dst.as_posix()
        m["tm_duration"] = self.total
        meta.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")

        lay = self.dst / "timeline_layout.json"
        if lay.is_file():
            L = json.loads(lay.read_text(encoding="utf-8"))
            for dock in L.get("dockItems", []):
                dock["timelineIds"] = [new_timeline]
            lay.write_text(json.dumps(L, ensure_ascii=False), encoding="utf-8")

        for junk in list(self.dst.rglob("*.bak")) + list(self.dst.glob("template.json")):
            junk.unlink()
        self.timeline_id = new_timeline
        return self.dst


def wav_us(p):
    import wave
    with wave.open(str(p)) as w:
        return int(round(w.getnframes() / w.getframerate() * US))


def build(project_name, clip, srt8, t1, t2, credit, mentions,
          image=None, scale=None, head=(), tail=(), pad=1.0):
    """head/tail = [(wav 경로, 자막 문구)] — 롱폼 나레이션을 앞뒤에 붙인다.
    나레이션이 흐르는 동안 삽화를 띄우고, 끝나면 pad 초 쉬어 자막을 마무리한다."""
    b = Builder(project_name)
    clip_dur = probe(clip)[0]
    head_list = [(pathlib.Path(w), t, wav_us(w)) for w, t in head]
    tail_list = [(pathlib.Path(w), t, wav_us(w)) for w, t in tail]
    pad_us = int(pad * US)
    head_voice = sum(d for _, _, d in head_list)
    tail_voice = sum(d for _, _, d in tail_list)
    head_dur = head_voice + (pad_us if head_voice else 0)   # 여백 포함
    tail_dur = tail_voice + (pad_us if tail_voice else 0)
    b.total = head_dur + clip_dur + tail_dur

    b.fill_full("출처", credit)
    b.fill_full("T1", t1)
    b.fill_full("T2", t2)

    off = head_dur / US
    b.fill_mentions([(a + off, c + off, t, m) for a, c, t, m in mentions])
    cues = [(a + head_dur, c + head_dur, t) for a, c, t in parse_srt(srt8)]
    # 나레이션 자막도 본편 자막처럼 여덟 자 안팎으로 쪼개 흘린다
    def chunks(text, limit=8):
        out, cur_ = [], ""
        for w in text.split():
            while len(w) > limit:
                if cur_:
                    out.append(cur_)
                    cur_ = ""
                out.append(w[:limit])
                w = w[limit:]
            cand = (cur_ + " " + w).strip()
            if len(cand) <= limit:
                cur_ = cand
            else:
                if cur_:
                    out.append(cur_)
                cur_ = w
        if cur_:
            out.append(cur_)
        return out

    def spread(text, start, dur):
        cs = chunks(text)
        if not cs:
            return []
        weights = [max(len(c), 1) for c in cs]
        tot = sum(weights)
        rows, pos = [], start
        for c, w in zip(cs, weights):
            step = max(int(dur * w / tot), 200_000)
            rows.append((pos, pos + step, c))
            pos += step
        return rows

    # 자막은 음성보다 pad 만큼 더 남겨 문장을 마무리한다
    nar_cues = []
    cur = 0
    for i, (_, t, d) in enumerate(head_list):
        extra = pad_us if i == len(head_list) - 1 else 0
        nar_cues += spread(t, cur, d + extra)
        cur += d
    cur = head_dur + clip_dur
    for i, (_, t, d) in enumerate(tail_list):
        extra = pad_us if i == len(tail_list) - 1 else 0
        nar_cues += spread(t, cur, d + extra)
        cur += d
    b.fill_cues("기본텍스트", nar_cues + cues)
    b.align_sfx([m[0] + off for m in mentions[:3]])

    # 한 트랙에 [삽화 → 본편 → 삽화] 로 이어 붙인다. 겹치지 않는다.
    slot = []
    if image and head_dur:
        slot.append((image, 0, head_dur, False))
    slot.append((clip, head_dur, clip_dur, True))
    if image and tail_dur:
        slot.append((image, head_dur + clip_dur, tail_dur, False))
    b.fill_slot(slot, scale=scale)

    # 나레이션 오디오
    nar = []
    cur = 0
    for w, _, d in head_list:
        nar.append((w, cur, d))
        cur += d
    cur = head_dur + clip_dur
    for w, _, d in tail_list:
        nar.append((w, cur, d))
        cur += d
    if nar:
        b.add_narration(nar)

    b.doc["tracks"] = [tr for tr in b.doc["tracks"] if tr.get("segments")]
    b.restack()
    print("프리셋 잔재 제거", b.strip_presets(), "건")
    b.repoint_root_assets()
    b.prune_orphans()
    out = b.finish()
    print(f"프로젝트: {out}")
    print(f"길이: {b.total/US:.1f}초  (나레이션 앞 {head_dur/US:.1f} + 본편 {clip_dur/US:.1f} "
          f"+ 나레이션 뒤 {tail_dur/US:.1f}) / 트랙: {len(b.doc['tracks'])}")
    return out


def narration(root, ids):
    """롱폼 나레이션 wav 를 그대로 쓴다. 쇼츠용으로 새로 합성하지 않는다."""
    folder = pathlib.Path(root) / "narration"
    out = []
    for name in ids:
        wav = folder / f"{name}.wav"
        txt = folder / f"{name}.txt"
        if not wav.is_file():
            raise SystemExit(f"SHORT_NARRATION_WAV_MISSING: {wav}")
        if not txt.is_file():
            raise SystemExit(f"SHORT_NARRATION_TEXT_MISSING: {txt}")
        out.append((wav, txt.read_text(encoding="utf-8").strip()))
    return out


def main():
    parser = root_parser("잠근 쇼츠를 CapCut 프로젝트로 조립한다")
    parser.add_argument("--only", help="이 슬러그만 만든다")
    parser.add_argument("--pad", type=float, default=1.0,
                        help="나레이션이 끝난 뒤 자막을 마무리할 여백 초")
    args = parser.parse_args()
    root = args.root
    if root is None:
        raise SystemExit("ROOT_REQUIRED: --root 또는 SPINE_EPISODE_ROOT")
    if not ROOT.is_dir():
        raise SystemExit(f"SHORT_CAPCUT_ROOT_MISSING: {ROOT}")

    path = pathlib.Path(root) / "work" / "shorts.json"
    if not path.is_file():
        raise SystemExit(f"SHORTS_JSON_MISSING: {path} — mark_shorts.py 를 먼저 돌린다")
    data = json.loads(path.read_text(encoding="utf-8"))
    shorts_dir = SHORTS_ROOT / data["episode_id"]

    ok = fail = 0
    for row in data["shorts"]:
        if args.only and row["slug"] != args.only:
            continue
        slug = row["slug"]
        folder = shorts_dir / slug
        clip = folder / f"{slug}.mp4"
        srt8 = folder / f"{slug}_8자.srt"
        for needed in (clip, srt8):
            if not needed.is_file():
                raise SystemExit(f"SHORT_CUT_MISSING: {needed} — cut_shorts.py 를 먼저 돌린다")
        art = pathlib.Path(row["art_path"])
        if not art.is_file():
            raise SystemExit(f"SHORT_ART_MISSING: {art} — gen_short_art.py 로 요청한다")
        try:
            build(project_name=row["project_name"], clip=clip, srt8=srt8,
                  t1=row["t1"], t2=row["t2"], credit=row["credit"],
                  mentions=[(a, b, t, m) for a, b, t, m in row["mentions"]],
                  image=art, scale=row.get("scale"),
                  head=narration(root, row["head_narration"]),
                  tail=narration(root, row["tail_narration"]),
                  pad=args.pad)
            ok += 1
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001 — 한 건 실패해도 나머지는 만든다
            print(f"실패 {row['project_name']} — {exc}")
            fail += 1
    print(f"완료 {ok} / 실패 {fail}")


if __name__ == "__main__":
    main()
