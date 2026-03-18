import threading
import time

inicio = time.perf_counter()

def mostrar_letras(letra):
    for i in range(4):
        print(letra)

letras = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l" , "m"]

hilos = []
for letra in letras:
    hilo = threading.Thread(target=mostrar_letras, args=(letra,))
    hilos.append(hilo)
    hilo.start()

    for hilo in hilos:
        hilo.join() #espera a que el hilo termine para continuar con el programa

final = time.perf_counter()

timepo_recorrido= final - inicio

print(timepo_recorrido)

