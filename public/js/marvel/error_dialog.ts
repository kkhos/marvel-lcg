import { Setting } from "./settings.js";
import { Command } from "./command.js";

export class ErrorDialog {
    private static error_occurred_div: HTMLElement
    private static error_occurred_body_tip: HTMLElement
    private static error_occurred_body_div: HTMLElement
    private static last_error_text = ""

    static async init() {
        ErrorDialog.error_occurred_div = ErrorDialog.createErrorOccurredDiv()
        ErrorDialog.error_occurred_body_div = ErrorDialog.error_occurred_div.querySelector('.error-occurred-body')!
        ErrorDialog.error_occurred_body_tip = ErrorDialog.error_occurred_div.querySelector('.error-occurred-tip')!

        document.body.appendChild(ErrorDialog.error_occurred_div);
    }

    // Create a function to generate the error occurred HTML
    static createErrorOccurredDiv(): HTMLDivElement {
        // Create the main div
        const errorDiv = document.createElement('div');
        errorDiv.id = 'error-occurred';
        errorDiv.classList.add('hide')

        // Create the body div
        const tipDiv = document.createElement('div');
        tipDiv.className = 'error-occurred-tip';
        errorDiv.appendChild(tipDiv);

        // Create the body div
        const bodyDiv = document.createElement('div');
        bodyDiv.className = 'error-occurred-body';
        errorDiv.appendChild(bodyDiv);

        // Create the footer div
        const footerDiv = document.createElement('div');
        footerDiv.className = 'error-occurred-footer';

        // Create the message div
        const messageDiv = document.createElement('div');
        messageDiv.style.flex = 'auto';
        // messageDiv.textContent = 'We apologize for the error. Please report this issue to help us improve the game!';
        footerDiv.appendChild(messageDiv);

        // Create the ignore button
        const ignoreButton = document.createElement('button');
        ignoreButton.type = 'button';
        ignoreButton.id = 'error-ignore';
        ignoreButton.textContent = '무시';
        ignoreButton.onclick = () => ErrorDialog.hideError();
        footerDiv.appendChild(ignoreButton);

        // Create the report button
        const reportButton = document.createElement('button');
        reportButton.type = 'button';
        reportButton.id = 'error-report';
        reportButton.textContent = '오류 신고';
        reportButton.onclick = () => ErrorDialog.reportError();
        footerDiv.appendChild(reportButton);

        // Append the footer to the main div
        errorDiv.appendChild(footerDiv);

        return errorDiv;
    }

    static showError(text: string) {
        if( Setting.hide_bug_report ) {
            return
        }
        if (text.endsWith("UndoRequest\n")) {
            ErrorDialog.error_occurred_body_tip.innerHTML = `대부분 실제 충돌이 아닙니다.
• 되돌리기를 누르고 다른 방법으로 시도하세요.

오류 신고 전에 다음을 확인하세요.
• 올바른 목표를 선택했는지
• 효과의 비용을 지불했는지
• 해결되지 않은 강제 효과가 있는지`;
        } else {
            ErrorDialog.error_occurred_body_tip.innerHTML = ""
        }
        ErrorDialog.last_error_text = text
        ErrorDialog.error_occurred_div.classList.remove('hide');
        ErrorDialog.error_occurred_body_div!.innerHTML = text;
    }

    static hideError() {
        ErrorDialog.error_occurred_div.classList.add('hide');
    }

    static reportError() {
        ErrorDialog.hideError()
        Command.uploadSave("Crash", ErrorDialog.error_occurred_body_div!.innerText)
    }
}

