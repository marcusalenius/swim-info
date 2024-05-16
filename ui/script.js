
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

function handleHeatContainerClick(element) {
    // clicked on the selected heat-container
    if (element.classList.contains('heat-selected')) {
        element.classList.remove('heat-selected');
        element.querySelector('.heat-content').classList.add('hidden');
        return;
    }

    // switch the selected heat-container
    const allHeatContainers = document.querySelectorAll('.heat-container');
    allHeatContainers.forEach(container => {
        container.classList.remove('heat-selected');
    });
    element.classList.add('heat-selected');

    // switch shown heat-content
    allHeatContainers.forEach(container => {
        const heatContent = container.querySelector('.heat-content');
        heatContent.classList.add('hidden');
    });
    element.querySelector('.heat-content').classList.remove('hidden');
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