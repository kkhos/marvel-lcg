// Presentation adapter: the original buttons remain the only action handlers.
export class MobileAbilityChoices {
    private static source: HTMLElement | null = null;
    private static originals: HTMLButtonElement[] = [];
    private static canCancel: () => boolean = () => false;
    private static dialog: HTMLDialogElement | null = null;
    private static list: HTMLElement;
    private static cancelButton: HTMLButtonElement;
    private static hint: HTMLElement;
    private static observer: MutationObserver | null = null;
    private static frame = 0;
    private static signature = '';

    static present(source: HTMLElement, canCancel: () => boolean) {
        if (!document.body.classList.contains('mobile-layout')) return;
        this.source = source;
        this.originals = Array.from(source.querySelectorAll<HTMLButtonElement>(':scope > button'));
        this.canCancel = canCancel;
        this.init();
        this.schedule();
    }

    private static init() {
        if (this.dialog) return;
        const dialog = document.createElement('dialog');
        dialog.id = 'mobile-ability-choice-dialog';
        dialog.setAttribute('aria-labelledby', 'mobile-ability-choice-title');
        const heading = document.createElement('h2');
        heading.id = 'mobile-ability-choice-title';
        heading.textContent = '해결할 능력 선택';
        this.hint = document.createElement('p');
        this.hint.className = 'mac-hint';
        this.list = document.createElement('div');
        this.list.className = 'mac-list';
        this.cancelButton = document.createElement('button');
        this.cancelButton.type = 'button';
        this.cancelButton.className = 'mac-cancel';
        this.cancelButton.onclick = () => this.requestCancel();
        dialog.append(heading, this.hint, this.list, this.cancelButton);
        // Never dismiss the mandatory choice by Escape or tapping the backdrop.
        dialog.addEventListener('cancel', e => {
            e.preventDefault();
            this.requestCancel();
        });
        dialog.addEventListener('contextmenu', e => e.preventDefault());
        dialog.addEventListener('selectstart', e => e.preventDefault());
        dialog.addEventListener('close', () => this.schedule());
        document.body.append(dialog);
        this.dialog = dialog;

        this.observer = new MutationObserver(() => this.schedule());
        if (this.source) this.observer.observe(this.source, {
            childList: true, subtree: true, attributes: true,
            attributeFilter: ['class', 'disabled', 'hidden']
        });
        this.observer.observe(document.body, {
            attributes: true, attributeFilter: ['class', 'data-selection-step']
        });
        const end = document.getElementById('btn-end');
        if (end) this.observer.observe(end, {
            attributes: true, childList: true, subtree: true,
            attributeFilter: ['class', 'disabled', 'hidden']
        });
        window.addEventListener('resize', () => this.schedule());
        window.visualViewport?.addEventListener('resize', () => this.schedule());
        // If another modal was already open, wait until it has closed.
        document.addEventListener('close', () => this.schedule(), true);
    }

    private static schedule() {
        if (this.frame) return;
        this.frame = requestAnimationFrame(() => {
            this.frame = 0;
            this.refresh();
        });
    }

    private static enabled(button: HTMLButtonElement) {
        return !button.disabled && !button.classList.contains('disable') && !button.hidden;
    }

    private static optionalCancel() {
        const end = document.getElementById('btn-end') as HTMLButtonElement | null;
        return this.canCancel() && end && !end.disabled &&
            !end.classList.contains('forced_action') && getComputedStyle(end).display !== 'none'
            ? end : null;
    }

    private static close() {
        this.source?.classList.remove('mac-popup-active');
        if (this.dialog?.open) this.dialog.close();
        this.signature = '';
    }

    private static requestCancel() {
        const end = this.optionalCancel();
        if (!end) return;
        this.close();
        end.click();
        this.schedule();
    }

    static handleBack(): boolean {
        if (!this.dialog?.open) return false;
        this.requestCancel();
        return true;
    }

    private static needsPopup(source: HTMLElement, buttons: HTMLButtonElement[]) {
        if (!source.clientHeight || !source.clientWidth) return false;
        // The measured two-line height includes padding and border. Images
        // may be tall intentionally; total overflow still triggers a popup.
        const tooTall = buttons.some(button => {
            if (button.querySelector('img')) return false;
            const s = getComputedStyle(button);
            const line = parseFloat(s.lineHeight) || parseFloat(s.fontSize) * 1.25;
            const extras = ['paddingTop','paddingBottom','borderTopWidth','borderBottomWidth']
                .reduce((sum, key) => sum + (parseFloat(s.getPropertyValue(key.replace(/[A-Z]/g, c => '-' + c.toLowerCase()))) || 0), 0);
            return button.getBoundingClientRect().height > Math.max(parseFloat(s.minHeight) || 0, line * 2 + extras) + 1;
        });
        return tooTall || source.scrollHeight > source.clientHeight + 2;
    }

    private static refresh() {
        const source = this.source, dialog = this.dialog;
        if (!source || !dialog) return;
        const buttons = Array.from(source.querySelectorAll<HTMLButtonElement>(':scope > button'));
        // A new engine prompt must explicitly register its own choices.
        // Removing the old buttons invalidates all proxies immediately.
        const same = buttons.length === this.originals.length &&
            buttons.every((button, index) => button === this.originals[index]);
        if (!same || !document.body.classList.contains('mobile-layout') ||
            document.body.dataset.selectionStep !== 'effect' ||
            !buttons.some(button => this.enabled(button)) ||
            buttons.some(button => button.classList.contains('clicked')) ||
            !this.needsPopup(source, buttons)) {
            this.close();
            return;
        }
        if (!dialog.open && document.querySelector('dialog[open]')) return;
        const cancel = this.optionalCancel();
        const signature = JSON.stringify([buttons.map(b => [b.innerHTML, this.enabled(b)]), cancel?.textContent]);
        if (signature !== this.signature || !dialog.open) {
            this.signature = signature;
            this.list.replaceChildren();
            for (const original of buttons) {
                const proxy = document.createElement('button');
                proxy.type = 'button';
                proxy.className = 'mac-option';
                proxy.innerHTML = original.innerHTML;
                proxy.disabled = !this.enabled(original);
                proxy.onclick = () => {
                    if (!original.isConnected || !this.originals.includes(original) || !this.enabled(original)) return;
                    this.close();
                    original.click();
                    this.schedule();
                };
                this.list.append(proxy);
            }
            this.hint.textContent = cancel ? '능력을 선택하세요' : '필수 · 능력을 선택하세요';
            this.cancelButton.hidden = !cancel;
            this.cancelButton.textContent = cancel?.textContent?.trim() || '취소';
        }
        if (!dialog.open) {
            source.classList.add('mac-popup-active');
            window.getSelection()?.removeAllRanges();
            dialog.showModal();
        }
    }
}
