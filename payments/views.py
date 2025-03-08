from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework import viewsets, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Payment
from .serializers import PaymentSerializer
from reservations.models import Reservation
import stripe
import logging
from django.contrib.admin.sites import site

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PaymentMethodsView(APIView):
    def get(self, request):
        payment_methods = [
            {
                'id': 'stripe',
                'name': 'Credit Card (Stripe)',
                'enabled': bool(settings.STRIPE_PUBLIC_KEY),
            },
            {
                'id': 'transfer',
                'name': 'Bank Transfer',
                'enabled': True,
            },
            {
                'id': 'cash',
                'name': 'Cash',
                'enabled': True,
            }
        ]
        return Response(payment_methods)

@login_required
def payment_method_selection(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    context = {
        'reservation': reservation,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'zelle_email': settings.ZELLE_EMAIL,
        'pago_movil_phone': settings.PAGO_MOVIL_PHONE,
        'pago_movil_bank': settings.PAGO_MOVIL_BANK,
        'pago_movil_id': settings.PAGO_MOVIL_ID,
    }
    return render(request, 'payments/payment_method_selection.html', context)

@login_required
def manual_payment_confirmation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    payment_method = request.GET.get('method', '').upper()
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        proof_image = request.FILES.get('proof_image')
        reference = request.POST.get('reference')
        notes = request.POST.get('notes', '')
        
        # Para pagos en efectivo, configurar un estado y mensaje diferentes
        if payment_method == 'CASH':
            payment_status = 'PENDING'
            payment_notes = "Pago en efectivo pendiente. " + notes
            
            # Para pagos en efectivo, asegurarnos de que la reserva permanezca como pendiente
            reservation.status = 'pending'
            reservation.save()
            
            success_message = 'Tu reserva con pago en efectivo ha sido registrada. Recuerda llegar al menos 30 minutos antes para completar el pago.'
        else:
            payment_status = 'REVIEWING'
            payment_notes = f"Referencia: {reference}"
            success_message = 'Tu confirmación de pago ha sido enviada. Te notificaremos cuando sea verificada.'
        
        payment = Payment.objects.create(
            reservation=reservation,
            user=request.user,
            amount=reservation.total_price,
            payment_method=payment_method,
            status=payment_status,
            proof_image=proof_image,
            notes=payment_notes
        )
        
        # Send email notification only for non-cash payments
        if payment_method != 'CASH':
            try:
                subject = f'Nueva confirmación de pago - Reserva #{reservation.id}'
                html_message = render_to_string('payments/email/payment_confirmation.html', {
                    'payment': payment,
                    'reservation': reservation,
                })
                send_mail(
                    subject,
                    '',
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    html_message=html_message,
                    fail_silently=False,
                )
                logger.info(f"Payment confirmation email sent for reservation #{reservation.id}")
            except Exception as e:
                logger.error(f"Error sending payment confirmation email: {str(e)}")
                # El pago se creó correctamente, solo falló el email
                pass
        else:
            # Para pagos en efectivo, enviar una notificación diferente
            try:
                subject = f'Nueva reserva con pago en efectivo - Reserva #{reservation.id}'
                admin_url = request.build_absolute_uri(reverse('admin:payments_payment_change', args=[payment.id]))
                html_message = render_to_string('payments/email/cash_payment_notification.html', {
                    'payment': payment,
                    'reservation': reservation,
                    'admin_url': admin_url,
                })
                send_mail(
                    subject,
                    '',
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    html_message=html_message,
                    fail_silently=False,
                )
                logger.info(f"Cash payment notification email sent for reservation #{reservation.id}")
            except Exception as e:
                logger.error(f"Error sending cash payment notification email: {str(e)}")
                pass
        
        messages.success(request, success_message)
        
        # Redirigir a una página de resumen del pago con opción de notificar por WhatsApp
        return redirect('payments:payment_success', reservation_id=reservation.id)
    
    context = {
        'reservation': reservation,
        'payment_method': payment_method,
        'pago_movil_bank': settings.PAGO_MOVIL_BANK,
        'pago_movil_phone': settings.PAGO_MOVIL_PHONE,
        'pago_movil_id': settings.PAGO_MOVIL_ID,
        'zelle_email': settings.ZELLE_EMAIL
    }
    return render(request, 'payments/manual_payment_confirmation.html', context)

@login_required
def whatsapp_notification(request, reservation_id):
    """
    Vista para enviar notificación manual por WhatsApp sobre una reserva.
    Muestra un formulario con el mensaje preformateado que el usuario puede revisar.
    """
    reservation = get_object_or_404(Reservation, id=reservation_id)
    admin_phone = settings.ADMIN_WHATSAPP_NUMBER if hasattr(settings, 'ADMIN_WHATSAPP_NUMBER') else "584249743328"
    
    # Formatear la fecha y hora para mejor legibilidad
    start_time = timezone.localtime(reservation.start_time)
    end_time = timezone.localtime(reservation.end_time)
    date_str = start_time.strftime("%d/%m/%Y")
    start_hour = start_time.strftime("%I:%M %p")
    end_hour = end_time.strftime("%I:%M %p")
    
    # Construir mensaje con símbolos de texto en lugar de emojis para compatibilidad
    default_message = (
        "*Nueva Reserva en Arenas Padel Club*\n\n"
        f"*Reserva #*{reservation.id}\n"
        f"*Cliente:* {reservation.user.get_full_name() or reservation.user.username}\n"
        f"*Teléfono:* {reservation.user.profile.phone if hasattr(reservation.user, 'profile') and hasattr(reservation.user.profile, 'phone') else 'No disponible'}\n"
        f"*Fecha:* {date_str}\n"
        f"*Hora:* {start_hour} - {end_hour}\n"
        f"*Cancha:* {reservation.court.name}\n"
        f"*Precio:* ${reservation.total_price}\n\n"
        f"*¡Gracias por reservar con nosotros!*"
    )
    
    if request.method == 'POST':
        message = request.POST.get('message', default_message)
        # El usuario ha revisado el mensaje y desea enviarlo
        # Codificamos el mensaje para la URL
        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://wa.me/{admin_phone}?text={encoded_message}"
        
        # Ya no intentamos guardar en notes porque el modelo no tiene ese campo
        # Simplemente redirigimos al usuario a WhatsApp
        return redirect(whatsapp_url)
    
    context = {
        'reservation': reservation,
        'default_message': default_message,
        'admin_phone': admin_phone
    }
    return render(request, 'payments/whatsapp_notification.html', context)

@login_required
def notify_payment_whatsapp(request, reservation_id):
    """
    Vista para enviar notificación de pago realizado por WhatsApp.
    Permite al usuario notificar rápidamente que ha realizado un pago manual.
    """
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    payment_method = request.GET.get('method', '').upper()
    admin_phone = getattr(settings, 'ADMIN_WHATSAPP_NUMBER', '584249743328')
    
    # Formatear la fecha y hora para mejor legibilidad
    start_time = timezone.localtime(reservation.start_time)
    end_time = timezone.localtime(reservation.end_time)
    date_str = start_time.strftime("%d/%m/%Y")
    start_hour = start_time.strftime("%I:%M %p")
    end_hour = end_time.strftime("%I:%M %p")
    
    # Construir mensaje personalizado para notificación de pago
    default_message = (
        "*Notificación de Pago - Arenas Padel Club*\n\n"
        f"*Reserva #*: {reservation.id}\n"
        f"*Cliente*: {reservation.user.get_full_name() or reservation.user.username}\n"
        f"*Teléfono*: {reservation.user.profile.phone if hasattr(reservation.user, 'profile') and hasattr(reservation.user.profile, 'phone') else 'No disponible'}\n"
        f"*Fecha de la reserva*: {date_str}\n"
        f"*Hora*: {start_hour} - {end_hour}\n"
        f"*Cancha*: {reservation.court.name}\n"
        f"*Precio*: ${format_price(reservation.total_price)}\n"
    )
    
    # Agregar información de artículos alquilados
    rental_items = reservation.rentals.all()
    if rental_items.exists():
        default_message += "\n*Implementos alquilados:*\n"
        for rental in rental_items:
            item_total = rental.quantity * rental.unit_price
            default_message += f"- {rental.item.name} x{rental.quantity}: ${format_price(item_total)}\n"
    
    default_message += f"\n*Método de pago*: {dict(Payment.PAYMENT_METHODS).get(payment_method, 'No especificado')}\n"
    
    # Agregar información de referencia si está disponible
    latest_payment = Payment.objects.filter(reservation=reservation).order_by('-created_at').first()
    if latest_payment and hasattr(latest_payment, 'notes') and latest_payment.notes:
        if "Referencia:" in latest_payment.notes:
            reference = latest_payment.notes.split("Referencia:")[1].strip()
            default_message += f"*Referencia de pago*: {reference}\n"
    
    default_message += "\n*He realizado el pago. Por favor, verifiquen a la brevedad posible.*"
    
    if request.method == 'POST':
        message = request.POST.get('message', default_message)
        # El usuario ha revisado el mensaje y desea enviarlo
        # Codificamos el mensaje para la URL
        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://wa.me/{admin_phone}?text={encoded_message}"
        
        return redirect(whatsapp_url)
    
    context = {
        'reservation': reservation,
        'default_message': default_message,
        'payment_method': payment_method
    }
    
    return render(request, 'payments/whatsapp_payment_notification.html', context)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Retrieve the reservation ID from client_reference_id
        reservation_id = session.get('client_reference_id')
        if reservation_id:
            reservation = Reservation.objects.get(id=reservation_id)
            
            # Create payment record
            payment = Payment.objects.create(
                reservation=reservation,
                user=reservation.user,
                amount=session.amount_total / 100,  # Convert from cents
                payment_method='STRIPE',
                status='APPROVED',
                notes=f"Stripe Session ID: {session.id}"
            )
            
            # Update reservation status
            reservation.status = 'confirmed'
            reservation.save()
            
            # Send confirmation email
            try:
                send_payment_notification_email(payment)
            except Exception as e:
                logger.error(f"Error sending stripe payment notification: {str(e)}")

    return HttpResponse(status=200)

@login_required
def payment_success(request, reservation_id):
    """
    Vista que muestra la página de éxito después de completar un pago.
    Incluye la opción para notificar por WhatsApp.
    """
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    # Obtener el último pago para esta reserva
    payment = Payment.objects.filter(reservation=reservation).order_by('-created_at').first()
    payment_method = payment.payment_method if payment else 'PAGO_MOVIL'
    
    context = {
        'reservation': reservation,
        'payment_method': payment_method
    }
    
    messages.success(request, 'Tu pago ha sido procesado exitosamente.')
    return render(request, 'payments/payment_success.html', context)

@login_required
def payment_cancel(request, reservation_id):
    messages.warning(request, 'El proceso de pago ha sido cancelado.')
    return redirect('payments:payment_method_selection', reservation_id=reservation_id)

@login_required
def payment_create(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        proof_image = request.FILES.get('proof_image')
        
        # Validar método de pago
        if payment_method not in dict(Payment.PAYMENT_METHODS):
            messages.error(request, 'Método de pago inválido')
            return redirect('reservations:reservation_confirm', reservation_id=reservation_id)
        
        # Validar comprobante para pagos que lo requieren
        if payment_method in ['PAGO_MOVIL', 'ZELLE'] and not proof_image:
            messages.error(request, 'Se requiere comprobante de pago para este método')
            return redirect('reservations:reservation_confirm', reservation_id=reservation_id)
        
        # Crear el pago
        payment = Payment.objects.create(
            user=request.user,
            reservation=reservation,
            amount=reservation.total_price,
            payment_method=payment_method,
            proof_image=proof_image if proof_image else None,
            status='REVIEWING' if payment_method in ['PAGO_MOVIL', 'ZELLE'] else 'PENDING'
        )
        
        # Actualizar estado de la reserva
        if payment_method == 'CASH':
            reservation.status = 'pending_payment'
        else:
            reservation.status = 'confirmed' if payment_method == 'STRIPE' else 'pending_payment'
        reservation.save()
        
        # Enviar notificación por correo al admin
        try:
            send_payment_notification_email(payment)
        except Exception as e:
            logger.error(f"Error sending payment creation notification: {str(e)}")
        
        # Redirigir según el método de pago
        if payment_method == 'STRIPE':
            return redirect('payments:stripe_checkout', payment_id=payment.id)
        else:
            messages.success(request, 'Pago registrado correctamente')
            return redirect('users:profile')
    
    return redirect('reservations:reservation_confirm', reservation_id=reservation_id)

@login_required
def payment_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    return render(request, 'payments/payment_detail.html', {'payment': payment})

@login_required
def payment_validate(request, payment_id):
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para realizar esta acción')
        return redirect('home')
        
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            payment.status = 'APPROVED'
            payment.validated_by = request.user
            payment.validated_at = timezone.now()
            payment.save()
            
            # Update reservation status
            payment.reservation.status = 'confirmed'
            payment.reservation.save()
            
            messages.success(request, 'Pago aprobado correctamente')
            
        elif action == 'reject':
            payment.status = 'REJECTED'
            payment.validated_by = request.user
            payment.validated_at = timezone.now()
            payment.save()
            
            messages.warning(request, 'Pago rechazado')
            
    return redirect('payments:payment_detail', payment_id=payment_id)

def send_payment_notification_email(payment):
    subject = f'Nuevo pago registrado - Reserva #{payment.reservation.id}'
    html_message = render_to_string('payments/email/payment_notification.html', {
        'payment': payment,
        'reservation': payment.reservation,
    })
    send_mail(
        subject,
        '',
        settings.DEFAULT_FROM_EMAIL,
        [settings.ADMIN_EMAIL],
        html_message=html_message,
        fail_silently=False,
    )

@login_required
def notify_payment_whatsapp(request, reservation_id):
    """
    Vista para enviar notificación de pago realizado por WhatsApp.
    Permite al usuario notificar rápidamente que ha realizado un pago manual.
    """
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    payment_method = request.GET.get('method', '').upper()
    admin_phone = getattr(settings, 'ADMIN_WHATSAPP_NUMBER', '584249743328')
    
    # Formatear la fecha y hora para mejor legibilidad
    start_time = timezone.localtime(reservation.start_time)
    end_time = timezone.localtime(reservation.end_time)
    date_str = start_time.strftime("%d/%m/%Y")
    start_hour = start_time.strftime("%I:%M %p")
    end_hour = end_time.strftime("%I:%M %p")
    
    # Construir mensaje personalizado para notificación de pago
    default_message = (
        "*Notificación de Pago - Arenas Padel Club*\n\n"
        f"*Reserva #*: {reservation.id}\n"
        f"*Cliente*: {reservation.user.get_full_name() or reservation.user.username}\n"
        f"*Teléfono*: {reservation.user.profile.phone if hasattr(reservation.user, 'profile') and hasattr(reservation.user.profile, 'phone') else 'No disponible'}\n"
        f"*Fecha de la reserva*: {date_str}\n"
        f"*Hora*: {start_hour} - {end_hour}\n"
        f"*Cancha*: {reservation.court.name}\n"
        f"*Precio*: ${format_price(reservation.total_price)}\n"
    )
    
    # Agregar información de artículos alquilados
    rental_items = reservation.rentals.all()
    if rental_items.exists():
        default_message += "\n*Implementos alquilados:*\n"
        for rental in rental_items:
            item_total = rental.quantity * rental.unit_price
            default_message += f"- {rental.item.name} x{rental.quantity}: ${format_price(item_total)}\n"
    
    default_message += f"\n*Método de pago*: {dict(Payment.PAYMENT_METHODS).get(payment_method, 'No especificado')}\n"
    
    # Agregar información de referencia si está disponible
    latest_payment = Payment.objects.filter(reservation=reservation).order_by('-created_at').first()
    if latest_payment and hasattr(latest_payment, 'notes') and latest_payment.notes:
        if "Referencia:" in latest_payment.notes:
            reference = latest_payment.notes.split("Referencia:")[1].strip()
            default_message += f"*Referencia de pago*: {reference}\n"
    
    default_message += "\n*He realizado el pago. Por favor, verifiquen a la brevedad posible.*"
    
    if request.method == 'POST':
        message = request.POST.get('message', default_message)
        # El usuario ha revisado el mensaje y desea enviarlo
        # Codificamos el mensaje para la URL
        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://wa.me/{admin_phone}?text={encoded_message}"
        
        return redirect(whatsapp_url)
    
    context = {
        'reservation': reservation,
        'default_message': default_message,
        'payment_method': payment_method
    }
    
    return render(request, 'payments/whatsapp_payment_notification.html', context)

def format_price(price):
    # Formatea con el formato español (coma para decimales, punto para miles)
    return "{:,.2f}".format(price).replace(',', ' ').replace('.', ',').replace(' ', '.')
