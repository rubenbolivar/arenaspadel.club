// Modal para mostrar las imágenes de comprobante de pago
document.addEventListener('DOMContentLoaded', function() {
    // Crear el modal y agregarlo al DOM si no existe
    if (!document.getElementById('imageModal')) {
        const modalHTML = `
            <div id="imageModal" class="image-modal">
                <div class="image-modal-content">
                    <span class="image-modal-close">&times;</span>
                    <h2 id="imageModalTitle"></h2>
                    <img id="imageModalImg" src="" alt="Comprobante de pago">
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Agregar el listener para cerrar el modal
        document.querySelector('.image-modal-close').addEventListener('click', function() {
            document.getElementById('imageModal').style.display = 'none';
        });
        
        // Cerrar el modal al hacer clic fuera de él
        window.addEventListener('click', function(event) {
            if (event.target == document.getElementById('imageModal')) {
                document.getElementById('imageModal').style.display = 'none';
            }
        });
    }
});

// Función para mostrar el modal con la imagen
function showImageModal(imageUrl, title) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('imageModalImg');
    const modalTitle = document.getElementById('imageModalTitle');
    
    modalTitle.textContent = title;
    modalImg.src = imageUrl;
    modal.style.display = 'block';
}
