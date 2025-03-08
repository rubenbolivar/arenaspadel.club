from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Court, Reservation, RentalItem, ReservationRental
from .serializers import CourtSerializer, ReservationSerializer

# Template Views
@login_required
def court_reserve_view(request, court_id):
    court = get_object_or_404(Court, id=court_id)
    
    if request.method == 'POST':
        date = request.POST.get('date')
        hours_str = request.POST.get('hours')
        
        if date and hours_str:
            try:
                # Parse date and hours
                selected_date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
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
                    timezone.datetime.combine(selected_date, timezone.datetime.min.time().replace(hour=selected_hours[0]))
                )
                end_datetime = timezone.make_aware(
                    timezone.datetime.combine(selected_date, timezone.datetime.min.time().replace(hour=selected_hours[-1] + 1))
                )
                
                # Check if any of the selected hours are already reserved or in the past
                current_time = timezone.now()
                min_advance_minutes = 10
                
                for hour in selected_hours:
                    hour_start = timezone.make_aware(
                        timezone.datetime.combine(selected_date, timezone.datetime.min.time().replace(hour=hour)),
                        timezone.get_current_timezone()
                    )
                    hour_end = hour_start + timezone.timedelta(hours=1)
                    
                    # Check if the hour is too soon (less than minimum advance time)
                    if hour_start <= current_time + timezone.timedelta(minutes=min_advance_minutes):
                        messages.error(request, f'La hora {hour}:00 debe reservarse con al menos {min_advance_minutes} minutos de anticipación')
                        return redirect('court_detail', court_id=court_id)
                    
                    if Reservation.objects.filter(
                        court=court,
                        status__in=['confirmed', 'pending_payment'],
                        start_time__lt=hour_end,
                        end_time__gt=hour_start
                    ).exists():
                        messages.error(request, f'La hora {hour}:00 ya no está disponible')
                        return redirect('court_detail', court_id=court_id)
                
                # Create the reservation with pending_payment status
                reservation = Reservation.objects.create(
                    user=request.user,
                    court=court,
                    start_time=start_datetime,
                    end_time=end_datetime,
                    status='pending_payment'
                )
                
                # Redirigir a la selección de implementos en alquiler
                return redirect('rental_selection', reservation_id=reservation.id)
            except ValueError as e:
                messages.error(request, str(e))
    
    return redirect('court_detail', court_id=court_id)

@login_required
def reservation_confirm_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    context = {
        'reservation': reservation,
        'total': reservation.total_price
    }
    return render(request, 'reservations/reservation_confirm.html', context)

@login_required
def rental_selection_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    # Verificar que la reserva esté en estado pendiente de pago
    if reservation.status != 'pending_payment':
        messages.error(request, _('Esta reserva no está pendiente de pago'))
        return redirect('home')
    
    # Obtener artículos disponibles
    paddles = RentalItem.objects.filter(item_type='PADDLE', available=True)
    balls = RentalItem.objects.filter(item_type='BALLS', available=True)
    
    if request.method == 'POST':
        # Procesar la selección de artículos
        paddle_id = request.POST.get('paddle')
        paddle_quantity = int(request.POST.get('paddle_quantity', 0))
        balls_id = request.POST.get('balls')
        balls_quantity = int(request.POST.get('balls_quantity', 1))
        
        # Guardar selección de palas
        if paddle_id and paddle_quantity > 0:
            paddle = get_object_or_404(RentalItem, id=paddle_id)
            ReservationRental.objects.create(
                reservation=reservation,
                item=paddle,
                quantity=paddle_quantity,
                unit_price=paddle.price
            )
        
        # Guardar selección de pelotas
        if balls_id and balls_quantity > 0:
            balls = get_object_or_404(RentalItem, id=balls_id)
            ReservationRental.objects.create(
                reservation=reservation,
                item=balls,
                quantity=balls_quantity,
                unit_price=balls.price
            )
        
        # Redirigir a selección de método de pago
        return redirect('payments:payment_select', reservation_id=reservation.id)
    
    context = {
        'reservation': reservation,
        'paddles': paddles,
        'balls': balls
    }
    
    return render(request, 'reservations/rental_selection.html', context)

# API Views
class CourtViewSet(viewsets.ModelViewSet):
    queryset = Court.objects.all()
    serializer_class = CourtSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CourtAvailabilityView(APIView):
    def get(self, request, court_id):
        court = get_object_or_404(Court, id=court_id)
        date = request.query_params.get('date')
        
        if not date:
            return Response({'error': 'Date parameter is required'}, status=400)
        
        try:
            date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=400)
        
        # Get all reservations for this court on this date
        reservations = Reservation.objects.filter(
            court=court,
            start_time__date=date,
            status__in=['confirmed', 'pending_payment']  # Added pending_payment to status check
        )
        
        # Create a list of all hours in a day
        hours = list(range(7, 23))  # 7 AM to 10 PM
        
        # Get current time
        current_time = timezone.now()
        current_date = current_time.date()
        
        # Mark hours as unavailable if there's a reservation or if they've already passed for today
        available_hours = []
        for hour in hours:
            hour_start = timezone.make_aware(
                timezone.datetime.combine(date, timezone.datetime.min.time().replace(hour=hour)),
                timezone.get_current_timezone()
            )
            hour_end = hour_start + timezone.timedelta(hours=1)
            
            # Check if the hour has already passed for today
            if date == current_date and hour_start <= current_time:
                is_available = False
            else:
                is_available = not reservations.filter(
                    start_time__lt=hour_end,
                    end_time__gt=hour_start
                ).exists()
            
            if is_available:
                available_hours.append(hour)
        
        return Response({
            'date': date,
            'available_hours': available_hours
        })

class CourtScheduleView(APIView):
    def get(self, request, court_id):
        court = get_object_or_404(Court, id=court_id)
        start_date = timezone.now().date()
        end_date = start_date + timezone.timedelta(days=7)
        
        # Get all reservations for this period
        reservations = Reservation.objects.filter(
            court=court,
            start_time__date__range=[start_date, end_date],
            status__in=['confirmed', 'pending_payment']  # Added pending_payment to status check
        )
        
        # Create schedule data
        schedule = []
        current_date = start_date
        while current_date <= end_date:
            day_reservations = reservations.filter(start_time__date=current_date)
            schedule.append({
                'date': current_date,
                'reservations': ReservationSerializer(day_reservations, many=True).data
            })
            current_date += timezone.timedelta(days=1)
        
        return Response(schedule)

class UserReservationsView(generics.ListAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)
