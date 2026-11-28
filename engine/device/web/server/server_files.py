from core import *

from engine.file import Cache
from engine.lib import ImageLib
from engine.device.web import *

from aiohttp import web
from engine.device.web.server.server_base import GameServerBase

import asyncio
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path
from threading import RLock
from urllib.parse import urlsplit

CATEGORY_NAME = "WEB"
_KO_PACK = Path('./ko-local/pack.zip')
_KO_LOCK = RLock()
_KO_ZIP = None
_KO_STAT = None
_KO_INDEX = {}
_KO_LIMIT = 256 * 1024 * 1024
_KO_ID = re.compile(r'^[0-9]{5}[a-z]?

class GameServerFiles(GameServerBase):

    def ImageResponse(self, card_id: str, image_bytes: bytes) -> web.Response:
        headers = dict(self.HeaderCache)
        retry_seconds = Cache.GetImageRetrySeconds(card_id)
        image_state = Cache.GetImageState(card_id)
        headers['X-Card-Image-State'] = image_state
        if image_state == 'pending':
            retry_seconds = 1
        if retry_seconds is not None:
            # A valid placeholder is still a failed download. Let the client
            # replace it automatically, and never cache it as finished artwork.
            headers['X-Card-Image-Retry-After'] = str(retry_seconds)
            headers['Cache-Control'] = 'no-store'
        return web.Response(
            body=image_bytes,
            content_type=ImageLib.GetContentType(image_bytes),
            headers=headers,
        )

    async def handle_marvel(self, request: web.Request) -> web.StreamResponse:
        if request.query_string == '':
            return self.ReadFile('./public/main.html')
        else:
            return self.ReadFile('./public/marvel.html')

    async def handle_players_404(self, request: web.Request) -> web.StreamResponse:
        player = request.match_info.get('player')
        return web.Response(text=f"Please visiting /?p={player}", status=404)

    def handle_sets_image(self, request: web.Request) -> web.StreamResponse:
        file_path = request.path

        image_bytes = Cache.LoadImage(file_path)

        return self.ImageResponse(file_path, image_bytes)

    async def get_ko_pack(self, request: web.Request) -> web.Response:
        try:
            with _KO_LOCK:
                return web.json_response(_ko_response(_ko_open()), headers={'Cache-Control': 'no-store'})
        except (OSError, ValueError, KeyError, zipfile.BadZipFile):
            return web.json_response({'error': '한글팩을 다시 설치해 주세요.'}, status=400)

    async def import_ko_pack(self, request: web.Request) -> web.Response:
        origin = urlsplit(request.headers.get('Origin', ''))
        if origin.scheme not in ('http', 'https') or origin.netloc != request.host or origin.hostname not in ('127.0.0.1', 'localhost', '::1') or request.remote not in ('127.0.0.1', '::1'):
            return web.json_response({'error': '기기에서 직접 설치해 주세요.'}, status=403)
        if request.content_length is not None and request.content_length > _KO_LIMIT:
            return web.json_response({'error': '한글팩이 너무 큽니다.'}, status=413)
        _KO_PACK.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=_KO_PACK.parent, suffix='.tmp', delete=False) as file:
                temporary = file.name
                size = 0
                async for chunk in request.content.iter_chunked(256 * 1024):
                    size += len(chunk)
                    if size > _KO_LIMIT:
                        raise ValueError('한글팩이 너무 큽니다.')
                    file.write(chunk)
            index = await asyncio.to_thread(_ko_install, temporary)
            return web.json_response(_ko_response(index), headers={'Cache-Control': 'no-store'})
        except (OSError, ValueError, KeyError, TypeError, AttributeError, zipfile.BadZipFile) as exc:
            return web.json_response({'error': str(exc)}, status=400)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

    def handle_image_request(self, request: web.Request) -> web.StreamResponse:
        # file_path = request.match_info['path']
        file_path = request.path
        file_path = file_path.split("/")[-1]

        # The installed Korean pack overrides only exact card faces; existing
        # managed images and original engine card definitions remain untouched.
        korean = _ko_image(file_path)
        if korean is not None:
            return web.Response(body=korean, content_type='image/avif', headers={'Cache-Control': 'no-store', 'X-Card-Image-State': 'ready'})
        image_bytes = Cache.LoadImage(file_path)
        image_size = len(image_bytes)

        self.device_manager.AddSize("Image", image_size)

        return self.ImageResponse(file_path, image_bytes)

    @override
    def __init__(self) -> None:
        super().__init__()

        self.AddDefaultGet()
        self.AddAwaitGetSecurity('/get_ko_pack', self.get_ko_pack)
        self.AddPostSecurity('/import_ko_pack', self.import_ko_pack)

        # Home branding is bundled artwork, not a card ID. Register exact
        # paths before the catch-all card image handler.
        async def home_logo(request: web.Request) -> web.StreamResponse:
            response = self.ReadFile('./public/images/home/champions.png')
            response.headers['Cache-Control'] = 'no-store'
            return response

        async def home_backdrop(request: web.Request) -> web.StreamResponse:
            response = self.ReadFile('./public/images/home/doom.webp')
            response.headers['Cache-Control'] = 'no-store'
            return response

        self.AddAwaitGetSecurity('/public/images/home/champions.png', home_logo)
        self.AddAwaitGetSecurity('/public/images/home/doom.webp', home_backdrop)

        self.AddAwaitGetSecurity('/', self.handle_marvel)
        self.AddAwaitGetSecurity(r'/p={player:\d+}', self.handle_players_404)
        self.AddAwaitGetSecurity('/watch', self.handle_marvel)

        self.AddNonAwaitGetSecurity(r'/sets/{path:.+}', self.handle_sets_image)
        self.AddNonAwaitGetSecurity(r'/{path:.+}', self.handle_image_request)

)

def _ko_open():
    """Call with the lock held. Only read the locally validated index."""
    global _KO_ZIP, _KO_STAT, _KO_INDEX
    stat = _KO_PACK.stat() if _KO_PACK.is_file() else None
    stamp = (stat.st_mtime_ns, stat.st_size) if stat else None
    if stamp == _KO_STAT:
        return _KO_INDEX
    if _KO_ZIP is not None:
        _KO_ZIP.close()
    _KO_ZIP = None
    _KO_INDEX = {}
    _KO_STAT = None
    if stamp:
        archive = zipfile.ZipFile(_KO_PACK)
        try:
            index = json.loads(archive.read('installed.json'))
        except Exception:
            archive.close()
            raise
        _KO_ZIP = archive
        _KO_INDEX = index
        _KO_STAT = stamp
    return _KO_INDEX

def _ko_image(card_id):
    if not _KO_ID.fullmatch(card_id):
        return None
    try:
        with _KO_LOCK:
            index = _ko_open()
            if not index.get('use_images', True) or card_id not in index.get('images', {}):
                return None
            return _KO_ZIP.read('images/' + card_id + '.avif')
    except (OSError, ValueError, KeyError, zipfile.BadZipFile):
        return None

def _ko_install(temporary):
    """Validate data, never extract filenames or execute bundled scripts."""
    from engine.config import ConfigVariables
    from engine.lib import Json
    catalog = Json.Load(ConfigVariables.File('cards_json_file').value)
    allowed = {}
    for group in catalog.values():
        if isinstance(group, list):
            for card in group:
                if isinstance(card, dict) and isinstance(card.get('card_id'), str):
                    allowed[card['card_id']] = card
    if not allowed:
        raise ValueError('게임 카드 목록이 비어 있습니다.')
    def norm(value):
        return re.sub(r'[^a-z0-9]', '', value.lower())
    with zipfile.ZipFile(temporary, 'a') as archive:
        members = archive.infolist()
        if len(members) > 10000 or len({m.filename for m in members}) != len(members):
            raise ValueError('잘못된 파일 목록')
        if sum(m.file_size for m in members) > _KO_LIMIT:
            raise ValueError('한글팩 용량 제한 초과')
        if any(m.filename != 'manifest.json' and not re.fullmatch(r'images/[0-9]{5}[a-z]?\.avif', m.filename) for m in members):
            raise ValueError('지원하지 않는 한글팩 파일')
        if archive.getinfo('manifest.json').file_size > 12 * 1024 * 1024:
            raise ValueError('번역 데이터가 너무 큽니다.')
        data = json.loads(archive.read('manifest.json'))
        if data.get('format') != 'marvel-ko-pack-v1' or not isinstance(data.get('cards'), dict) or not isinstance(data.get('images'), dict):
            raise ValueError('지원하지 않는 한글팩 형식')
        rows, images, mismatches = {}, {}, []
        for cid, row in data['cards'].items():
            if not _KO_ID.fullmatch(cid) or cid not in allowed or not isinstance(row, dict):
                continue
            name, english, body = row.get('name'), row.get('en'), row.get('text')
            if not all(isinstance(v, str) for v in (name, english, body)) or not name.strip() or not english.strip() or len(name) > 300 or len(english) > 300 or len(body) > 15000:
                continue
            original = allowed[cid].get('name') or allowed[cid].get('card_name')
            # Exact ID is mandatory. Compare English names where the catalogue supplies one.
            if isinstance(original, str) and re.search('[A-Za-z]', original) and norm(original) != norm(english):
                mismatches.append(cid)
                continue
            if row.get('type') in {'hero','alter','ally','minion','villain'}:
                name = english.lstrip('* ').strip()
            rows[cid] = {'name': name, 'text': body}
            if cid not in data['images']:
                continue
            try:
                member = archive.getinfo('images/' + cid + '.avif')
                if member.file_size < 16 or member.file_size > 2 * 1024 * 1024:
                    continue
                image = archive.read(member)
                if image[4:8] == b'ftyp' and image[8:12] in (b'avif', b'avis'):
                    images[cid] = True
            except (KeyError, OSError, zipfile.BadZipFile):
                continue
        if not rows:
            raise ValueError('일치하는 카드가 없습니다.')
        index = {'cards': rows, 'images': images, 'mismatches': mismatches, 'source_count': len(data['cards'])}
        archive.writestr('installed.json', json.dumps(index, ensure_ascii=False, separators=(',', ':')), compress_type=zipfile.ZIP_DEFLATED)
    global _KO_ZIP, _KO_STAT, _KO_INDEX
    with _KO_LOCK:
        if _KO_ZIP is not None:
            _KO_ZIP.close()
        _KO_ZIP = None
        _KO_STAT = None
        _KO_INDEX = {}
        os.replace(temporary, _KO_PACK)
    return index

def _ko_response(index):
    return {'cards': index.get('cards', {}), 'image_count': len(index.get('images', {})),
            'mismatches': index.get('mismatches', []), 'source_count': index.get('source_count', 0)}


class GameServerFiles(GameServerBase):

    def ImageResponse(self, card_id: str, image_bytes: bytes) -> web.Response:
        headers = dict(self.HeaderCache)
        retry_seconds = Cache.GetImageRetrySeconds(card_id)
        image_state = Cache.GetImageState(card_id)
        headers['X-Card-Image-State'] = image_state
        if image_state == 'pending':
            retry_seconds = 1
        if retry_seconds is not None:
            # A valid placeholder is still a failed download. Let the client
            # replace it automatically, and never cache it as finished artwork.
            headers['X-Card-Image-Retry-After'] = str(retry_seconds)
            headers['Cache-Control'] = 'no-store'
        return web.Response(
            body=image_bytes,
            content_type=ImageLib.GetContentType(image_bytes),
            headers=headers,
        )

    async def handle_marvel(self, request: web.Request) -> web.StreamResponse:
        if request.query_string == '':
            return self.ReadFile('./public/main.html')
        else:
            return self.ReadFile('./public/marvel.html')

    async def handle_players_404(self, request: web.Request) -> web.StreamResponse:
        player = request.match_info.get('player')
        return web.Response(text=f"Please visiting /?p={player}", status=404)

    def handle_sets_image(self, request: web.Request) -> web.StreamResponse:
        file_path = request.path

        image_bytes = Cache.LoadImage(file_path)

        return self.ImageResponse(file_path, image_bytes)

    def handle_image_request(self, request: web.Request) -> web.StreamResponse:
        # file_path = request.match_info['path']
        file_path = request.path
        file_path = file_path.split("/")[-1]

        image_bytes = Cache.LoadImage(file_path)
        image_size = len(image_bytes)

        self.device_manager.AddSize("Image", image_size)

        return self.ImageResponse(file_path, image_bytes)

    @override
    def __init__(self) -> None:
        super().__init__()

        self.AddDefaultGet()

        # Home branding is bundled artwork, not a card ID. Register exact
        # paths before the catch-all card image handler.
        async def home_logo(request: web.Request) -> web.StreamResponse:
            response = self.ReadFile('./public/images/home/champions.png')
            response.headers['Cache-Control'] = 'no-store'
            return response

        async def home_backdrop(request: web.Request) -> web.StreamResponse:
            response = self.ReadFile('./public/images/home/doom.webp')
            response.headers['Cache-Control'] = 'no-store'
            return response

        self.AddAwaitGetSecurity('/public/images/home/champions.png', home_logo)
        self.AddAwaitGetSecurity('/public/images/home/doom.webp', home_backdrop)

        self.AddAwaitGetSecurity('/', self.handle_marvel)
        self.AddAwaitGetSecurity(r'/p={player:\d+}', self.handle_players_404)
        self.AddAwaitGetSecurity('/watch', self.handle_marvel)

        self.AddNonAwaitGetSecurity(r'/sets/{path:.+}', self.handle_sets_image)
        self.AddNonAwaitGetSecurity(r'/{path:.+}', self.handle_image_request)

