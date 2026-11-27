"""Generate Korean translations for a personal offline build; do not commit output."""
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
REV = "055b6b427854287943ffa025adf8c39b44494fbf"
FILES = [
  {
    "path": "translations/ko/pack/core.json",
    "prefix": "01",
    "sha": "4b7121e7c9ab6a64a32a611a645e786bb0088df0"
  },
  {
    "path": "translations/ko/pack/core_encounter.json",
    "prefix": "01",
    "sha": "cc071e0cc29910df62d4058c5215e57948beea3b"
  },
  {
    "path": "translations/ko/pack/gob_encounter.json",
    "prefix": "02",
    "sha": "f64956a463e1cdbc3c84c0f56ce3393d49f881ba"
  },
  {
    "path": "translations/ko/pack/cap.json",
    "prefix": "03",
    "sha": "1af4935a04d6c1e47512bb41c003f91da8269b10"
  },
  {
    "path": "translations/ko/pack/cap_encounter.json",
    "prefix": "03",
    "sha": "c2545c2a788ced67e263fa9658aae6f5f655afad"
  },
  {
    "path": "translations/ko/pack/trors.json",
    "prefix": "04",
    "sha": "b97b5ce1a417bb4d93abda49779f2e072aae28cb"
  },
  {
    "path": "translations/ko/pack/trors_encounter.json",
    "prefix": "04",
    "sha": "a5cb9d1c0ccb7698a2ad61946596f9c226c4e654"
  },
  {
    "path": "translations/ko/pack/msm.json",
    "prefix": "05",
    "sha": "6fc3075e870881955edd280478601588bf331d42"
  },
  {
    "path": "translations/ko/pack/msm_encounter.json",
    "prefix": "05",
    "sha": "8b5837b2fd065e18312b0a89245394fec6edcc4b"
  },
  {
    "path": "translations/ko/pack/thor.json",
    "prefix": "06",
    "sha": "1c5a1b1d96d74efa34466bc40f8fcd7f87b0f4c8"
  },
  {
    "path": "translations/ko/pack/thor_encounter.json",
    "prefix": "06",
    "sha": "e797ee89974899bece39596a166d0c9b1bf6e7df"
  },
  {
    "path": "translations/ko/pack/twc_encounter.json",
    "prefix": "07",
    "sha": "ab095b255e274624a40cba06f19cd9e98dae6593"
  },
  {
    "path": "translations/ko/pack/bkw.json",
    "prefix": "08",
    "sha": "5e1b766de5cd2e3fc96e0b15a748fd368488858f"
  },
  {
    "path": "translations/ko/pack/bkw_encounter.json",
    "prefix": "08",
    "sha": "1bb4b7c82993bc07d75e7e69239ffc0253dd1f6b"
  },
  {
    "path": "translations/ko/pack/drs.json",
    "prefix": "09",
    "sha": "a3f554fdc535a0c244e4baa79942c41f20ff3125"
  },
  {
    "path": "translations/ko/pack/drs_encounter.json",
    "prefix": "09",
    "sha": "4fd80de0e549c9f8679d36c572f45864bdfd4f0e"
  },
  {
    "path": "translations/ko/pack/hlk.json",
    "prefix": "10",
    "sha": "1e17bcc7ff65b13b3d1b5891f208a130ad8d352c"
  },
  {
    "path": "translations/ko/pack/hlk_encounter.json",
    "prefix": "10",
    "sha": "89309223aeb89534cc10508c5296c2ec5a6c2950"
  },
  {
    "path": "translations/ko/pack/toafk_encounter.json",
    "prefix": "11",
    "sha": "6a8ae79ea599f2e33e99ecfa161333c1f31944c0"
  },
  {
    "path": "translations/ko/pack/ant.json",
    "prefix": "12",
    "sha": "8ee91d4a0b8de3b50022a877ab8dae6799fa48d4"
  },
  {
    "path": "translations/ko/pack/ant_encounter.json",
    "prefix": "12",
    "sha": "3f4c8edbf41bf0d764b2f41c01e98d3113bfc111"
  },
  {
    "path": "translations/ko/pack/wsp.json",
    "prefix": "13",
    "sha": "083be5fb595a056f044826e0f739474c53d6bbd4"
  },
  {
    "path": "translations/ko/pack/wsp_encounter.json",
    "prefix": "13",
    "sha": "30b24d6fa54e73f6eb59f66456308c102f89ea36"
  },
  {
    "path": "translations/ko/pack/qsv.json",
    "prefix": "14",
    "sha": "1fecd12af9bd643aead7d5787467b5654b726319"
  },
  {
    "path": "translations/ko/pack/qsv_encounter.json",
    "prefix": "14",
    "sha": "984311ef4dbfaabd5ec5960622861bd9216691f0"
  },
  {
    "path": "translations/ko/pack/scw.json",
    "prefix": "15",
    "sha": "4c74e9c0cbdb0443ae3327d9da9a57915139cbd9"
  },
  {
    "path": "translations/ko/pack/scw_encounter.json",
    "prefix": "15",
    "sha": "7859fb70c607ac341bfdb6f5f42ea37adac56c44"
  }
]
OUT = ROOT / "public/js/marvel/ko-bundled.ts"
SYMBOLS = {"energy":"에너지","mental":"정신력","physical":"물리력","wild":"만능",
           "per_hero":"플레이어당","boost":"강화 아이콘","star":"★","cost":"비용",
           "acceleration":"가속","amplify":"증폭","crisis":"위기","hazard":"수렁",
           "unique":"고유","per_group":"그룹당"}
HANGUL = re.compile(r"[가-힣]")
ID = re.compile(r"\d{5}[a-z]?")

def plain(value):
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"<hr\s*/?>", "\n────\n", value, flags=re.I)
    value = re.sub(r"<[^>]*>", "", value)
    value = re.sub(r"\[\[([^\]]+)\]\]", r"\1", value)
    for old, new in {"&nbsp;":" ","&amp;":"＆","&quot;":"”","&apos;":"’","&lt;":"＜","&gt;":"＞"}.items():
        value = value.replace(old,new)
    value = re.sub(r"\[([a-z_]+)\]",lambda m: SYMBOLS.get(m[1],m[0]),value)
    return value.translate(str.maketrans("<>&","＜＞＆")).strip()

def fetch(row):
    url = "https://raw.githubusercontent.com/zzorba/marvelsdb-json-data/"+REV+"/"+row["path"]
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent":"Marvel-personal-Korean-build"}),timeout=30) as res:
                data = res.read()
            sha = hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
            if sha != row["sha"]:
                raise ValueError("Source blob mismatch: "+row["path"])
            return json.loads(data)
        except (OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(2*(attempt+1))

def main():
    catalog = json.loads((ROOT/"data/cards.json").read_text(encoding="utf-8"))
    ids = {c["card_id"] for group in catalog.values() if isinstance(group,list)
           for c in group if isinstance(c,dict) and isinstance(c.get("card_id"),str)}
    if not ids:
        raise ValueError("No engine card IDs")
    cards = {}
    for row in FILES:
        count = 0
        for card in fetch(row):
            code, name, text = card.get("code"), card.get("name"), card.get("text")
            if not isinstance(code,str) or not ID.fullmatch(code) or not code.startswith(row["prefix"]) or code not in ids:
                continue
            if not isinstance(name,str) or not isinstance(text,str) or not HANGUL.search(text):
                continue
            cleaned = plain(text)
            if not HANGUL.search(cleaned) or len(cleaned)>15000:
                continue
            name = plain(name).translate(str.maketrans({"'":"’",'"':"”","\r":" ","\n":" ","\\":" "}))
            cards[code] = {"name":name,"text":cleaned}
            count += 1
        print(row["path"], count)
    if len(cards)<250 or "03001a" not in cards:
        raise ValueError("Unexpectedly incomplete Korean dataset")
    output = "// Generated personal-use module. See prepare_ko.py and ATTRIBUTION.md.\n"
    output += "export const bundledKo: Record<string,{name:string;text:string}> = "
    output += json.dumps(cards,ensure_ascii=False,sort_keys=True,indent=2)+";\n"
    OUT.write_text(output,encoding="utf-8")
    print("Bundled Korean cards:",len(cards))

if __name__ == "__main__":
    main()
