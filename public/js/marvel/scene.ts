import { Lib } from './lib.js'
import { Setting } from "./settings.js";
import { HoverCard } from './hover.js';

export class Scene {
    static scale: number = 0

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
            rail.append(prompt, options, controls);
            document.body.append(rail);
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
        if (mobile) window.addEventListener('pageshow', scheduleResize);

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

    // Read the width and height from CSS variables
    const sceneWidth = parseFloat(rootStyles.getPropertyValue('--scene-width'));
    const sceneHeight = parseFloat(rootStyles.getPropertyValue('--scene-height'));

    const mobile = document.body.classList.contains('mobile-layout');
    const viewportWidth = mobile ? (document.documentElement.clientWidth || window.innerWidth) : window.innerWidth;
    const viewportHeight = mobile ? (document.documentElement.clientHeight || window.innerHeight) : window.innerHeight;
    if (![viewportWidth, viewportHeight, sceneWidth, sceneHeight].every(n => Number.isFinite(n) && n > 0)) return;

    // Reserve one stable action rail, even when no ability is being chosen.
    // Avoid shifting or resizing the board on each option/prompt update.
    const railWidth = mobile ? (document.getElementById('mobile-action-rail')?.offsetWidth ?? 0) : 0;
    const boardWidth = viewportWidth - railWidth;
    if (boardWidth <= 0) return;
    // Calculate scale factors
    const scaleX = boardWidth / sceneWidth;
    const scaleY = viewportHeight / sceneHeight;
    const nextScale = Math.min(scaleX, scaleY);
    const left = `${(boardWidth - sceneWidth * nextScale) / 2}px`;
    const top = `${(viewportHeight - sceneHeight * nextScale) / 2}px`;
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

