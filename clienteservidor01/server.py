import socket
import threading


class ChatServer:
    def __init__(self, host="127.0.0.1", port=5555):
        self.host = host
        self.port = port
        self.clients = []
        self.nicknames = []

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))

    def broadcast(self, message, sender_conn=None):
        """Envía el mensaje a todos los clientes excepto al remitente."""
        for client in self.clients:
            if client != sender_conn:
                try:
                    client.send(message)
                except:
                    client.close()
                    self.remove_client(client)

    def handle_client(self, client_conn):
        """Atiende a un cliente específico en un hilo."""
        nickname = None
        while True:
            try:
                message = client_conn.recv(1024)
                if message:
                    if nickname is None:
                        # Primer mensaje es el nickname
                        nickname = message.decode("utf-8")
                        self.nicknames.append(nickname)
                        self.clients.append(client_conn)
                        print(f"[+] {nickname} conectado")
                        self.broadcast(
                            f"{nickname} se ha unido al chat".encode("utf-8"),
                            client_conn,
                        )
                    else:
                        # Mensaje de chat normal
                        full_msg = f"{nickname}: {message.decode('utf-8')}".encode(
                            "utf-8"
                        )
                        self.broadcast(full_msg, client_conn)
            except:
                if nickname:
                    print(f"[-] {nickname} desconectado")
                    self.broadcast(
                        f"{nickname} ha salido del chat".encode("utf-8"), client_conn
                    )
                    if nickname in self.nicknames:
                        self.nicknames.remove(nickname)
                self.remove_client(client_conn)
                break

    def remove_client(self, client_conn):
        if client_conn in self.clients:
            self.clients.remove(client_conn)
        client_conn.close()

    def start(self):
        self.server.listen()
        print(f"[INFO] Servidor de chat escuchando en {self.host}:{self.port}")
        try:
            while True:
                client_conn, addr = self.server.accept()
                print(f"[INFO] Conexión entrante desde {addr}")
                thread = threading.Thread(
                    target=self.handle_client, args=(client_conn,)
                )
                thread.start()
        except KeyboardInterrupt:
            print("\n[INFO] Servidor detenido por el usuario.")
        finally:
            self.server.close()


if __name__ == "__main__":
    server = ChatServer()
    server.start()
