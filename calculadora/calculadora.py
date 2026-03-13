def suma (a, b):
    return a + b

def resta (a, b):
    return a - b

def multiplicacion (a, b):
    return a * b

def division (a, b):
    if b == 0:
        return "Error: No se puede dividir por cero"
    else:
        return a / b
    
def potencia (a, b):
    return a ** b

def menu ():
    print("Seleccione la operación que desea realizar:")
    print("1. Suma")
    print("2. Resta")
    print("3. Multiplicación")
    print("4. División")
    print("5. Potencia")
    print("6. Salir")

while True:

    menu()
    opcion= input("ingrese la operacion que desea realizar: ")

    if opcion == "1":
        num1 = float(input("Ingrese el primer número: "))
        num2 = float(input("Ingrese el segundo número: "))
        print( suma(num1, num2))

    elif opcion == "2":
        num1 = float(input("Ingrese el primer número: "))
        num2 = float(input("Ingrese el segundo número: "))
        print(resta(num1, num2))

    elif opcion == "3":
        num1 = float(input("Ingrese el primer número: "))
        num2 = float(input("Ingrese el segundo número: "))
        print( multiplicacion(num1, num2)) 

    elif opcion == "4":
        num1 = float(input("Ingrese el primer número: "))
        num2 = float(input("Ingrese el segundo número: "))
        print(division(num1, num2))

    elif opcion == "5":
        num1 = float(input("Ingrese el primer número: "))
        num2 = float(input("Ingrese el segundo número: "))
        print(potencia(num1, num2))

    elif opcion == "6":
        print("Saliendo de la calculadora...")
        break

    else:
        print("Opción no válida. Por favor, seleccione una opción válida.")

menu()