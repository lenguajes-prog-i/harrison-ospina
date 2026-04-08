import threading
import time

# ✅ Recurso compartido + Lock para protegerlo
contador = 0
lock = threading.Lock()

def tarea(nombre):
    global contador
    for i in range(3):
        print(f"{nombre} está ejecutando la tarea {i}")
        time.sleep(1)

        # ✅ SECCIÓN CRÍTICA protegida con Lock
        with lock:                          # solo 1 hilo entra aquí a la vez
            contador += 1                   # operación segura
            print(f"{nombre} → contador = {contador}")

# ✅ Crear e iniciar todos los hilos PRIMERO
hilos = []
for i in range(3):
    hilo = threading.Thread(target=tarea, args=(f"Hilo-{i}",))
    hilos.append(hilo)
    hilo.start()          # ← lanzar ANTES del join

# ✅ Esperar a que TODOS terminen DESPUÉS
for hilo in hilos:
    hilo.join()           # ← join va en su propio bucle separado

print(f"\n✅ Contador final: {contador}")  # siempre será 9 (3 hilos × 3 iteraciones)