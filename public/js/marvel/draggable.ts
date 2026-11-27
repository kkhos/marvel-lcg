const draggables = document.querySelectorAll<HTMLElement>('.draggable');

draggables.forEach(draggable => {
    let pointerId: number | null = null;
    let offsetX = 0, offsetY = 0;
    draggable.style.touchAction = 'none';

    draggable.addEventListener('pointerdown', e => {
        if (draggable.closest('#mobile-action-rail')) return;
        if (!e.isPrimary || e.button !== 0 || pointerId !== null) return;
        if ((e.target as Element).closest('button,input,select,textarea,a,[role="button"],#prompt-box-close,#prompt-box-lock')) return;
        pointerId = e.pointerId;
        offsetX = e.clientX - draggable.getBoundingClientRect().left;
        offsetY = e.clientY - draggable.getBoundingClientRect().top;
        draggable.setPointerCapture(pointerId);
    });
    draggable.addEventListener('pointermove', e => {
        if (e.pointerId !== pointerId) return;
        draggable.style.left = `${Math.max(0, Math.min(window.innerWidth - draggable.offsetWidth, e.clientX - offsetX))}px`;
        draggable.style.top = `${Math.max(0, Math.min(window.innerHeight - draggable.offsetHeight, e.clientY - offsetY))}px`;
    });
    const finish = (e: PointerEvent) => {
        if (e.pointerId !== pointerId) return;
        pointerId = null;
        if (draggable.hasPointerCapture(e.pointerId)) draggable.releasePointerCapture(e.pointerId);
    };
    draggable.addEventListener('pointerup', finish);
    draggable.addEventListener('pointercancel', finish);
    draggable.addEventListener('lostpointercapture', finish);
});

export function centerDraggableDiv(draggable: HTMLElement) {
    if (draggable.closest('#mobile-action-rail')) return;
    const bodyWidth = document.body.clientWidth;
    const divWidth = draggable.clientWidth;
    const centerX = (bodyWidth - divWidth) / 2;
    draggable.style.left = `${centerX}px`;
}
