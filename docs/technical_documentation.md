Documentación Técnica: Sistema de Reservas y Alquiler de Arenas Padel Club
Índice
Introducción
Sistema de Notificaciones de WhatsApp
Sistema de Gestión de Artículos Alquilados
Modificaciones Recientes
Guía de Mantenimiento
1. Introducción
Este documento proporciona detalles técnicos sobre el sistema de reservas de Arenas Padel Club, centrándose específicamente en las funcionalidades de notificaciones por WhatsApp y la gestión de artículos alquilados. Sirve como referencia para desarrolladores que necesiten mantener o ampliar estas funcionalidades.

2. Sistema de Notificaciones de WhatsApp
2.1. Descripción General
El sistema utiliza la API de WhatsApp Business para enviar notificaciones a los usuarios sobre sus reservas y pagos. Las notificaciones se generan en momentos clave:

Cuando se confirma una nueva reserva
Cuando se realiza un pago exitoso
2.2. Estructura del Código
La funcionalidad de notificaciones por WhatsApp se implementa principalmente en:

payments/views.py: Contiene la función whatsapp_notification que construye y envía los mensajes.
templates/payments/whatsapp_payment_notification.html: Plantilla para el mensaje de notificación de pago.
templates/payments/whatsapp_reservation_notification.html: Plantilla para el mensaje de notificación de reserva.
2.3. Funcionamiento
Construcción del mensaje: La función whatsapp_notification en payments/views.py construye un mensaje predeterminado con los detalles de la reserva.
Inclusión de artículos alquilados: Se consultan los artículos alquilados asociados a la reserva y se agregan al mensaje.
Envío: El mensaje se envía a través de la API de WhatsApp Business.
2.4. Modificaciones Recientes
Se implementó la inclusión de artículos alquilados en el mensaje de WhatsApp modificando la función whatsapp_notification:

python
CopyInsert
# Agregar información de artículos alquilados
rental_items = reservation.rentals.all()
if rental_items.exists():
    default_message += "\n*Implementos alquilados:*\n"
    for rental in rental_items:
        default_message += f"- {rental.item.name} x{rental.quantity}: ${rental.total_price}\n"
    
    # Agregar el subtotal de artículos alquilados
    default_message += f"*Subtotal Alquileres:* ${reservation.total_rental_price}\n"
3. Sistema de Gestión de Artículos Alquilados
3.1. Descripción General
El sistema permite a los usuarios alquilar artículos adicionales (palas, pelotas) junto con sus reservas de canchas. Estos artículos se muestran en la interfaz, se seleccionan durante el proceso de reserva y se incluyen en el costo total.

3.2. Estructura del Código
Los principales componentes son:

Modelos (reservations/models.py):
RentalItem: Define los artículos disponibles para alquiler.
ReservationRental: Relaciona los artículos alquilados con una reserva específica.
Reservation: Contiene propiedades para calcular el precio total incluyendo alquileres.
Vistas (reservations/views.py):
rental_selection_view: Maneja la selección de artículos durante el proceso de reserva.
Plantillas:
templates/reservations/rental_selection.html: Interfaz para seleccionar artículos.
templates/users/profile.html: Muestra los detalles de alquiler en el perfil.
3.3. Visualización de Artículos Alquilados
3.3.1. En la Interfaz de Selección
Los artículos se muestran en rental_selection.html con sus imágenes, permitiendo a los usuarios seleccionar el tipo y la cantidad. Se implementó código JavaScript para mostrar dinámicamente las imágenes de las palas cuando se seleccionan:

javascript
CopyInsert
$(document).ready(function() {
    $('#paddle').change(function() {
        var selectedPaddleId = $(this).val();
        $('.paddle-image-preview').hide();
        if (selectedPaddleId) {
            $('.paddle-image-preview[data-paddle-id="' + selectedPaddleId + '"]').show();
        }
    }).trigger('change');
});
3.3.2. En el Perfil del Usuario
Los detalles de alquiler se muestran en un modal personalizado en profile.html. Se implementó un sistema de modal JavaScript que reemplazó el anterior sistema basado en Bootstrap para evitar problemas de visualización.

El código JavaScript construye dinámicamente el contenido del modal con los detalles de los artículos alquilados, incluyendo imágenes:

javascript
CopyInsert
const imgHtml = rental.image ? `<img src="${rental.image}" alt="${rental.item}" style="height: 40px; width: auto; margin-right: 10px;">` : '';
tableRows += `
    <tr>
        <td>${imgHtml}${rental.item}</td>
        <td>${rental.quantity}</td>
        <td>$${rental.unitPrice.toFixed(2)}</td>
        <td>$${rental.total.toFixed(2)}</td>
    </tr>
`;
4. Modificaciones Recientes
4.1. Notificaciones de WhatsApp
Problema: Los artículos alquilados no aparecían en las notificaciones de WhatsApp.
Solución: Se modificó la función whatsapp_notification para incluir un resumen de los artículos alquilados, sus cantidades y precios.
Archivos modificados: payments/views.py
4.2. Visualización de Imágenes
Problema: Las imágenes de las palas no se mostraban correctamente en la página de selección de alquileres.
Solución: Se modificó la estructura HTML para mostrar directamente las imágenes como elementos <img> en lugar de contenedores <div>, y se actualizó el código JavaScript correspondiente.
Archivos modificados: templates/reservations/rental_selection.html
4.3. Navegación Mejorada
Problema: Los usuarios tenían que hacer clic adicional para ver sus reservas.
Solución: Se modificó la barra de navegación para incluir un enlace a "Mis Reservas" que lleva directamente a la sección de reservas en la página de perfil.
Archivos modificados:
templates/base/base.html
templates/users/profile.html (se agregó JavaScript para activar la pestaña correcta)
5. Guía de Mantenimiento
5.1. Modificar el Formato de las Notificaciones
Para cambiar el formato de las notificaciones de WhatsApp:

Localiza la función whatsapp_notification en payments/views.py.
Modifica la estructura del mensaje en la variable default_message.
5.2. Agregar Nuevos Tipos de Artículos
Para agregar nuevos tipos de artículos para alquiler:

Agrega la nueva opción en la lista ITEM_TYPES del modelo RentalItem.
Crea registros para los nuevos artículos en el admin de Django.
Asegúrate de subir las imágenes correspondientes.
5.3. Solución de Problemas Comunes
Imágenes no visibles
Verifica que las imágenes estén correctamente subidas al servidor en /media/rental_items/.
Comprueba los permisos de los archivos.
Asegúrate de que los registros en la base de datos tengan la ruta correcta.
Notificaciones no enviadas
Verifica la configuración de la API de WhatsApp Business.
Comprueba que el número de teléfono del usuario esté en el formato correcto.
Revisa los logs del servidor para errores específicos.
Documento preparado el 5 de marzo de 2025.