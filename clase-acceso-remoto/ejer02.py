import pickle

datos= { 
    "nombre": "Harrison",
    "materia": "Lenguaje de Programacion 1",
    "notas": [3,3,4],
}

with open("data.txt", "wb") as archivo:
    pickle.dump(datos, archivo)

with open("data.txt", "rb") as archivo2:
    datos_estudiantes= pickle.load(archivo2)  
print(datos_estudiantes)  