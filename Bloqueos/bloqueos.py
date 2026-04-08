import threading

#mutex: es un bloqueo que permite que solo un hilo acceda a un recurso compartido a la vez. 
#       Se utiliza para evitar condiciones de carrera y garantizar la integridad de los datos.

contador = 0 
lock = threading.Lock() #crea un objeto de bloqueo para proteger el acceso al recurso compartido (contador)

def incrementar_contador():
    global contador
    for i in range(100):
        with lock: #adquiere el bloqueo antes de acceder al recurso compartido
            contador += 1 

hilo1 = threading.Thread(target=incrementar_contador, args=()) 
hilo1.start()       
hilo2 = threading.Thread(target=incrementar_contador, args=())  
hilo2.start()

hilo1.join()
hilo2.join()   

print(contador)

#contador con sistemas de bloqueo sin mutex