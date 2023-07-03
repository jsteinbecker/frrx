document.addEventListener('DOMContentLoaded', function() {

    const tooltipDiv = document.querySelector('.tippr-tooltip');
    const elementsWithDataTip = document.querySelectorAll('[data-tippr]');

    elementsWithDataTip.forEach((element) => {

        element.addEventListener('mousemove', (event) => {

            const tooltipText = event.target.closest('[data-tippr]').getAttribute('data-tippr');
            tooltipDiv.textContent = tooltipText;

            // Getting the cursor's x and y coordinates
            const x = event.clientX;
            const y = event.clientY;

            // Account for page scroll
            const scrollX = window.scrollX || window.pageXOffset;
            const scrollY = window.scrollY || window.pageYOffset;

            // Getting the element's dimensions
            const elementWidth = element.offsetWidth;
            const elementHeight = element.offsetHeight;

            // Getting the tooltip's dimensions
            const tooltipWidth = tooltipDiv.offsetWidth;
            const tooltipHeight = tooltipDiv.offsetHeight;

            // Setting the tooltip's position based on the element's position
            tooltipDiv.style.top = `${y - tooltipHeight}px`;
            tooltipDiv.style.left = `${x - tooltipWidth / 2 * 2.05}px`;
            tooltipDiv.style.display = 'block';


        });

        element.addEventListener('mouseleave', (event) => {
            let relatedTarget = event.relatedTarget;
            while (relatedTarget) {
                if (relatedTarget === element) return;
                relatedTarget = relatedTarget.parentNode;
            }
            tooltipDiv.style.display = 'none';
        });
    });
});
