import threading
import time

def tarea(numero):
    print(f"Numero de hilo {numero}")

inicio = time.perf_counter()

hilos = []
for i in range (1, 1500):
    hilo = threading.Thread(target=tarea, args=(i, ))
    hilos.append(hilo)
    hilo.start()

for hilo in hilos:
    hilo.join() #espera a que el hilo termine para continuar con el programa

fin = time.perf_counter()

tiempo= fin - inicio

print(tiempo)