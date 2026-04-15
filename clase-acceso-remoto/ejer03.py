import pickle

class Auto():
    def __init__(self, placa, modelo):
        self.modelo= modelo
        self.placa= placa

    def __repr__(self):
        return f"El auto {self.modelo} con placa {self.placa}"
    
objeto_auto= Auto("Mazda", "ABC123")
objeto_auto1= Auto("Chevrolet", "DEF456")
objeto_auto2= Auto("Renault", "GHI789")
objeto_auto3= Auto("Toyota", "JKL012")
objeto_auto4= Auto("Ford", "MNO345")

lista_autos= [objeto_auto, objeto_auto1, objeto_auto2, objeto_auto3, objeto_auto4]



archivo_autos= open("autos.txt", "wb")

pickle.dump(lista_autos, archivo_autos)

archivo_autos.close()

archivo_autos= open("autos.txt", "rb")
autos= pickle.load(archivo_autos) 
archivo_autos.close()

for auto in autos:
    print(auto)