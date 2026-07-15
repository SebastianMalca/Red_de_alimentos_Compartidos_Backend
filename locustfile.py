from locust import HttpUser, task, between

class ComedorUser(HttpUser):
    # Simula el tiempo de espera entre tareas (entre 0.5 y 1.5 segundos)
    wait_time = between(0.5, 1.5)

    @task
    def cargar_feed_donaciones(self):
        # Hace la petición GET al endpoint
        with self.client.get("/donaciones", catch_response=True) as response:
            # Verificamos el tiempo en segundos sin usar el símbolo menor/mayor
            tiempo_ok = response.elapsed.total_seconds().__lt__(0.5)
            
            if response.status_code == 200 and tiempo_ok:
                response.success()
            else:
                response.failure(f"Fallo: HTTP {response.status_code} o tiempo de respuesta fuera de limite")
