import pickle


def crear_auto(modelo, placa):
    auto = {
        "modelo": modelo,
        "placa": placa
    }
    return auto


def mostrar_detalle(auto):
    return f"El auto {auto['modelo']} tiene placa {auto['placa']}"


autos = [
    crear_auto("Mazda", "ABC123"),
    crear_auto("Toyota", "DEF456"),
    crear_auto("Honda", "GHI789"),
    crear_auto("Ford", "JKL012"),
    crear_auto("Chevrolet", "MNO345")
]


archivo_auto = open("auto.txt", "wb")
pickle.dump(autos, archivo_auto)  # Guardamos la lista una sola vez
archivo_auto.close()


archivo_auto = open("auto.txt", "rb")
autos_recuperados = pickle.load(archivo_auto)
archivo_auto.close()


for auto in autos_recuperados:
    print(mostrar_detalle(auto))