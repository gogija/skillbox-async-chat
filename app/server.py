#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        decoded = data.decode("utf-8")
        print(decoded)
        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")
                for client in self.server.clients:
                    if login == client.login:
                        self.transport.write(
                            f"Логин {login} занят, попробуйте другой".encode("utf-8")
                        )
                        self.transport.close()

                self.login = login
                self.transport.write(
                    f"Привет, {self.login}!\r\n".encode("utf-8")
                )
                self.send_history()
            else:
                self.transport.write("Неправильный логин\r\n".encode("utf-8"))

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}"

        for user in self.server.clients:
            user.transport.write(message.encode("utf-8"))

        if len(self.server.history) == 10:
            self.server.history.pop(0)
        self.server.history.append(message)

    def send_history(self):
        for message in self.server.history:
            self.transport.write(message.encode("utf-8"))


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []
    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
