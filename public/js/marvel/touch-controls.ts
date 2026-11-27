import { Cards } from './cards.js';
import { ClassName } from './class_name.js';
import { Effect } from './effect.js';
import { SelectStep } from './select.js';
import { CardImages } from '../module/card_images.js';

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
            #touch-preview { background: #18222c; color: white; border: 1px solid #a0b4c8; border-radius: 12px;
                max-width: 90vw; max-height: 90vh; padding: 10px; overflow: auto; }
            #touch-preview::backdrop { background: #000b; }
            #touch-preview img { display: block; height: min(74vh, 600px); max-width: 78vw; object-fit: contain; margin: auto; }
            #touch-preview .touch-buttons { display: flex; gap: 8px; justify-content: center; margin-top: 6px; }
            #touch-preview button { min-height: 44px; padding: 5px 16px; font-size: 16px; }
            #touch-drag-ghost { position: fixed; pointer-events: none; z-index: 2147483646; width: 86px; height: 120px;
                background: #24384c center / contain no-repeat; border: 2px solid #9cd8ff; border-radius: 6px; opacity: .86;
                transform: translate(-50%, -70%); }
            #touch-drop-zone { position: fixed; z-index: 2147483645; top: 8px; left: 50%; transform: translateX(-50%);
                background: #24384c; border: 2px dashed #9cd8ff; border-radius: 10px; color: white;
                padding: 14px 24px; font: bold 16px Arial; }
        `;
        document.head.append(style);
        const dialog = document.createElement('dialog');
        dialog.id = 'touch-preview';
        dialog.setAttribute('aria-label', 'Card preview');
        const img = document.createElement('img');
        img.alt = 'Card preview';
        const controls = document.createElement('div');
        controls.className = 'touch-buttons';
        const flip = document.createElement('button');
        flip.type = 'button'; flip.textContent = 'Flip';
        const close = document.createElement('button');
        close.type = 'button'; close.textContent = 'Close';
        controls.append(flip, close);
        dialog.append(img, controls);
        document.body.append(dialog);
        let previewFront = '', previewBack = '', showingBack = false;
        close.onclick = () => dialog.close();
        dialog.onclick = e => { if (e.target === dialog) dialog.close(); };
        dialog.addEventListener('close', () => CardImages.setImage(img, ''));
        flip.onclick = () => {
            showingBack = !showingBack;
            CardImages.setImage(img, showingBack ? previewBack : previewFront);
        };
        function preview(card: HTMLElement) {
            const data = Cards.getCard(Number(card.dataset.id));
            if (!data || !data.isVisible() || !data.pic_id) return;
            previewFront = data.pic_id;
            previewBack = data.down_card_id;
            showingBack = false;
            flip.disabled = !previewBack || previewBack === previewFront;
            if (!dialog.open) dialog.showModal();
            CardImages.setImage(img, previewFront);
        }

        const ghost = document.createElement('div');
        ghost.id = 'touch-drag-ghost'; ghost.hidden = true;
        const zone = document.createElement('div');
        zone.id = 'touch-drop-zone'; zone.hidden = true; zone.textContent = 'Drop to select card';
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
            if (!card || dialog.open || (e.target as Element).closest('button,input,a,.auto-activate')) return;
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
        const sidebarHandle = document.getElementById('right-side-bar-handle');
        sidebarHandle?.addEventListener('click', () => {
            document.getElementById('right-side-bar')?.classList.toggle('clicked');
        });
        window.addEventListener('blur', () => { if (gesture) { suppress(gesture.card); stop(); } });
        (window as unknown as { MarvelTouch: { back: () => boolean } }).MarvelTouch = {
            back: () => {
                if (dialog.open) { dialog.close(); return true; }
                if (gesture) { suppress(gesture.card); stop(); return true; }
                const sidebar = document.querySelector('#right-side-bar.clicked');
                if (sidebar) { sidebar.classList.remove('clicked'); return true; }
                return false;
            },
        };
    }
}
