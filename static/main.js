const modalButton = document.getElementById('open-modal-button');
const closeButton = document.getElementById('close-modal-button');
closeButton.addEventListener('click', () => {
    const modalView = document.getElementById('modal-view');
    modalView.classList.remove('is-active');
});
modalButton.addEventListener('click', () => {
    const modalView = document.getElementById('modal-view');
    modalView.classList.add('is-active');
});