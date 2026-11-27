import { koText, koHtml, koLabel, koGameOverReason } from "./ko-game.js";
import { Command } from "./command.js";
import { Game } from "./game.js";
import { Replay } from "./replay.js";
import { Client } from "./client.js";
import { UI } from "./ui.js";
import { Setting } from "./settings.js";

export class Message {

    private static overlay: HTMLElement
    private static messageElement: HTMLElement

    private static game_over_div: HTMLElement
    private static end_messageElement: HTMLElement
    private static end_messageElementText: HTMLElement

    private static retryButton: HTMLButtonElement;
    private static leaving = false;

    static init() {
        Message.overlay = document.getElementById('message-overlay')!;
        Message.messageElement = document.getElementById('message-text')!;

        Message.game_over_div = document.getElementById('game-over-box')!;
        // Message.end_overlay = document.getElementById('message-overlay')!;
        Message.end_messageElement = document.getElementById('game-over-text')!;
        Message.end_messageElementText = document.getElementById('game-over-text-2')!;
        const game_over_buttons = document.getElementById('game-over-buttons')!;

        const buttonSave = document.createElement('button');
        buttonSave.innerHTML = '<i class="fa fa-download" aria-hidden="true"></i> 리플레이 저장';
        buttonSave.classList.add('save-replay')
        buttonSave.title = '이 게임을 로컬 리플레이 보관함에 저장'
        buttonSave.addEventListener('click', function() {
            Command.saveLocal()
        });

        const buttonShare = document.createElement('button');
        buttonShare.innerHTML = '<i class="fa fa-cloud-upload" aria-hidden="true"></i> 리플레이 공유';
        buttonShare.classList.add('share-replay')
        buttonShare.addEventListener('click', function() {
            Command.uploadSave("Share")
        });

        game_over_buttons.appendChild(buttonShare);
        game_over_buttons.appendChild(buttonSave);
        const retry = document.createElement('button');
        retry.type = 'button';
        retry.className = 'retry-game';
        retry.innerHTML = '<i class="fa fa-refresh" aria-hidden="true"></i> 다시 도전';
        retry.onclick = () => { void Message.leaveResult(true); };
        Message.retryButton = retry;
        const home = document.createElement('button');
        home.type = 'button';
        home.className = 'main-menu';
        home.innerHTML = '<i class="fa fa-home" aria-hidden="true"></i> 메인 메뉴';
        home.onclick = () => { void Message.leaveResult(false); };
        game_over_buttons.append(retry,home);
    }

    private static async leaveResult(retry: boolean) {
        if (Message.leaving) return;
        if (Command.isSavingReplay) {
            window.alert('리플레이 저장이 끝난 후 다시 선택해 주세요.');
            return;
        }
        Message.leaving = true;
        const buttons = Array.from(document.querySelectorAll<HTMLButtonElement>('#game-over-buttons button'));
        buttons.forEach(b => b.disabled = true);
        try {
            if (retry) {
                const response = await fetch('/retry_finished_game', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({game_id:UI.last_game_id})
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || '다시 도전할 수 없습니다.');
            }
            // A full navigation gives each attempt an independent document and
            // cancels outstanding UI tasks. Keep the local Python server alive.
            const target = retry ? new URL(window.location.href) : new URL('/main', window.location.origin);
            if (retry) target.searchParams.delete('replay');
            else {
                const version = new URLSearchParams(window.location.search).get('v');
                if (version) target.searchParams.set('v',version);
            }
            Client.disconnect();
            window.location.replace(target.toString());
        } catch (error) {
            Message.leaving = false;
            buttons.forEach(b => b.disabled = false);
            window.alert(error instanceof Error ? error.message : '이동하지 못했습니다.');
        }
    }

    static cleanGameOverMessage() {
        Message.game_over_div.classList.remove('active');
    }

    static showGameOverMessage(text: string) {
        Message.retryButton.hidden = Replay.is_watching || Setting.is_watch;
        Message.game_over_div.classList.add('active');
        Message.overlay.classList.remove('active');
        if( Game.players_won ) {
            Message.end_messageElement.textContent = koLabel(Replay.is_watching ? "Replay complete — VICTORY" : "VICTORY");
        } else {
            Message.end_messageElement.textContent = koLabel(Replay.is_watching ? "Replay complete — DEFEAT" : "DEFEAT");
        }
        Message.end_messageElementText.textContent = koGameOverReason(text)
    }

    static showMessage(text: string, original_duration: number|null = 1200) {
        // Show the overlay
        Message.overlay.classList.add('active');

        let duration = 1200
        if( original_duration != null ) {
            duration = original_duration
        }

        let sec = duration / 1000
        if( Game.game_over ) {
            Message.showGameOverMessage(text)
        } else
        if( original_duration == null ) {
            Message.messageElement.textContent = koText(text);
            Message.overlay.style.animation = `overlay-move-once ${sec}s forwards`
        } else {
            Message.messageElement.textContent = koText(text);
            Message.overlay.style.animation = `overlay-move ${sec}s forwards`
        }

        // Hide the overlay after the specified duration
        if( !Game.game_over && original_duration != null ) {
            setTimeout(() => {
                Message.overlay.style.animation = ""
                Message.overlay.classList.remove('active');
                // if( !Game.game_over ) {
                //     Message.game_over_div.classList.remove('active');
                // }
            }, duration);
        }
    }
}
