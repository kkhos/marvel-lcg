export interface ArtworkStatus {
    state: string;
    ready: boolean;
    can_play: boolean;
    completed_cards: number;
    total_cards: number;
    completed_packs: number;
    total_packs: number;
    downloaded_bytes: number;
    total_bytes: number;
    installed_bytes: number;
    required_bytes: number;
    required_storage_bytes: number;
    total_installed_bytes: number;
    folder: string;
    error?: string;
    errors?: Record<string, string>;
}

export function formatArtworkBytes(bytes: number): string {
    if (!Number.isFinite(bytes) || bytes < 0) return 'Not available';
    const unit = bytes >= 1024 ** 3 ? 'GiB' : bytes >= 1024 ** 2 ? 'MiB' : 'KiB';
    const divisor = unit === 'GiB' ? 1024 ** 3 : unit === 'MiB' ? 1024 ** 2 : 1024;
    return `${(bytes / divisor).toFixed(1)} ${unit} (${bytes.toLocaleString()} bytes)`;
}

export function artworkDestination(raw: string | null, origin: string): string {
    if (!raw) return '/main';
    let destination: URL;
    try { destination = new URL(raw, origin); }
    catch { return '/main'; }
    const page = destination.pathname.replace(/^\/public\//, '/').replace(/\.html$/, '');
    const allowed = ['/', '/main', '/deck', '/cards', '/scene', '/replay', '/puzzle', '/puzzle_editor', '/puzzle_test', '/marvel', '/watch'];
    return destination.origin === origin && allowed.includes(page)
        ? destination.pathname + destination.search : '/main';
}

// Keep the originating page and uploaded save in memory while preparation runs.
export function showArtworkPreparation(retry: () => void): void {
    document.getElementById('artwork-selection-notice')?.remove();
    const notice = document.createElement('aside');
    notice.id = 'artwork-selection-notice';
    notice.setAttribute('role', 'status');
    notice.style.cssText = 'position:fixed;right:20px;bottom:20px;max-width:420px;padding:20px;background:#253244;color:white;border:1px solid #80d5ff;border-radius:8px;z-index:99999;font:16px Arial;box-shadow:0 8px 30px #0008';
    const message = document.createElement('p');
    message.textContent = '선택한 카드의 이미지를 준비 중입니다. 선택은 유지됩니다. 준비 완료 후 다시 시도하세요.';
    notice.appendChild(message);
    const link = document.createElement('a');
    link.href = '/artwork'; link.target = '_blank'; link.rel = 'noopener';
    link.textContent = '이미지 준비 상태'; link.style.color = '#80d5ff';
    notice.appendChild(link);
    for (const [label, action] of [
        ['선택 다시 시도', () => { notice.remove(); retry(); }],
        ['닫기', () => notice.remove()],
    ] as const) {
        const control = document.createElement('button');
        control.type = 'button'; control.textContent = label;
        control.style.marginLeft = '12px'; control.onclick = action;
        notice.appendChild(control);
    }
    document.body.appendChild(notice);
}

export function startArtworkPage(): void {
    const text = (id: string, value: string) => { document.getElementById(id)!.textContent = value; };
    const button = (id: string) => document.getElementById(id) as HTMLButtonElement;
    const progress = document.getElementById('progress') as HTMLProgressElement;
    const next = new URLSearchParams(location.search).get('next');
    const destination = artworkDestination(next, location.origin);
    let status: ArtworkStatus | null = null;
    let actionRunning = false;
    let timer: number | undefined;

    function render(value: ArtworkStatus): void {
        status = value;
        const preparing = ['idle', 'preparing', 'downloading'].includes(value.state);
        const titles: Record<string, string> = {
            idle: '카드 이미지 준비 중', preparing: '카드 이미지 준비 중', downloading: '카드 이미지 다운로드 중',
            paused: '다운로드 일시정지', ready: '카드 이미지 준비 완료', error: '다운로드 오류 확인 필요', incomplete: '카드 이미지 목록 불완전',
        };
        text('state', titles[value.state] || '이미지 준비 중');
        text('message', value.ready ? '지원되는 모든 카드 이미지가 저장되었습니다.'
            : value.can_play ? '설치된 카드로 플레이할 수 있습니다. 새 카드는 다운로드 후 사용할 수 있습니다.'
            : value.state === 'incomplete' ? '검증된 이미지 목록이 불완전합니다. 수정된 빌드가 필요합니다.'
            : value.state === 'paused' ? '이어서 받기를 누르세요. 완료된 이미지는 유지됩니다.'
            : '플레이 전 전체 카드를 준비합니다. 진행 상황은 자동 저장됩니다.');
        progress.max = Math.max(1, value.total_cards);
        progress.value = value.completed_cards;
        text('cards', `${value.completed_cards.toLocaleString()} / ${value.total_cards.toLocaleString()}`);
        text('packs', `${value.completed_packs.toLocaleString()} / ${value.total_packs.toLocaleString()}`);
        text('download', `${formatArtworkBytes(value.downloaded_bytes)} / ${formatArtworkBytes(value.total_bytes)}`);
        text('installed', `${formatArtworkBytes(value.installed_bytes)} / ${formatArtworkBytes(value.total_installed_bytes)}`);
        text('required', formatArtworkBytes(value.required_storage_bytes));
        text('folder', value.folder || 'Not available');
        const errors = [value.error, ...Object.values(value.errors || {})].filter(Boolean);
        text('errors', [...new Set(errors)].join('\n'));
        document.getElementById('errors')!.hidden = errors.length === 0;
        button('pause').disabled = actionRunning || !preparing;
        button('resume').disabled = actionRunning || value.state !== 'paused';
        button('retry').disabled = actionRunning || value.state !== 'error';
        button('continue').disabled = !value.can_play;
        button('continue').textContent = value.ready ? '계속' : '설치된 카드로 계속';
        if (next && value.can_play) location.replace(destination);
    }

    async function poll(): Promise<void> {
        try {
            const response = await fetch('/get_artwork_status', { cache: 'no-store' });
            if (!response.ok) throw new Error('Could not read artwork status');
            if (response.headers.get('Content-Type')?.includes('text/html')) {
                // Authentication/version pages are returned as HTML by the
                // existing server. Let their normal cookie flow recover.
                location.reload();
                return;
            }
            render(await response.json());
        } catch {
            text('state', '게임 서버 연결 대기 중');
            text('message', '앱을 켜 두세요. 자동으로 다시 연결합니다.');
        } finally {
            timer = window.setTimeout(poll, 1000);
        }
    }

    async function action(name: string): Promise<void> {
        actionRunning = true;
        if (status) render(status);
        try {
            const response = await fetch('/artwork_action', {
                method: 'POST', cache: 'no-store', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: name }),
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Could not update artwork download');
            render(result);
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            if (status) status = { ...status, error: message };
            else { text('errors', message); document.getElementById('errors')!.hidden = false; }
        } finally {
            actionRunning = false;
            if (status) render(status);
        }
    }

    for (const name of ['pause', 'resume', 'retry']) button(name).onclick = () => { void action(name); };
    button('continue').onclick = () => { if (status?.can_play) location.assign(destination); };
    window.addEventListener('pagehide', () => { if (timer !== undefined) window.clearTimeout(timer); }, { once: true });
    void poll();
}
