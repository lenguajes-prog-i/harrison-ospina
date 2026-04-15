def leer_logs(ruta):
    with open(ruta, "r") as f:
        return f.readlines()


def es_error(linea):
    return "ERROR" in linea


def transformar(linea):
    return linea.upper()


logs = leer_logs("logs.txt")

resultado = list(map(transformar, filter(es_error, logs)))

print("\n".join(resultado))
# print(resultado)