import threading
import time

def programar():
    print("Inicio 1")
    time.sleep(4)
    print("Finzalizo 1")

def beber_agua():
    print("Inicio 2")
    time.sleep(6)
    print("Finzalizo 2")

def estudiar(): 
    print("Inicio 3")
    time.sleep(4)
    print("Finzalizo 3")

inicio = time.perf_counter()
#Concurrencia
#programar()
#beber_agua()
#estudiar()

#Hilos
hilo_programar = threading.Thread(target= programar, args=())
hilo_programar.start()

hilo_beber_agua = threading.Thread(target=beber_agua, args=())
hilo_beber_agua.start()

hilo_estudiar = threading.Thread(target=estudiar, args=())
hilo_estudiar.start()

#ejecuta los hilos y espera a que terminen para continuar con el programa
hilo_programar.join()
hilo_beber_agua.join()
hilo_estudiar.join()



fin = time.perf_counter()

tiempo= fin - inicio

print(tiempo)