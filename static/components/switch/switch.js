// for switch component
// TODO: add event animation via javascript


function toggleSwitch(wrapper) {
    // Toggle the on class for both elements
    const switchElement = wrapper.querySelector('.switch');
    const circleElement = wrapper.querySelector('.switch-handle');
    const inputElement = wrapper.querySelector('.onoff-switch-input');

    if (switchElement.classList.contains('on')) {
        switchElement.classList.remove('on');
        circleElement.classList.remove('on');
        circleElement.classList.add('off');

        // If you want to store the state in the hidden input (e.g., "on" or "off")
        inputElement.value = 'off';
    } else {
        switchElement.classList.add('on');
        circleElement.classList.add('on');
        circleElement.classList.remove('off');

        inputElement.value = 'on';
    }
}
