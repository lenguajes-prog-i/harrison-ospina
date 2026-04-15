# Pure function
def adicionar(lista, elemento):
    return lista + [elemento]


# Con efectos secundarios
def adicionarE(lista, elemento):
    lista.append(elemento)
    return lista


lista = [1]
r = adicionarE(lista, 4)

print(f"lista original {lista}")
print(f"lista resultante {r}")