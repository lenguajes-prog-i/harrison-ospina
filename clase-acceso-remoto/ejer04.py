import pickle

class Auto:
    def __init__(self, modelo, placa):
        self.modelo = modelo
        self.placa = placa

    def __repr__(self):
        return f"El auto {self.modelo} tiene la placa {self.placa}"

objeto_auto = Auto("Mazda", "AVC123")
objeto_auto1 = Auto("Toyota", "XYZ789")
objeto_auto2 = Auto("Ford", "LMN456")

autos = [objeto_auto, objeto_auto1, objeto_auto2]

# Guardar todos en un solo dump
with open("file_auto", "wb") as archivo_auto:
    pickle.dump(autos, archivo_auto)

# Leer
with open("file_auto", "rb") as archivo_auto:
    autos_recuperados = pickle.load(archivo_auto)

for auto in autos_recuperados:
    print(auto)