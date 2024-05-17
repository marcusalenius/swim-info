
window.addEventListener('click', event => {
    const element = event.target;
    if (element.classList.contains('event-item')) {
        handleEventItemClick(element);
    } else if (element.classList.contains('heat-container')) {
        handleHeatContainerClick(element);
    } else if (element.classList.contains('swimmer-container')) {
        handleSwimmerContainerClick(element);
    } 
});


function handleEventItemClick(element) {
    // clicked on the selected event-item
    if (element.classList.contains('event-selected')) {
        element.classList.remove('event-selected');
        const allRightColumns = document.querySelectorAll('.right-column');
        allRightColumns.forEach(column => {
            column.classList.add('hidden');
        });    
        return;
    }

    // switch the selected event-item
    const allEventItems = document.querySelectorAll('.event-item');
    allEventItems.forEach(item => {
        item.classList.remove('event-selected');
    });
    element.classList.add('event-selected');

    // switch shown right column
    const allRightColumns = document.querySelectorAll('.right-column');
    allRightColumns.forEach(column => {
        column.classList.add('hidden');
    });
    const numericId = element.id.replace('event-item-', '');
    const thisRightColumn = document
        .querySelector(`#right-column-${numericId}`);
    thisRightColumn.classList.remove('hidden');
}

function openHeatContent(element) {
    // get padding of heat-content
    const cssRules = document.styleSheets[0].cssRules;
    const heatContentIndex = Object.keys(cssRules).find(
        key => cssRules[key].selectorText === '.heat-content');
    const paddingTop = cssRules[heatContentIndex].style.paddingTop;
    const paddingBottom = cssRules[heatContentIndex].style.paddingBottom;
    const padding = parseInt(paddingTop) + parseInt(paddingBottom);
    
    const heatContent = element.querySelector('.heat-content');
    // console.log("opening - correct call:", heatContent.style.maxHeight === null);
    newHeight = parseInt(heatContent.scrollHeight) + padding;
    heatContent.style.maxHeight = newHeight.toString() + "px";
}

function closeHeatContent(element) {
    const heatContent = element.querySelector('.heat-content');
    // console.log("closing - correct call:", heatContent.style.maxHeight !== null);
    // console.log(element.querySelector('p').innerHTML);
    heatContent.style.maxHeight = null;
}

function handleHeatContainerClick(element) {
    // clicked on the selected heat-container
    if (element.classList.contains('heat-selected')) {
        element.classList.remove('heat-selected');
        element.querySelector('.heat-content').classList.add('hidden');
        closeHeatContent(element);
        return;
    }

    // switch the selected heat-container
    const allHeatContainers = document.querySelectorAll('.heat-container');
    allHeatContainers.forEach(container => {
        container.classList.remove('heat-selected');
    });
    element.classList.add('heat-selected');

    // switch shown heat-content
    console.log("closing all other heat-content");
    allHeatContainers.forEach(container => {
        const heatContent = container.querySelector('.heat-content');
        if (!heatContent.classList.contains('hidden')) {
            heatContent.classList.add('hidden');
            closeHeatContent(container);    
        }
    });
    console.log("opening clicked heat-content");
    if (element.querySelector('.heat-content').classList.contains('hidden')) {
        openHeatContent(element);
        element.querySelector('.heat-content').classList.remove('hidden');
    }
}

function handleSwimmerContainerClick(element) {
    // clicked on the selected swimmer-container
    if (element.classList.contains('swimmer-selected')) {
        element.classList.remove('swimmer-selected');
        element.querySelector('.swimmer-content').classList.add('hidden');
        return;
    }

    // show the selected swimmer-container
    element.classList.add('swimmer-selected');

    // show swimmer-content
    element.querySelector('.swimmer-content').classList.remove('hidden');
}