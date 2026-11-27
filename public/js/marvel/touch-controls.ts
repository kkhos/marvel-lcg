import { koCard, koCardSource } from './ko-cards.js';
import { koStatusCard } from './ko-status.js';
import { Cards } from './cards.js';
import { ClassName } from './class_name.js';
import { Effect } from './effect.js';
import { SelectStep } from './select.js';
import { CardImages } from '../module/card_images.js';
import { HoverCard } from './hover.js';
import { HistoryLog } from './history.js';

type Gesture = {
    id: number; card: HTMLElement; x: number; y: number;
    timer: number; dragging: boolean; held: boolean;
};

// Touch is an input adapter, not a second game engine.
// A drop selects an existing action/target, never changes card ownership or zone.
export class TouchControls {
    static isTouchDevice() {
        return navigator.maxTouchPoints > 0 || matchMedia('(pointer: coarse)').matches;
    }

    static init() {
        const style = document.createElement('style');
        style.textContent = `
            #scene .card { touch-action: none; -webkit-user-select: none; user-select: none; -webkit-touch-callout: none; }
            #touch-preview { background: #172a23; color: white; border: 1px solid #83b79a; border-radius: 12px;
                position: fixed; inset: 0; margin: auto; box-sizing: border-box; width: fit-content;
                height: fit-content; max-width: 90vw; max-height: 90dvh; padding: 10px; overflow: auto; }
            #touch-preview::backdrop { background: #000b; }
            #touch-preview img { display: block; height: min(74vh, 600px); max-width: 78vw; object-fit: contain; margin: auto; }
            #touch-preview .touch-card-body { display:flex; gap:16px; align-items:center; }
            #touch-preview .touch-card-body img { max-width:42vw; height:min(65dvh,500px); flex:0 0 auto; }
            #touch-preview .touch-card-text { width:min(42vw,450px); min-width:0; max-height:65dvh; overflow:auto; font:15px/1.5 system-ui,sans-serif; white-space:pre-wrap; overflow-wrap:anywhere; }
            #touch-preview .touch-card-title { display:block; font-size:19px; margin-bottom:8px; }
            #touch-preview .touch-card-source { display:block; color:#b9d4c3; font-size:11px; margin-top:10px; }
            #touch-preview .touch-buttons { display: flex; gap: 8px; justify-content: center; margin-top: 6px; }
            #touch-preview button, #touch-pile > button { min-height: 44px; padding: 5px 16px;
                font: 700 15px/1.25 system-ui,sans-serif; color: #f1f6f3; background: #30493e;
                border: 1px solid #83b79a; border-radius: 7px; }
            #touch-preview button[hidden] { display: none !important; }
            #touch-drag-ghost { position: fixed; pointer-events: none; z-index: 2147483646; width: 86px; height: 120px;
                background: #263e33 center / contain no-repeat; border: 2px solid #a5e5c6; border-radius: 6px; opacity: .86;
                transform: translate(-50%, -70%); }
            #touch-drop-zone { position: fixed; z-index: 2147483645; top: 8px; left: 50%; transform: translateX(-50%);
                background: #263e33; border: 2px dashed #a5e5c6; border-radius: 10px; color: white;
                padding: 14px 24px; font: bold 16px Arial; }
        `;
        document.head.append(style);
        const dialog = document.createElement('dialog');
        dialog.id = 'touch-preview';
        dialog.setAttribute('aria-label', '카드 미리보기');
        const img = document.createElement('img');
        img.alt = '카드 미리보기';
        const controls = document.createElement('div');
        controls.className = 'touch-buttons';
        const flip = document.createElement('button');
        flip.type = 'button'; flip.textContent = '뒤집기';
        const close = document.createElement('button');
        close.type = 'button'; close.textContent = '닫기';
        controls.append(flip, close);
        const body = document.createElement('div');
        body.className = 'touch-card-body';
        const description = document.createElement('div');
        description.className = 'touch-card-text';
        const name = document.createElement('strong');
        name.className = 'touch-card-title';
        const text = document.createElement('div');
        const source = document.createElement('small');
        source.className = 'touch-card-source';
        description.append(name,text,source);
        body.append(img,description);
        dialog.append(body, controls);
        document.body.append(dialog);
        let previewFront = '', previewBack = '', showingBack = false;
        let previewId = '', previewName = '', previewType = '';
        function updateDescription() {
            const id = showingBack ? previewBack : previewId;
            // Never infer or reveal a hidden card's name from its object ID.
            const status = showingBack ? undefined : koStatusCard(previewType, previewName);
            const translated = status ?? koCard(id);
            name.textContent = translated?.name ?? (showingBack ? '뒷면' : previewName);
            const raw = translated?.text ?? (showingBack ? '' : Cards.getText(id));
            const plain = raw.replace(/<hr\s*\/?\s*>/gi,'\n────\n').replace(/<br\s*\/?\s*>/gi,'\n').replace(/<[^>]*>/g,'');
            text.textContent = plain || (translated ? '추가 능력 설명 없음' : '표시할 설명 없음');
            source.textContent = status ? '부가 상태 카드 · 한국어 설명' : translated?.text !== undefined ? (koCardSource(id) === 'verified' ? '정발판 효과 대조 완료 · 자원 기호는 문자로 표시' : koCardSource(id) === 'community' ? 'MarvelCDB 커뮤니티 번역 · 실물 대조 권장' : '한국어 번역 초안 · 원본 카드와 대조 권장') : '원문 / 미번역';
        }
        close.onclick = () => dialog.close();
        dialog.onclick = e => { if (e.target === dialog) dialog.close(); };
        dialog.addEventListener('close', () => CardImages.setImage(img, ''));
        flip.onclick = () => {
            showingBack = !showingBack;
            CardImages.setImage(img, showingBack ? previewBack : previewFront);
            updateDescription();
        };
        function preview(card: HTMLElement) {
            const data = Cards.getCard(Number(card.dataset.id));
            if (!data || !data.isVisible() || !data.pic_id) return;
            previewId = data.card_id;
            previewName = data.name;
            previewType = data.card_type;
            previewFront = data.pic_id;
            previewBack = data.down_card_id;
            showingBack = false;
            flip.hidden = previewType === 'StatusCard' || !previewBack || previewBack === previewFront;
            flip.disabled = flip.hidden;
            if (!dialog.open) dialog.showModal();
            CardImages.setImage(img, previewFront);
            updateDescription();
        }

        const pile = document.createElement('dialog');
        pile.id = 'touch-pile';
        pile.style.cssText = 'position:fixed;inset:0;margin:auto;box-sizing:border-box;height:fit-content;background:#172a23;color:white;border:1px solid #83b79a;border-radius:12px;width:min(80vw,760px);max-height:85dvh;overflow:auto;padding:12px';
        const pileTitle = document.createElement('h3');
        const pileList = document.createElement('div');
        pileList.style.cssText = 'display:flex;gap:10px;overflow-x:auto;touch-action:pan-x;padding:8px';
        const pileClose = document.createElement('button');
        pileClose.textContent = '닫기';
        pileClose.onclick = () => pile.close();
        pile.append(pileTitle, pileList, pileClose);
        document.body.append(pile);
        pile.addEventListener('close', () => {
            pileList.querySelectorAll('img').forEach(image => CardImages.setImage(image, ''));
            pileList.replaceChildren();
        });
        pile.onclick = e => { if (e.target === pile) pile.close(); };
        document.addEventListener('click', e => {
            if (!(e.target instanceof Element)) return;
            const parent = e.target.closest<HTMLElement>('#nemesis-pool,#removed-pool,#area-removed,#area-advanced');
            if (!parent || dialog.open || settings.open || pile.open || performance.now() < suppressUntil) return;
            const cards = Array.from(parent.querySelectorAll<HTMLElement>('.card[data-id]'));
            if (cards.some(card => selectable(card))) return;
            const visible = cards.filter(card => Cards.getCard(Number(card.dataset.id))?.isVisible());
            if (!visible.length) return;
            e.preventDefault(); e.stopImmediatePropagation();
            parent.classList.remove('clicked');
            HoverCard.set(null);
            pileTitle.textContent = parent.id === 'nemesis-pool' ? '숙적 카드' : '예비 카드';
            for (const card of visible) {
                const data = Cards.getCard(Number(card.dataset.id))!;
                const button = document.createElement('button');
                button.style.cssText = 'flex:0 0 auto;background:transparent;border:0;padding:2px';
                const image = document.createElement('img');
                image.alt = koCard(data.card_id)?.name ?? data.name;
                image.style.cssText = 'height:min(48dvh,230px);width:auto;display:block';
                button.append(image);
                CardImages.setImage(image, data.pic_id);
                button.onclick = () => preview(card);
                pileList.append(button);
            }
            pile.showModal();
        }, true);
        const ghost = document.createElement('div');
        ghost.id = 'touch-drag-ghost'; ghost.hidden = true;
        const zone = document.createElement('div');
        zone.id = 'touch-drop-zone'; zone.hidden = true; zone.textContent = '여기에 놓아 카드 선택';
        document.body.append(ghost, zone);

        let gesture: Gesture | null = null;
        let suppressCard: HTMLElement | null = null;
        let suppressUntil = 0;
        function suppress(card: HTMLElement) {
            suppressCard = card;
            suppressUntil = performance.now() + 800;
        }
        function cardAt(target: EventTarget | null): HTMLElement | null {
            return target instanceof Element ? target.closest<HTMLElement>('#scene .card[data-id]') : null;
        }
        function selectable(card: HTMLElement) {
            return [ClassName.highlight_effect, ClassName.forced_action_effect, ClassName.highlight_target, ClassName.highlight_pay]
                .some(name => card.classList.contains(name));
        }
        function stop() {
            if (!gesture) return;
            const g = gesture;
            gesture = null;
            clearTimeout(g.timer);
            if (g.card.hasPointerCapture(g.id)) g.card.releasePointerCapture(g.id);
            ghost.hidden = true; zone.hidden = true;
            CardImages.setBackground(ghost, 'background-image', '');
        }
        document.addEventListener('pointerdown', e => {
            if (e.pointerType !== 'touch' && e.pointerType !== 'pen') return;
            if (!e.isPrimary || gesture) { if (gesture) { suppress(gesture.card); stop(); } return; }
            // A fresh deliberate tap must not be swallowed by the prior drag.
            suppressUntil = 0;
            const card = cardAt(e.target);
            if (!card || dialog.open || settings.open || (e.target as Element).closest('button,input,a,.auto-activate')) return;
            const g: Gesture = { id: e.pointerId, card, x: e.clientX, y: e.clientY, timer: 0, dragging: false, held: false };
            gesture = g;
            g.timer = window.setTimeout(() => {
                if (gesture !== g || !card.isConnected) return;
                g.held = true;
                suppress(card);
                preview(card);
            }, 480);
        }, true);
        document.addEventListener('pointermove', e => {
            const g = gesture;
            if (!g || g.id !== e.pointerId || g.held) return;
            if (!g.dragging && Math.hypot(e.clientX - g.x, e.clientY - g.y) > 12) {
                clearTimeout(g.timer);
                g.dragging = true;
                suppress(g.card);
                const data = Cards.getCard(Number(g.card.dataset.id));
                const visible = data?.isVisible();
                if (visible && data) CardImages.setBackground(ghost, 'background-image', data.pic_id);
                else if (data?.down_card_id) CardImages.setBackground(ghost, 'background-image', data.down_card_id);
                ghost.hidden = false;
                zone.hidden = !selectable(g.card);
                if (g.card.isConnected) g.card.setPointerCapture(e.pointerId);
            }
            if (g.dragging) {
                e.preventDefault();
                ghost.style.left = `${e.clientX}px`;
                ghost.style.top = `${e.clientY}px`;
            }
        }, { capture: true, passive: false });
        document.addEventListener('pointerup', e => {
            const g = gesture;
            if (!g || e.pointerId !== g.id) return;
            if (!g.dragging && !g.held) { stop(); return; } // normal browser click is the tap
            e.preventDefault();
            suppress(g.card);
            const hit = document.elementFromPoint(e.clientX, e.clientY);
            const target = cardAt(hit);
            const inZone = hit === zone || !!hit?.closest('#touch-drop-zone');
            const inPlay = !!hit?.closest('#area-play');
            const canSelect = g.card.isConnected && selectable(g.card);
            const canTarget = !!target && target !== g.card && SelectStep.isTargets()
                && Effect.select_effect_obj?.bind_id === Number(g.card.dataset.id)
                && target.classList.contains(ClassName.highlight_target);
            stop();
            if (g.dragging && !g.held) {
                if (canTarget && target?.isConnected) Effect.onCardClick(target, false, false, true);
                else if (canSelect && (inZone || inPlay)) Effect.onCardClick(g.card, false, false, true);
            }
        }, { capture: true, passive: false });
        document.addEventListener('pointercancel', e => {
            if (gesture?.id === e.pointerId) { suppress(gesture.card); stop(); }
        }, true);
        document.addEventListener('lostpointercapture', e => {
            if (gesture?.id === e.pointerId) { suppress(gesture.card); stop(); }
        }, true);
        document.addEventListener('click', e => {
            if (performance.now() < suppressUntil && suppressCard
                && (cardAt(e.target) === suppressCard || (e.target instanceof Element && e.target.closest('#scene')))) {
                e.preventDefault(); e.stopImmediatePropagation();
                suppressUntil = 0;
            }
        }, true);
        document.addEventListener('contextmenu', e => {
            if (cardAt(e.target) && (gesture || (e as PointerEvent).pointerType === 'touch')) {
                e.preventDefault(); e.stopImmediatePropagation();
            }
        }, true);
        // Put the existing settings controls into a top-layer modal. Their IDs,
        // listeners and game preferences remain intact. showModal makes the board
        // inert, so dismissing the settings cannot also confirm a game action.
        HistoryLog.initMobile();
        const settings = document.createElement('dialog');
        settings.id = 'mobile-settings-dialog';
        settings.setAttribute('aria-label', '게임 설정');
        const sidebar = document.getElementById('right-side-bar');
        const sidebarHandle = document.getElementById('right-side-bar-handle');
        if (sidebar && sidebarHandle) {
            const header = document.createElement('div');
            header.className = 'mobile-settings-header';
            const title = document.createElement('strong');
            title.textContent = '게임 설정';
            const closeSettings = document.createElement('button');
            closeSettings.type = 'button';
            closeSettings.textContent = '닫기 ×';
            header.append(title, closeSettings);
            sidebar.classList.remove('clicked', 'side-bar');
            sidebar.classList.add('mobile-settings-controls');
            document.body.append(sidebarHandle, settings);
            settings.append(header, sidebar);
            sidebarHandle.setAttribute('role', 'button');
            sidebarHandle.setAttribute('tabindex', '0');
            sidebarHandle.setAttribute('aria-expanded', 'false');
            sidebarHandle.setAttribute('aria-controls', settings.id);
            const openSettings = () => {
                if (dialog.open || settings.open) return;
                if (gesture) { suppress(gesture.card); stop(); }
                // Clear only desktop hover state, not the game selection.
                HoverCard.set(null);
                settings.showModal();
                sidebarHandle.setAttribute('aria-expanded', 'true');
            };
            sidebarHandle.addEventListener('click', e => {
                e.preventDefault(); e.stopPropagation(); openSettings();
            });
            sidebarHandle.addEventListener('keydown', e => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault(); openSettings();
                }
            });
            closeSettings.onclick = () => settings.close();
            settings.addEventListener('click', e => {
                // The backdrop targets the modal itself, not the game board.
                e.stopPropagation();
                if (e.target === settings) {
                    const rect = settings.getBoundingClientRect();
                    if (e.clientX < rect.left || e.clientX > rect.right ||
                        e.clientY < rect.top || e.clientY > rect.bottom) {
                        e.preventDefault();
                        settings.close();
                    }
                }
            });
            settings.addEventListener('close', () => {
                sidebarHandle.setAttribute('aria-expanded', 'false');
                if (!HistoryLog.isOpen()) sidebarHandle.focus({ preventScroll: true });
            });
            // History is a separate existing game overlay; reveal it after the
            // user explicitly opens it, rather than leaving it behind settings.
            sidebar.addEventListener('click', e => {
                const target = e.target instanceof Element ? e.target.closest('button') : null;
                if (target && (target.textContent?.trim() === '기록' || target.matches('.do-save,.do-load') || target.textContent?.trim() === '빠른 저장') && settings.open) settings.close();
            });
        }
        window.addEventListener('blur', () => { if (gesture) { suppress(gesture.card); stop(); } });
        (window as unknown as { MarvelTouch: { back: () => boolean } }).MarvelTouch = {
            back: () => {
                if (HistoryLog.isOpen()) { HistoryLog.close(); return true; }
                if (settings.open) { settings.close(); return true; }
                if (dialog.open) { dialog.close(); return true; }
                if (pile.open) { pile.close(); return true; }
                const result = document.querySelector('#game-over-box-container');
                if (result?.querySelector('#game-over-box.active') && !result.classList.contains('minimize')) {
                    result.classList.add('minimize'); return true;
                }
                if (gesture) { suppress(gesture.card); stop(); return true; }
                const sidebar = document.querySelector('#right-side-bar.clicked');
                if (sidebar) { sidebar.classList.remove('clicked'); return true; }
                return false;
            },
        };
    }
}
