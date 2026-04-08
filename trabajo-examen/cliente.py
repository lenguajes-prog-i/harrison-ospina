import socket
import threading


# ─────────────────────────────────────────────
#  SALAS DISPONIBLES
# ─────────────────────────────────────────────
ROOMS_CONFIG = {
    "general": 5555,
    "tech":    5556,
    "random":  5557,
}


# ─────────────────────────────────────────────
#  CLASE CLIENT
# ─────────────────────────────────────────────
class Client:
    def __init__(self, host):
        self.host = host
        self.sock = None
        self.running = True
        self.in_room = False
        self.current_room = None
        self.ready = threading.Event()  # señal de que el servidor aceptó el nickname

    def show_room_menu(self):
        """Muestra el menú de salas y retorna la elegida"""
        print("\n=== SALAS DISPONIBLES ===")
        for name, port in ROOMS_CONFIG.items():
            print(f"  - {name} (puerto {port})")
        print("  - salir")
        print("=========================")

        while True:
            sala = input("¿A qué sala quieres unirte? ").strip().lower()
            if sala == "salir":
                return None
            if sala in ROOMS_CONFIG:
                return sala
            print(f"Sala '{sala}' no existe. Opciones: {', '.join(ROOMS_CONFIG.keys())}, salir")

    def connect_to_room(self, sala):
        """Abre conexión al puerto de la sala y hace el handshake de nickname"""
        port = ROOMS_CONFIG[sala]

        if self.sock:
            try:
                self.sock.close()
            except:
                pass

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.sock.connect((self.host, port))
            self.current_room = sala
            self.in_room = True
            self.ready.clear()
            return True
        except Exception as e:
            print(f"Error al conectar a sala '{sala}': {e}")
            return False

    def receive_messages(self):
        """Escucha mensajes del servidor — corre en su propio hilo"""
        buffer = ""
        while self.running and self.in_room:
            try:
                data = self.sock.recv(1024).decode("utf-8")
                if not data:
                    break

                buffer += data
                # Procesar línea por línea
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    # Señal: servidor pide nickname
                    if line == "__ASK_NICKNAME__":
                        nickname = input("Ingresa tu nombre: ").strip()
                        self.sock.send(nickname.encode("utf-8"))

                    # Señal: servidor listo, habilitar comandos
                    elif line == "__READY__":
                        print(f"\n=== Conectado a sala '{self.current_room}' ===")
                        print("Comandos: /msg <texto>, /rooms, /join <sala>, /leave, /quit\n")
                        self.ready.set()  # desbloquea send_messages

                    else:
                        print(line)

            except:
                if self.running and self.in_room:
                    print("\n[!] Conexión perdida con el servidor.")
                self.in_room = False
                self.ready.set()  # desbloquear para no quedar colgado
                break

    def send_messages(self):
        """Lee lo que escribe el usuario — espera hasta que servidor esté listo"""
        # Esperar a que el servidor confirme el nickname
        self.ready.wait()

        while self.running and self.in_room:
            try:
                message = input()
                if not message.strip():
                    continue

                # /quit — salir del programa
                if message.strip() == "/quit":
                    self.sock.send(message.encode("utf-8"))
                    self.running = False
                    self.in_room = False
                    print("Hasta luego!")
                    break

                # /leave — volver al menú
                elif message.strip() == "/leave":
                    self.sock.send(message.encode("utf-8"))
                    self.in_room = False
                    break

                # /join <sala> — cambiar de sala directamente
                elif message.strip().startswith("/join "):
                    sala_destino = message.strip().split(" ", 1)[1].strip().lower()
                    if sala_destino not in ROOMS_CONFIG:
                        print(f"Sala '{sala_destino}' no existe. Opciones: {', '.join(ROOMS_CONFIG.keys())}")
                        continue
                    if sala_destino == self.current_room:
                        print(f"Ya estás en la sala '{sala_destino}'.")
                        continue
                    self.sock.send("/leave".encode("utf-8"))
                    self.in_room = False
                    if self.connect_to_room(sala_destino):
                        t = threading.Thread(target=self.receive_messages, daemon=True)
                        t.start()
                        self.ready.wait()  # esperar nickname de la nueva sala
                        continue
                    else:
                        break

                # /rooms y /msg — enviar al servidor
                elif message.strip() == "/rooms" or message.strip().startswith("/msg "):
                    self.sock.send(message.encode("utf-8"))

                else:
                    print("Comandos: /msg <texto>, /rooms, /join <sala>, /leave, /quit")

            except KeyboardInterrupt:
                print("\nDesconectando...")
                self.running = False
                self.in_room = False
                break
            except:
                self.in_room = False
                break

    def start(self):
        """Flujo principal"""
        print("=== CLIENTE DE CHAT ===")

        while self.running:
            sala = self.show_room_menu()

            if sala is None:
                print("Hasta luego!")
                break

            if not self.connect_to_room(sala):
                continue

            # Arrancar hilo de recepción
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()

            # Enviar mensajes (espera señal READY internamente)
            self.send_messages()

        if self.sock:
            try:
                self.sock.close()
            except:
                pass


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────
if __name__ == "__main__":
    host = input("IP del servidor (Enter para 127.0.0.1): ").strip()
    if not host:
        host = "127.0.0.1"

    client = Client(host=host)
    client.start()
