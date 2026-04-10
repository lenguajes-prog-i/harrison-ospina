import socket
import threading
import time

# ─────────────────────────────────────────────
#  SALAS DISPONIBLES
# ─────────────────────────────────────────────
ROOMS_CONFIG = {
    "general": 5555,
    "tech":    5556,
    "random":  5557,
}

class Client:
    def __init__(self, host, id_temp):
        self.host = host
        self.id_temp = id_temp
        self.nickname = f"User_{id_temp}"
        self.sock = None
        self.running = True
        self.in_room = False
        self.current_room = None
        self.ready = threading.Event()

    def show_room_menu(self):
        print(f"\n=== SALAS ({self.nickname}) ===")
        for name, port in ROOMS_CONFIG.items():
            print(f"  - {name} ({port})")
        print("  - salir")

        while True:
            sala = input(f"[{self.nickname}] Selección: ").strip().lower()
            if sala == "salir": return None
            if sala in ROOMS_CONFIG: return sala
            print("Sala no válida.")

    def connect_to_room(self, sala):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, ROOMS_CONFIG[sala]))
            self.current_room = sala
            self.in_room = True
            self.ready.clear()
            return True
        except Exception as e:
            print(f"Error al conectar: {e}")
            return False

    def receive_messages(self):
        buffer = ""
        while self.running and self.in_room:
            try:
                data = self.sock.recv(1024).decode("utf-8")
                if not data: break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line == "__ASK_NICKNAME__":
                        self.nickname = input(f"\n[SISTEMA] Ingresa tu nombre para {self.current_room}: ").strip()
                        self.sock.send(self.nickname.encode("utf-8"))
                    elif line == "__READY__":
                        self.ready.set()
                    else:
                        # Indica de qué sala proviene el mensaje recibido
                        print(f"\n[RECIBIDO EN {self.current_room}] {line}")
            except:
                break
        self.in_room = False
        self.ready.set()

    def send_messages(self):
        self.ready.wait()
        while self.running and self.in_room:
            try:
                # Indica para quién/qué sala se envía el mensaje
                message = input(f"[{self.nickname}] enviando a [SALA: {self.current_room}] > ")
                if not message.strip(): continue
                
                self.sock.send(message.encode("utf-8"))
                
                if message.strip() in ("/leave", "/quit"):
                    self.in_room = False
                    if message.strip() == "/quit": self.running = False
                    break
            except:
                break

    def start(self):
        while self.running:
            sala = self.show_room_menu()
            if not sala: break
            if self.connect_to_room(sala):
                threading.Thread(target=self.receive_messages, daemon=True).start()
                self.send_messages()
        if self.sock: self.sock.close()

if __name__ == "__main__":
    print("=== LANZADOR DE CLIENTES ===")
    host = input("IP Servidor (Enter para 127.0.0.1): ").strip() or "127.0.0.1"
    try:
        n = int(input("¿Cuántos usuarios quieres conectar? ") or 1)
    except ValueError:
        n = 1
    
    hilos = []
    for i in range(1, n + 1):
        c = Client(host, i)
        t = threading.Thread(target=c.start)
        t.start()
        hilos.append(t)
        time.sleep(0.3) # Pausa para organizar el flujo de entrada inicial
    
    for t in hilos: t.join()