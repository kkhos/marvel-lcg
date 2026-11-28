import { ButtonSetting, Setting } from "./settings.js";

export class Music {
    private static sound_bgm = document.getElementById('play-bgm') as HTMLAudioElement;
    private static sound_cache: Record<string, HTMLAudioElement> = {};

    private static bgmWanted = false;

    static initBgm() {
        Music.bgmWanted = Boolean(ButtonSetting.bgm_on);
        // Android WebView requires a user gesture to begin playback.
        document.addEventListener('click', () => {
            if (Music.bgmWanted && Music.sound_bgm?.paused) Music.playBgm();
        }, {capture: true});
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState !== 'visible') {
                Music.sound_bgm?.pause();
                for (const sound of Object.values(Music.sound_cache)) sound.pause();
            } else if (Music.bgmWanted) Music.playBgm();
        });
        window.addEventListener('pagehide', () => Music.pauseBgm());
    }

    static playBgm() {
        if (!Music.sound_bgm || !ButtonSetting.bgm_on) return;
        Music.bgmWanted = true;
        if (document.visibilityState !== 'visible') return;
        if (!Music.sound_bgm.getAttribute('src') || Music.sound_bgm.getAttribute('src') === '') {
            Music.sound_bgm.src = '/public/audio/hero-theme.mp3';
        }
        Music.sound_bgm.loop = true;
        Music.sound_bgm.volume = 0.12;
        void Music.sound_bgm.play().catch(() => {});
    }

    static pauseBgm() {
        Music.bgmWanted = false;
        Music.sound_bgm?.pause();
    }

    static playClickCardSound() {
        Music.doPlaySound('flip.wav');
    }

    static preloadSound(sound_name: string) {
        if (!Music.sound_cache[sound_name]) {
            const audio = new Audio(sound_name);
            Music.sound_cache[sound_name] = audio;
        }
    }

    static doPlaySound(sound_name: string) {

        if( !Setting.is_debug && document.visibilityState != 'visible'){
            return;
        }

        if (!ButtonSetting.music_on) {
            return;
        }

        console.log("Sound:", sound_name)

        // Preload the sound if not already in cache
        Music.preloadSound(sound_name);

        // Use the cached sound
        const sound = Music.sound_cache[sound_name];
        sound.volume = 0.2;

        // Stop the current sound if it's playing
        if (!sound.paused) {
            sound.pause();
            sound.currentTime = 0; // Reset to the beginning
        }

        sound.play().catch((error) => {
        });
    }
}
