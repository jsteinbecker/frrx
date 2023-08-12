import {computePosition} from '@floating-ui/dom';

export default function initShiftsModals() {
    let modal = document.getElementById('phase-floating');
    let relativeTo = document.getElementById('phase-reference');

    let position = computePosition(modal, relativeTo, 'bottom', 'center');
    modal.style.top = position.top + 'px';
    modal.style.left = position.left + 'px';
    modal.style.display = 'block';
}


