class NotificationManager {
    constructor() {
        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        document.body.appendChild(this.container);
    }

    show(message, type = 'success', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        let icon = '';
        switch(type) {
            case 'success':
                icon = '<i class="fas fa-check-circle notification-icon"></i>';
                break;
            case 'error':
                icon = '<i class="fas fa-exclamation-circle notification-icon"></i>';
                break;
            case 'warning':
                icon = '<i class="fas fa-exclamation-triangle notification-icon"></i>';
                break;
        }

        notification.innerHTML = `
            ${icon}
            <span>${message}</span>
        `;

        this.container.appendChild(notification);
        
        // Trigger reflow
        notification.offsetHeight;
        
        // Add show class for animation
        notification.classList.add('show');

        // Remove notification after duration
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                this.container.removeChild(notification);
            }, 300);
        }, duration);
    }
}

// Initialize notification manager
const notifications = new NotificationManager();

// Function to show reservation confirmation
function showReservationConfirmation(courtName, date, time) {
    notifications.show(
        `¡Reserva confirmada! Has reservado la ${courtName} para el ${date} de ${time}.`,
        'success'
    );
}

// Function to show cancellation confirmation
function showCancellationConfirmation() {
    notifications.show(
        'La reserva ha sido cancelada exitosamente.',
        'success'
    );
}

// Function to show payment confirmation
function showPaymentConfirmation(amount) {
    notifications.show(
        `¡Pago recibido! Se ha procesado el pago de $${amount} exitosamente.`,
        'success'
    );
}

// Function to show error message
function showError(message) {
    notifications.show(
        message,
        'error'
    );
}

// Add event listeners for reservation actions
document.addEventListener('DOMContentLoaded', function() {
    // Confirm reservation button
    const confirmButtons = document.querySelectorAll('.confirm-reservation');
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const courtName = this.dataset.court;
            const date = this.dataset.date;
            const time = this.dataset.time;
            showReservationConfirmation(courtName, date, time);
        });
    });

    // Cancel reservation button
    const cancelButtons = document.querySelectorAll('.cancel-reservation');
    cancelButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (confirm('¿Estás seguro de que deseas cancelar esta reserva?')) {
                showCancellationConfirmation();
            }
        });
    });
});
