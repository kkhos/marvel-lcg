import { Lib } from './lib.js'
import { Setting } from "./settings.js";
import { HoverCard } from './hover.js';
import { MobileForecast } from './mobile-forecast.js';

export class Scene {
    static scale: number = 0
    // Keep logical board coordinates constant throughout a game session.
    static mobileBoardWidth = 0

    static init() {
        const mobile = /Android|iPhone|iPad/i.test(navigator.userAgent) || matchMedia('(pointer: coarse)').matches;
        document.body.classList.toggle('mobile-layout', mobile);
        if (mobile) {
            // Keep the existing game controls and handlers, but separate their
            // layout from the camera so prompts cannot cover selectable cards.
            const rail = document.createElement('aside');
            rail.id = 'mobile-action-rail';
            rail.setAttribute('aria-label', '게임 진행 및 능력 선택');
            const prompt = document.getElementById('prompt-box-container')!;
            const options = document.getElementById('option-buttons')!;
            const controls = document.createElement('div');
            controls.id = 'mobile-action-confirm';
            controls.append(document.getElementById('btn-end')!, document.getElementById('btn-ok')!);
            const header = document.createElement('header');
            header.id = 'mobile-progress-bar';
            header.setAttribute('aria-label', '게임 진행 상황');
            header.append(prompt);
            MobileForecast.init(header);
            rail.setAttribute('aria-label', '능력 선택 및 확인');
            rail.append(options, controls);
            document.body.append(header, rail);
        }
        // Layout viewport is stable when transient Android bars or dialogs
        // change only visualViewport. Coalesce genuine resizes to one frame.
        let resizeFrame = 0;
        const scheduleResize = () => {
            if (resizeFrame) return;
            resizeFrame = requestAnimationFrame(() => {
                resizeFrame = 0;
                adjustSceneScale();
            });
        };
        document.addEventListener('DOMContentLoaded', scheduleResize);
        adjustSceneScale();
        window.addEventListener('resize', mobile ? scheduleResize : adjustSceneScale);
        if (mobile) {
            window.addEventListener('pageshow', scheduleResize);
            // Android immersive mode can report a smaller actual visible
            // viewport than the layout viewport. Coalesce and ignore no-ops.
            window.visualViewport?.addEventListener('resize', scheduleResize);
            window.visualViewport?.addEventListener('scroll', scheduleResize);
        }

        // import { HoverCard } from "./hover.js";
        if( Setting.scene_3d ) {
            Lib.loader.loadCSS("./css./marvel./scene-3d.css")
            document.body.classList.add('scene-3d')
        }
    }
}

// Function to convert scene position to window position
export function convertScenePosToWindowPos(sceneX: number, sceneY: number) {
    const scene = document.getElementById('scene')!;
    const rect = scene.getBoundingClientRect(); // Get the bounding rectangle of the scene

    // Get the current scale of the scene
    const scale = Scene.scale; // Assuming Scene.scale holds the current scale value

    // Calculate the window position
    const windowX = (sceneX * scale) + rect.left; // Adjusted X position in window coordinates
    const windowY = (sceneY * scale) + rect.top;  // Adjusted Y position in window coordinates

    return { x: windowX, y: windowY };
}

// Function to get mouse position relative to the scene
export function getMousePositionInScene(windowX: number, windowY: number) {
    const scene = document.getElementById('scene')!;
    const rect = scene.getBoundingClientRect(); // Get the bounding rectangle of the scene

    // Calculate the mouse position relative to the scene
    const mouseX = windowX - rect.left; // Mouse X relative to the scene
    const mouseY = windowY - rect.top;  // Mouse Y relative to the scene

    // Adjust for scaling
    const scale = Scene.scale; // Extract the scale value
    const sceneX = mouseX / scale; // Adjusted X position
    const sceneY = mouseY / scale; // Adjusted Y position

    return { x: sceneX, y: sceneY };
}

export function adjustSceneScale() {
    const camera = document.getElementById('camera')!;
    const rootStyles = getComputedStyle(document.documentElement); // Get the root element's styles

    let sceneWidth = parseFloat(rootStyles.getPropertyValue('--scene-width'));
    const sceneHeight = parseFloat(rootStyles.getPropertyValue('--scene-height'));
    const mobile = document.body.classList.contains('mobile-layout');
    const vv = mobile && window.visualViewport?.scale === 1 ? window.visualViewport : null;
    const viewportWidth = mobile ? Math.min(window.innerWidth, document.documentElement.clientWidth || window.innerWidth, vv?.width || Infinity) : window.innerWidth;
    const viewportHeight = mobile ? Math.min(window.innerHeight, document.documentElement.clientHeight || window.innerHeight, vv?.height || Infinity) : window.innerHeight;
    if (![viewportWidth, viewportHeight, sceneWidth, sceneHeight].every(n => Number.isFinite(n) && n > 0)) return;
    const originX = vv ? Math.max(0, vv.offsetLeft) : 0;
    const originY = vv ? Math.max(0, vv.offsetTop) : 0;
    const header = mobile ? document.getElementById('mobile-progress-bar') : null;
    
    if (mobile) {
        const body = document.body.style;
        for (const [name, value] of Object.entries({
            '--mobile-vp-left': originX, '--mobile-vp-top': originY,
            '--mobile-vp-width': viewportWidth, '--mobile-vp-height': viewportHeight
        })) {
            const px = `${value}px`;
            if (body.getPropertyValue(name) !== px) body.setProperty(name, px);
        }
    }
    const headerHeight = header?.offsetHeight ?? 0;
    const boardWidth = viewportWidth;
    const boardHeight = viewportHeight - headerHeight;
    if (boardWidth <= 0 || boardHeight <= 0) return;

    // Widen the logical tabletop on wide phones rather than leaving large
    // blank side margins. Preserve the original card dimensions and height.
    // Initialize only once; later keyboard/system viewport changes must not
    // cause a card re-layout or change engine/selection state.
    if (mobile && !Scene.mobileBoardWidth) {
        Scene.mobileBoardWidth = Math.max(sceneWidth, Math.round(boardWidth * sceneHeight / boardHeight));
        document.documentElement.style.setProperty('--scene-width', String(Scene.mobileBoardWidth));
        // Give each upper-right pile room even for a landscape scheme card.
        const anchors: Record<string, number> = {
            'victory-display': 880, 'area-removed': 660, 'removed-pool': 660,
            'nemesis-pool': 440, 'area-advanced': 220,
            'area-schemes-main': 40, 'area-schemes-side': 40
        };
        for (const [id, inset] of Object.entries(anchors)) {
            document.getElementById(id)?.style.setProperty('--x', String(Scene.mobileBoardWidth - inset));
        }
    }
    if (mobile && Scene.mobileBoardWidth) sceneWidth = Scene.mobileBoardWidth;
    const nextScale = Math.min(boardWidth / sceneWidth, boardHeight / sceneHeight);
    const left = `${originX + (boardWidth - sceneWidth * nextScale) / 2}px`;
    const top = `${originY + headerHeight + (boardHeight - sceneHeight * nextScale) / 2}px`;
    if (mobile && Scene.scale === nextScale && camera.style.left === left &&
        camera.style.top === top && camera.style.display === "unset") return;
    Scene.scale = nextScale;

    // Apply the scale transformation only for a genuine layout change.
    camera.style.transform = `scale(${Scene.scale})`;
    if( Setting.scene_3d ) {
        document.getElementById('scene')!.style.transform = `scale(1) rotateX(20deg)`;
    }
    camera.style.display = "unset";

    // Center the scene in the viewport
    camera.style.left = left;
    camera.style.top = top;

    // Set the new value for the CSS variable
    // Must use `parseInt`
    const x = parseInt(rootStyles.getPropertyValue('--font-size'));
    document.documentElement.style.setProperty('--font-size-out', `${x * Scene.scale}px`);

    HoverCard.updateRect()
}

