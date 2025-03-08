from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils import timezone
from users.forms import UserRegistrationForm, UserLoginForm
from reservations.models import Court, Reservation
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def home(request):
    latest_courts = Court.objects.filter(is_active=True)[:3]
    return render(request, 'home.html', {'latest_courts': latest_courts})

def court_list(request):
    # Get all active courts
    courts = Court.objects.filter(is_active=True)
    
    # Get filter parameters
    date_str = request.GET.get('date')
    time_str = request.GET.get('time')
    
    # Generate available hours (7:00 AM - 11:00 PM)
    available_hours = list(range(7, 23))
    
    # If date and time are provided, filter courts by availability
    if date_str and time_str:
        try:
            # Parse date and time
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            selected_hour = int(time_str)
            
            # Create datetime objects for the selected time slot
            selected_datetime = timezone.make_aware(
                datetime.combine(selected_date, datetime.min.time().replace(hour=selected_hour))
            )
            end_datetime = selected_datetime + timedelta(hours=1)
            
            # Exclude courts that have confirmed reservations during the selected time slot
            unavailable_courts = Court.objects.filter(
                reservations__status__in=['confirmed', 'pending_payment'],
                reservations__start_time__lt=end_datetime,
                reservations__end_time__gt=selected_datetime
            )
            courts = courts.exclude(id__in=unavailable_courts)
            
        except (ValueError, TypeError):
            messages.error(request, 'Por favor, selecciona una fecha y hora válidas.')
    
    context = {
        'courts': courts,
        'available_hours': available_hours,
        'today': timezone.now().date(),
    }
    return render(request, 'courts/court_list.html', context)

def court_detail(request, court_id):
    # Get the court or return 404
    court = get_object_or_404(Court, id=court_id, is_active=True)
    
    # Generate available hours (7:00 AM - 11:00 PM)
    available_hours = list(range(7, 23))
    
    # Generate next 7 days for the calendar display
    today = timezone.now().date()
    next_week_dates = [today + timedelta(days=i) for i in range(7)]
    
    # Initialize context
    context = {
        'court': court,
        'available_hours': available_hours,
        'today': today,
        'next_week_dates': next_week_dates,
        'selected_date': None,
        'selected_hours': [],
        'is_available': False,
    }
    
    # Create a dictionary to store availability for displayed dates
    availability = {}
    current_time = timezone.now()
    
    # Imprimir información de depuración
    logger.info(f"Current time (UTC): {current_time}")
    logger.info(f"Current time (configured timezone): {timezone.localtime(current_time)}")
    logger.info(f"Timezone used: {timezone.get_current_timezone()}")
    
    for date in next_week_dates:
        availability[date] = {}
        for hour in available_hours:
            # Create datetime objects for this time slot
            start_datetime = timezone.make_aware(
                datetime.combine(date, datetime.min.time().replace(hour=hour)),
                timezone.get_current_timezone()
            )
            end_datetime = start_datetime + timedelta(hours=1)
            
            # Permitir reservas con mínima anticipación (solo 10 minutos)
            min_advance_minutes = 10
            reservation_buffer = current_time + timedelta(minutes=min_advance_minutes)
            
            # Check if the time slot has already passed or is too soon
            if start_datetime <= reservation_buffer:
                # Si la fecha es hoy y la hora ya pasó o es muy pronto, marcar como no disponible
                is_slot_available = False
                logger.info(f"Slot {date} {hour}:00 marked unavailable: start_time={start_datetime}, buffer={reservation_buffer}")
            else:
                # Check if there are any confirmed reservations for this time slot
                is_slot_available = not Reservation.objects.filter(
                    court=court,
                    status__in=['confirmed', 'pending_payment'],
                    start_time__lt=end_datetime,
                    end_time__gt=start_datetime
                ).exists()
            
            availability[date][hour] = is_slot_available
    
    context['availability'] = availability
    
    return render(request, 'courts/court_detail.html', context)

@login_required
def create_reservation(request, court_id):
    if request.method == 'POST':
        court = get_object_or_404(Court, id=court_id, is_active=True)
        date_str = request.POST.get('date')
        hours_str = request.POST.get('hours')
        
        try:
            # Parse date and hours
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            selected_hours = [int(h) for h in hours_str.split(',')]
            
            if not selected_hours:
                raise ValueError('No se seleccionaron horas')
            
            # Sort hours to ensure they're consecutive
            selected_hours.sort()
            
            # Verify hours are consecutive
            for i in range(len(selected_hours) - 1):
                if selected_hours[i + 1] != selected_hours[i] + 1:
                    raise ValueError('Las horas seleccionadas deben ser consecutivas')
            
            # Create datetime objects for the reservation
            start_datetime = timezone.make_aware(
                datetime.combine(selected_date, datetime.min.time().replace(hour=selected_hours[0]))
            )
            end_datetime = timezone.make_aware(
                datetime.combine(selected_date, datetime.min.time().replace(hour=selected_hours[-1] + 1))
            )
            
            # Check if any of the selected hours are already reserved
            for hour in selected_hours:
                hour_start = timezone.make_aware(
                    datetime.combine(selected_date, datetime.min.time().replace(hour=hour))
                )
                hour_end = hour_start + timedelta(hours=1)
                
                if Reservation.objects.filter(
                    court=court,
                    status__in=['confirmed', 'pending_payment'],
                    start_time__lt=hour_end,
                    end_time__gt=hour_start
                ).exists():
                    messages.error(request, f'La hora {hour}:00 ya no está disponible')
                    return redirect('court_detail', court_id=court_id)
            
            # Calculate total price (hourly rate × number of hours)
            total_price = court.hourly_rate * len(selected_hours)
            
            # Create the reservation with pending_payment status
            reservation = Reservation.objects.create(
                user=request.user,
                court=court,
                start_time=start_datetime,
                end_time=end_datetime,
                total_price=total_price,
                status='pending_payment'  # Cambiado de 'confirmed' a 'pending_payment'
            )
            
            # Redirect to payment method selection
            return redirect('payment_method_selection', reservation_id=reservation.id)
            
        except ValueError as e:
            messages.error(request, str(e) if str(e) != 'No se seleccionaron horas' else 'Por favor, selecciona al menos una hora')
        except (TypeError, Exception) as e:
            messages.error(request, 'Ha ocurrido un error al procesar la reserva')
    
    return redirect('court_detail', court_id=court_id)

@login_required
def cancel_reservation(request, reservation_id):
    if request.method == 'POST':
        reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
        
        # Get current time
        now = timezone.now()
        
        # Calculate cancellation deadline (6 hours before start time)
        cancellation_deadline = reservation.start_time - timezone.timedelta(hours=6)
        
        # Check if the reservation is in the future and can be cancelled within policy
        if now < cancellation_deadline:
            reservation.status = 'cancelled'
            reservation.save()
            messages.success(request, 'Reserva cancelada exitosamente.')
        elif now < reservation.start_time:
            # Reservation is in the future but within 6-hour window
            messages.error(request, 'Las cancelaciones deben realizarse con al menos 6 horas de antelación. La reserva no ha sido cancelada y deberá abonar el importe total.')
        else:
            # Reservation is already in the past
            messages.error(request, 'No se puede cancelar una reserva pasada.')
    
    return redirect('profile')

@login_required
def profile(request):
    # Get user's reservations
    reservations = Reservation.objects.filter(
        user=request.user
    ).order_by('-start_time')  # Most recent first
    
    # Get current date for comparing with reservation dates
    today = timezone.now().date()
    
    context = {
        'reservations': reservations,
        'today': today
    }
    return render(request, 'users/profile.html', context)

@login_required
def profile_update(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        messages.success(request, 'Perfil actualizado exitosamente.')
        return redirect('profile')
    return redirect('profile')

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, '¡Bienvenido de nuevo!')
            return redirect('home')
    else:
        form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Cuenta creada exitosamente!')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('home')

def terms(request):
    return render(request, 'legal/terms.html')