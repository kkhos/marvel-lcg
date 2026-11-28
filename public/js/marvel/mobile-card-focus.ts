// Mobile presentation only: preserve engine coordinates and card identity.
export class MobileCardFocus {
    private static key = 'marvel.mobile.dynamicCardFocus';
    private static enabled = true;
    private static phase = 'neutral';

    static init() {
        try { this.enabled = localStorage.getItem(this.key) !== 'off'; } catch {}
        this.apply();
    }

    static setPhase(phase: string) {
        this.phase = /^Player(?: \d+)? Turn$/.test(phase) ? 'player' :
            ['Main Scheme Place Threat','Enemy Activation','Deal Encounter Cards','Reveal Encounter Cards'].includes(phase)
                ? 'villain' : 'neutral';
        this.apply();
    }

    private static apply() {
        if (document.body.classList.contains('mobile-layout')) {
            document.body.dataset.cardFocus = this.enabled ? this.phase : 'off';
        }
    }

    static toggleButton(): HTMLButtonElement {
        const button = document.createElement('button');
        button.type = 'button';
        button.id = 'mobile-dynamic-card-focus';
        button.className = 'button';
        const update = () => {
            button.textContent = '동적 카드 확대: ' + (this.enabled ? '켜기' : '끄기');
            button.setAttribute('aria-pressed', String(this.enabled));
        };
        button.onclick = () => {
            this.enabled = !this.enabled;
            try { localStorage.setItem(this.key, this.enabled ? 'on' : 'off'); } catch {}
            this.apply();
            update();
        };
        update();
        return button;
    }
}
