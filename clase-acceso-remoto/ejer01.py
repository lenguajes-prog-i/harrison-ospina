import pickle 

data= {"mensaje": "hola"}

serializacion= pickle.dumps(data) 
print(serializacion)

mensaje= pickle.loads(serializacion)
print(mensaje) 