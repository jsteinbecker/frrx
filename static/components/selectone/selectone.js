

function selectOneOptionClicked(element) {
    let option = element;
    let selectOne = option.parentElement;
    let selectOneOptions = selectOne.querySelectorAll(".selectone-option");
    let hiddenInput = selectOne.querySelector("input[type=hidden]");

    selectOneOptions.forEach((option) => {
        option.classList.remove("selected");
    }
    );
    option.classList.add("selected");
    hiddenInput.value = option.dataset.value;
}