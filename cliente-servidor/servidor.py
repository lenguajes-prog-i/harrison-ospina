import socket

HOST = "127.0.0.1"
PORT = 5001

# socket TCP
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# IP - Perto
server.bind((HOST, PORT))

server.listen(2)

print("Servidor esperando conexiones...")

while True:
    conn, addr = server.accept()
    print(f"Conexión establecida desde {addr}")

    data = conn.recv(1024).decode()
    print(f"Mensaje recibido: {data}")

    respuesta = "Mensaje recibido correctamente"
    conn.send(respuesta.encode())

    conn.close()
    print(f"Conexión cerrada con {addr}")