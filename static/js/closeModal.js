
function createModalCloseListener(elementId) {

    var dialog = document.getElementById(elementId);

    console.log(dialog);
    console.log('showing dialog')

    // Close the dialog when the backdrop is clicked.
    dialog.addEventListener('click', (event) => {
        var target = event.target;
        var boundingBox = dialog.getBoundingClientRect();

        if (boundingBox.top <= event.clientY && event.clientY <= boundingBox.top + boundingBox.height
            && boundingBox.left <= event.clientX && event.clientX <= boundingBox.left + boundingBox.width) {
            return;
        }
        dialog.close();
    });
    // remove listener
    dialog.removeEventListener('click', createModalCloseListener);

}