// Court Availability Check
function checkCourtAvailability(courtId, date) {
    fetch(`/api/reservations/courts/${courtId}/availability/?date=${date}`)
        .then(response => response.json())
        .then(data => {
            updateTimeSlots(data.available_slots);
        })
        .catch(error => console.error('Error:', error));
}

// Update Time Slots Display
function updateTimeSlots(availableSlots) {
    const timeSlotsContainer = document.getElementById('time-slots');
    if (!timeSlotsContainer) return;

    timeSlotsContainer.innerHTML = '';
    
    for (let hour = 7; hour < 23; hour++) {
        const timeSlot = document.createElement('div');
        const time = `${hour.toString().padStart(2, '0')}:00`;
        const isAvailable = availableSlots.includes(time);
        
        timeSlot.className = `time-slot ${isAvailable ? 'available' : 'reserved'}`;
        timeSlot.textContent = time;
        
        if (isAvailable) {
            timeSlot.addEventListener('click', () => selectTimeSlot(time));
        }
        
        timeSlotsContainer.appendChild(timeSlot);
    }
}

// Time Slot Selection
function selectTimeSlot(time) {
    const selectedSlot = document.querySelector('.time-slot.selected');
    if (selectedSlot) {
        selectedSlot.classList.remove('selected');
    }
    
    event.target.classList.add('selected');
    document.getElementById('selected_time').value = time;
    updateReservationSummary();
}

// Payment Method Selection
function selectPaymentMethod(method) {
    const paymentCards = document.querySelectorAll('.payment-method-card');
    paymentCards.forEach(card => card.classList.remove('selected'));
    
    const selectedCard = document.querySelector(`[data-payment-method="${method}"]`);
    if (selectedCard) {
        selectedCard.classList.add('selected');
        document.getElementById('payment_method').value = method;
        
        // Show/hide relevant payment information fields
        const paymentFields = document.querySelectorAll('[data-payment-field]');
        paymentFields.forEach(field => {
            field.style.display = field.dataset.paymentField === method ? 'block' : 'none';
        });
    }
}

// Update Reservation Summary
function updateReservationSummary() {
    const court = document.getElementById('court').value;
    const date = document.getElementById('date').value;
    const time = document.getElementById('selected_time').value;
    const hours = document.getElementById('hours').value;
    const rate = parseFloat(document.getElementById('hourly_rate').value);
    
    if (court && date && time && hours && rate) {
        const total = hours * rate;
        document.getElementById('total_amount').textContent = `$${total.toFixed(2)}`;
        document.getElementById('summary_court').textContent = `Arena ${court}`;
        document.getElementById('summary_datetime').textContent = `${date} ${time}`;
        document.getElementById('summary_duration').textContent = `${hours} hora(s)`;
    }
}

// File Upload Preview
function previewFile(input) {
    const preview = document.getElementById('proof-preview');
    const file = input.files[0];
    const reader = new FileReader();

    reader.onloadend = function() {
        preview.src = reader.result;
        preview.style.display = 'block';
    }

    if (file) {
        reader.readAsDataURL(file);
    } else {
        preview.src = '';
        preview.style.display = 'none';
    }
}

// Initialize date picker with disabled past dates
document.addEventListener('DOMContentLoaded', function() {
    const datePicker = document.getElementById('date');
    if (datePicker) {
        const today = new Date().toISOString().split('T')[0];
        datePicker.min = today;
        
        datePicker.addEventListener('change', () => {
            const courtId = document.getElementById('court').value;
            if (courtId) {
                checkCourtAvailability(courtId, datePicker.value);
            }
        });
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Court Availability Calendar
function initializeCalendar(courtId) {
    const calendar = document.getElementById('availability-calendar');
    if (!calendar) return;

    // Get current date
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();

    // Fetch available time slots
    fetchAvailability(courtId, currentYear, currentMonth);
}

function fetchAvailability(courtId, year, month) {
    fetch(`/api/reservations/courts/${courtId}/schedule/?year=${year}&month=${month}`)
        .then(response => response.json())
        .then(data => {
            updateCalendar(data.availability);
        })
        .catch(error => {
            console.error('Error fetching availability:', error);
            showAlert('Error loading availability. Please try again.', 'danger');
        });
}

function updateCalendar(availability) {
    const calendar = document.getElementById('availability-calendar');
    if (!calendar) return;

    calendar.innerHTML = '';
    
    // Add calendar header (days of week)
    const daysOfWeek = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
    daysOfWeek.forEach(day => {
        const dayHeader = document.createElement('div');
        dayHeader.className = 'calendar-cell font-weight-bold';
        dayHeader.textContent = day;
        calendar.appendChild(dayHeader);
    });

    // Add calendar cells
    availability.forEach(slot => {
        const cell = document.createElement('div');
        cell.className = `calendar-cell ${slot.available ? 'available' : 'booked'}`;
        cell.textContent = new Date(slot.date).getDate();
        
        if (slot.available) {
            cell.addEventListener('click', () => selectTimeSlot(slot));
        }
        
        calendar.appendChild(cell);
    });
}

// Reservation Form
function selectTimeSlot(slot) {
    const startTime = document.getElementById('id_start_time');
    const endTime = document.getElementById('id_end_time');
    
    if (startTime && endTime) {
        startTime.value = slot.start_time;
        endTime.value = slot.end_time;
        calculatePrice();
    }
}

function calculatePrice() {
    const startTime = document.getElementById('id_start_time').value;
    const endTime = document.getElementById('id_end_time').value;
    const courtId = document.getElementById('id_court').value;
    
    if (startTime && endTime && courtId) {
        fetch(`/api/reservations/courts/${courtId}/price/?start=${startTime}&end=${endTime}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('total-price').textContent = `$${data.price}`;
            })
            .catch(error => {
                console.error('Error calculating price:', error);
                showAlert('Error calculating price. Please try again.', 'danger');
            });
    }
}

// Payment Processing
function initializePayment() {
    const paymentForm = document.getElementById('payment-form');
    if (!paymentForm) return;

    const paymentMethods = document.querySelectorAll('.payment-method');
    paymentMethods.forEach(method => {
        method.addEventListener('click', () => selectPaymentMethod(method));
    });
}

function selectPaymentMethod(methodElement) {
    // Remove selected class from all methods
    document.querySelectorAll('.payment-method').forEach(method => {
        method.classList.remove('selected');
    });
    
    // Add selected class to chosen method
    methodElement.classList.add('selected');
    
    // Update hidden input
    document.getElementById('id_payment_method').value = methodElement.dataset.method;
    
    // Show/hide relevant payment fields
    togglePaymentFields(methodElement.dataset.method);
}

function togglePaymentFields(method) {
    const stripeFields = document.getElementById('stripe-fields');
    const transferFields = document.getElementById('transfer-fields');
    
    if (stripeFields) stripeFields.style.display = method === 'stripe' ? 'block' : 'none';
    if (transferFields) transferFields.style.display = method === 'transfer' ? 'block' : 'none';
}

// Utility Functions
function showAlert(message, type = 'info') {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type} alert-dismissible fade show`;
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.querySelector('main').insertBefore(alertContainer, document.querySelector('main').firstChild);
}

// Initialize components when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => new bootstrap.Tooltip(tooltip));
    
    // Initialize payment form if present
    initializePayment();
    
    // Initialize calendar if on court detail page
    const courtId = document.getElementById('court-id')?.value;
    if (courtId) initializeCalendar(courtId);
    
    // Add event listeners for reservation form
    const reservationForm = document.getElementById('reservation-form');
    if (reservationForm) {
        const timeInputs = reservationForm.querySelectorAll('input[type="time"]');
        timeInputs.forEach(input => {
            input.addEventListener('change', calculatePrice);
        });
    }
});
