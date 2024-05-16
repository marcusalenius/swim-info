
window.addEventListener('click', event => {
    const element = event.target;
    if (element.classList.contains('event-item')) {
        handleEventItemClick(element);
    }
});


function handleEventItemClick(element) {
    // switch the selected item
    const allEventItems = document.querySelectorAll('.event-item');
    allEventItems.forEach(item => {
        item.classList.remove('event-selected');
    });
    element.classList.add('event-selected');

    // switch the right column
    const allRightColumns = document.querySelectorAll('.right-column');
    allRightColumns.forEach(column => {
        column.classList.add('hidden');
    });
    const numericId = element.id.replace('event-item-', '');
    const thisRightColumn = document
        .querySelector(`#right-column-${numericId}`);
    thisRightColumn.classList.remove('hidden');
}