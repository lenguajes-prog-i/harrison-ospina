import socket

HOST = "127.0.0.1"
PORT = 5001

# socket TCP
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Conexion
client.connect((HOST, PORT))

# mensaje
mensaje = "Hola desde Cliente 02"
client.send(mensaje.encode())

# repuesta
respuesta = client.recv(1024).decode()
print(f"Respuesta del servidor: {respuesta}")

client.close()