interface ImageEntry {
    source: string;
    imageUrl: string;
    complete: boolean;
    failures: number;
    bindings: Set<ImageBinding>;
    timer?: number;
}

interface ImageBinding {
    element: HTMLElement;
    key: string;
    entry: ImageEntry;
    apply: (url: string) => void;
}

// Share downloads and recovery between duplicate cards, thumbnails and previews.
export class CardImages {
    private static entries = new Map<string, ImageEntry>();
    private static bindings = new WeakMap<HTMLElement, Map<string, ImageBinding>>();
    private static orientations = new Map<string, Promise<string>>();

    static releaseAll(): void {
        for (const entry of this.entries.values()) {
            if (entry.timer !== undefined) window.clearTimeout(entry.timer);
            entry.bindings.clear();
            if (entry.imageUrl) URL.revokeObjectURL(entry.imageUrl);
        }
        this.entries.clear();
        this.bindings = new WeakMap();
        this.orientations.clear();
    }

    static setImage(image: HTMLImageElement, source: string): void {
        this.bind(image, 'src', source, url => image.src = url);
    }

    static setBackground(element: HTMLElement, property: string, source: string, detectOrientation = false): void {
        this.bind(element, property, source, url => {
            const value = url ? `url("${url}")` : 'none';
            const unchanged = element.style.getPropertyValue(property) === value;
            element.style.setProperty(property, value);
            if (!detectOrientation) return;
            if (unchanged && element.hasAttribute('data-art-orientation') && url) return;
            element.removeAttribute('data-art-orientation');
            if (!url) return;
            element.dataset.artOrientation = 'pending';
            // Decode the actual delivered blob, not the card type: imported
            // packs can contain native landscape artwork while legacy art is
            // stored in a portrait bitmap that needs the original rotation.
            let orientation = this.orientations.get(url);
            if (!orientation) {
                orientation = new Promise<string>(resolve => {
                    const image = new Image();
                    image.onload = () => resolve(image.naturalWidth > image.naturalHeight ? 'landscape' : 'portrait');
                    image.onerror = () => resolve('unknown');
                    image.src = url;
                });
                this.orientations.set(url, orientation);
            }
            void orientation.then(result => {
                if (element.style.getPropertyValue(property) === value)
                    element.dataset.artOrientation = result;
            });
        });
    }

    private static bind(element: HTMLElement, key: string, source: string, apply: (url: string) => void): void {
        let bindings = this.bindings.get(element);
        if (!bindings) {
            bindings = new Map();
            this.bindings.set(element, bindings);
        }
        const previous = bindings.get(key);
        if (!source) {
            if (previous) this.removeBinding(previous);
            if (key === 'src') (element as HTMLImageElement).removeAttribute('src');
            else apply('');
            return;
        }
        const url = new URL(source, document.baseURI).href;
        if (previous?.entry.source === url) {
            if (previous.entry.imageUrl || key !== 'src') apply(previous.entry.imageUrl);
            return;
        }
        if (previous) this.removeBinding(previous);

        let entry = this.entries.get(url);
        const start = !entry;
        if (!entry) {
            entry = { source: url, imageUrl: '', complete: false, failures: 0, bindings: new Set() };
            this.entries.set(url, entry);
        }
        const binding = { element, key, entry, apply };
        bindings.set(key, binding);
        if (!entry.complete) entry.bindings.add(binding);
        // Do not make a second, unmanaged request through the original img URL.
        if (entry.imageUrl || key !== 'src') apply(entry.imageUrl);
        else (element as HTMLImageElement).removeAttribute('src');
        if (start) void this.download(entry);
    }

    private static removeBinding(binding: ImageBinding): void {
        this.bindings.get(binding.element)?.delete(binding.key);
        const entry = binding.entry;
        entry.bindings.delete(binding);
        if (!entry.complete && entry.bindings.size === 0) {
            if (entry.timer !== undefined) window.clearTimeout(entry.timer);
            this.entries.delete(entry.source);
            if (entry.imageUrl) {
                this.orientations.delete(entry.imageUrl);
                URL.revokeObjectURL(entry.imageUrl);
            }
        }
    }

    private static prune(entry: ImageEntry): boolean {
        for (const binding of entry.bindings) {
            if (!binding.element.isConnected) this.removeBinding(binding);
        }
        return this.entries.get(entry.source) === entry && entry.bindings.size > 0;
    }

    private static async download(entry: ImageEntry): Promise<void> {
        let retrySeconds = 30;
        let pending = false;
        try {
            const response = await fetch(entry.source, { cache: 'no-store' });
            if (!response.ok || !response.headers.get('Content-Type')?.startsWith('image/')) {
                throw new Error('Card image unavailable');
            }
            const blob = await response.blob();
            if (!this.prune(entry)) return;
            const oldUrl = entry.imageUrl;
            entry.imageUrl = URL.createObjectURL(blob);
            for (const binding of entry.bindings) binding.apply(entry.imageUrl);
            if (oldUrl) {
                this.orientations.delete(oldUrl);
                URL.revokeObjectURL(oldUrl);
            }

            const retryHeader = response.headers.get('X-Card-Image-Retry-After');
            const state = response.headers.get('X-Card-Image-State');
            pending = state === 'pending';
            const retry = Number(retryHeader);
            if (!pending && state !== 'error' && (retryHeader === null || !Number.isFinite(retry) || retry <= 0)) {
                entry.complete = true;
                entry.bindings.clear();
                return;
            }
            retrySeconds = Number.isFinite(retry) && retry > 0 ? retry : (pending ? 1 : 30);
        } catch {
            if (!this.prune(entry)) return;
        }
        // An extended outage should not hammer the image providers. The first
        // retry honors the server cooldown; repeated failures back off to 5 min.
        if (pending) entry.failures = 0;
        else entry.failures++;
        const delay = pending ? Math.max(1, retrySeconds)
            : Math.max(retrySeconds, Math.min(300, 30 * 2 ** (entry.failures - 1)));
        entry.timer = window.setTimeout(() => {
            entry.timer = undefined;
            if (this.prune(entry)) void this.download(entry);
        }, delay * 1000 + 100);
    }
}

// Keep bfcache documents intact; unload releases all object URLs and retry timers.
window.addEventListener('pagehide', event => { if (!event.persisted) CardImages.releaseAll(); });
