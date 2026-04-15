logs = ["ERROR", "DATA", "OK", "ERROR"]

resultado = list(map(lambda x: x.upper(), filter(lambda x: x == "ERROR", logs)))

print(resultado)