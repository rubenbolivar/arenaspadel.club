import time
import random
from locust import HttpUser, task, between

class ReservationUser(HttpUser):
    wait_time = between(1, 5)  # Tiempo entre 1 y 5 segundos entre tareas
    
    def on_start(self):
        # Iniciar sesión
        self.client.post("/accounts/login/", {
            "username": "testuser",  # Reemplazar con un usuario de prueba real
            "password": "testpassword"  # Reemplazar con una contraseña real
        })
        
        # Obtener el token CSRF de la página principal
        response = self.client.get("/")
        if "csrfmiddlewaretoken" in response.text:
            self.token = response.text.split('name="csrfmiddlewaretoken" value="')[1].split('"')[0]
        else:
            self.token = ""
    
    @task(2)
    def view_courts(self):
        self.client.get("/courts/")
    
    @task(3)
    def view_court_detail(self):
        # Asume que tienes canchas con IDs del 1 al 5
        court_id = random.randint(1, 5)
        self.client.get(f"/courts/{court_id}/")
        
    @task(5)
    def check_availability(self):
        # Simular verificación de disponibilidad
        court_id = random.randint(1, 5)
        date = "2025-03-10"  # Ajustar a una fecha futura según sea necesario
        self.client.get(f"/api/reservations/availability/?court={court_id}&date={date}")
        
    @task(1)
    def make_reservation(self):
        # Crear reserva (simulación básica - ajustar según la estructura real de tu API)
        court_id = random.randint(1, 5)
        
        # Crear una hora aleatoria entre 7 AM y 10 PM
        hour = random.randint(7, 22)
        minute = 0 if random.random() < 0.5 else 30
        
        # Simular el proceso de reserva
        response = self.client.post(
            f"/api/reservations/create/",
            {
                "court": court_id,
                "date": "2025-03-10",
                "start_time": f"{hour:02d}:{minute:02d}",
                "duration": 60,
                "csrfmiddlewaretoken": self.token
            },
            headers={"X-CSRFToken": self.token}
        )

class BrowsingUser(HttpUser):
    wait_time = between(2, 8)
    
    @task(10)
    def index_page(self):
        self.client.get("/")
        
    @task(5)
    def view_about(self):
        self.client.get("/about/")
        
    @task(2)
    def view_contact(self):
        self.client.get("/contact/")
