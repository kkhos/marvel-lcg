import { koText, koHtml, koLabel } from "./ko-game.js";
export class HistoryLog
{
    static history_div? = document.getElementById("history") as HTMLElement;
    static history_text_div? = document.getElementById("history-text") as HTMLElement;
    private static mobileDialog: HTMLDialogElement | null = null;
    private static mobileTools: HTMLDetailsElement | null = null;
    static last_id = -1
    static contextMenu = document.getElementById('contextMenu') as HTMLElement;
    static click_object_id = 0
    static click_card_id = ""
    static click_card_name = ""

    static {
        HistoryLog.history_div?.addEventListener('click', (e) => {
            let target = e.target as HTMLElement
            if ( target !== HistoryLog.contextMenu && !HistoryLog.contextMenu.contains(target)) {
                HistoryLog.reportMenuOff();
            }
        });
    }

    static initMobile() {
        const history = HistoryLog.history_div;
        const log = HistoryLog.history_text_div;
        const tools = document.getElementById('ex-buttons');
        if (HistoryLog.mobileDialog || !history || !log || !tools) return;
        const dialog = document.createElement('dialog');
        dialog.id = 'mobile-history-dialog';
        dialog.setAttribute('aria-labelledby', 'mobile-history-title');
        const header = document.createElement('header');
        header.className = 'mobile-history-header';
        const title = document.createElement('h2');
        title.id = 'mobile-history-title';
        title.textContent = '게임 기록';
        const latest = document.createElement('button');
        latest.type = 'button';
        latest.id = 'mobile-history-latest';
        latest.textContent = '최신 기록 ↓';
        latest.onclick = () => { log.scrollTop = log.scrollHeight; };
        const close = document.createElement('button');
        close.type = 'button';
        close.id = 'mobile-history-close';
        close.textContent = '닫기 ×';
        close.onclick = () => HistoryLog.close();
        header.append(title, latest, close);
        const details = document.createElement('details');
        details.className = 'mobile-history-tools';
        const summary = document.createElement('summary');
        summary.textContent = '저장·불러오기 및 단계 이동';
        details.append(summary, tools);
        // Keep original nodes and handlers, including replay and step controls.
        history.prepend(header);
        history.append(details);
        document.body.append(dialog);
        dialog.append(history);
        HistoryLog.mobileDialog = dialog;
        HistoryLog.mobileTools = details;
        log.setAttribute('role', 'log');
        log.setAttribute('aria-label', '게임 진행 기록');
        log.tabIndex = 0;
        dialog.addEventListener('cancel', e => { e.preventDefault(); HistoryLog.close(); });
        dialog.addEventListener('click', e => {
            if (e.target !== dialog) return;
            const r = dialog.getBoundingClientRect();
            if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) {
                HistoryLog.close();
            }
        });
        dialog.addEventListener('close', () => {
            if (dialog.open) return;
            history.classList.add('hide');
            details.open = false;
            HistoryLog.reportMenuOff();
            document.getElementById('right-side-bar-handle')?.focus({preventScroll: true});
        });
    }

    static close() {
        if (HistoryLog.mobileDialog) {
            HistoryLog.history_div?.classList.add('hide');
            HistoryLog.reportMenuOff();
            if (HistoryLog.mobileTools) HistoryLog.mobileTools.open = false;
            if (HistoryLog.mobileDialog.open) HistoryLog.mobileDialog.close();
            return;
        }
        if (HistoryLog.isOpen()) HistoryLog.toggle();
    }

    static isOpen() {
        return HistoryLog.mobileDialog ? HistoryLog.mobileDialog.open :
            !HistoryLog.history_div?.classList.contains('hide');
    }
    static toggle() {
        const dialog = HistoryLog.mobileDialog;
        if (!dialog) {
            HistoryLog.history_div?.classList.toggle('hide');
            return;
        }
        if (dialog.open) { HistoryLog.close(); return; }
        // Close settings before opening the independent top-layer history.
        const settings = document.getElementById('mobile-settings-dialog') as HTMLDialogElement | null;
        if (settings?.open) settings.close();
        HistoryLog.history_div?.classList.remove('hide');
        dialog.showModal();
        document.getElementById('mobile-history-latest')?.focus({preventScroll: true});
        const log = HistoryLog.history_text_div;
        if (log) log.scrollTop = log.scrollHeight;
    }
    static addText(id: number, text: string) {
        if( id == HistoryLog.last_id ) {
            return
        }
        if( text && HistoryLog.history_text_div ) {
            text = koHtml(text).replaceAll("\n", "")
            HistoryLog.last_id = id
            text = `<p class='log-id'>${id}</p> <p>${text}</p>`
            // Follow live entries only when the reader is already at the end.
            const log = HistoryLog.history_text_div;
            const follow = !!HistoryLog.mobileDialog?.open &&
                log.scrollHeight - log.clientHeight - log.scrollTop < 32;
            log.insertAdjacentHTML('beforeend', text);
            if (follow) log.scrollTop = log.scrollHeight;
        }
    }
    static isEmpty() {
        return HistoryLog.history_text_div?.innerHTML == ""
    }

    static showMenu(e: MouseEvent, object_id: number, card_id: string, card_name: string) {
        // e.preventDefault();
        HistoryLog.click_object_id = object_id
        HistoryLog.click_card_id = card_id
        HistoryLog.click_card_name = card_name
        HistoryLog.contextMenu.style.display = 'block';
        HistoryLog.contextMenu.style.left = `${e.pageX}px`;
        HistoryLog.contextMenu.style.top = `${e.pageY}px`;
        HistoryLog.contextMenu.querySelector('#view_in_mdb')!.textContent =
            HistoryLog.mobileDialog ? 'MarvelCDB에서 보기' : card_id;
        if (HistoryLog.mobileDialog?.open) {
            e.preventDefault();
            const menu = HistoryLog.contextMenu;
            menu.style.left = Math.max(4, Math.min(e.clientX, innerWidth - menu.offsetWidth - 4)) + 'px';
            menu.style.top = Math.max(4, Math.min(e.clientY, innerHeight - menu.offsetHeight - 4)) + 'px';
        }
    }

    static gotoMDB(e: HTMLElement) {
        HistoryLog.reportMenuOff()
        window.open(`https://marvelcdb.com/card/${HistoryLog.click_card_id}`)
    }

    // static editCard(e: HTMLElement) {
    //     HistoryLog.reportMenuOff()
    //     Debug.doDebugCmd(`edit ${HistoryLog.click_card_id}`)
    // }

    static markCard(e: HTMLElement) {
        HistoryLog.reportMenuOff()
        // Debug.markCard(HistoryLog.click_object_id, 'marked-card')
    }

    static reportMenuOff(e: HTMLElement|null=null) {
        HistoryLog.contextMenu.style.display = 'none';
    };
}

(window as any).HistoryLog = HistoryLog;
