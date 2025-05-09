# Author: Mani Amoozadeh
# Email: mani.amoozadeh2@gmail.com

import json
import socket
from threading import Lock

class QMPClient:

    def __init__(self, path):
        self.socket = None
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.connect(path)
        self.qmp_lock = Lock()

        # get server greeting
        out = self._receive()
        print("Connected to QMP Server:\n    ", out)

        # start capability negotiation
        out = self._negotiate_capabilities()
        print("Capability negotiation:\n    ", out)

    def _receive(self):
        if not self.socket:
            raise RuntimeError("Not connected to QMP server")
        response = b''
        while True:
            chunk = self.socket.recv(4096)
            response += chunk
            if b'\n' in chunk:
                break
        return json.loads(response.decode('utf-8'))

    def _send(self, cmd):
        if not self.socket:
            raise RuntimeError("Not connected to QMP server")
        self.socket.sendall(json.dumps(cmd).encode('utf-8') + b'\n')

    def _negotiate_capabilities(self):
        cmd = {'execute': 'qmp_capabilities'}
        self._send(cmd)
        return self._receive()

    ###########################

    def execute(self, command, arguments=None):
        with self.qmp_lock:
            cmd = {'execute': command}
            if arguments:
                cmd['arguments'] = arguments
            self._send(cmd)
            return self._receive()

    def close(self):
        if self.socket:
            self.socket.close()
            self.socket = None


if __name__ == '__main__':

    client = QMPClient('./qmp-sock')

    response = client.execute('query-version')
    print("QEMU version:", response)

    response = client.execute('query-status')
    print("QEMU status:", response)

    response = client.execute('query-chardev')
    print("QEMU chardev:", response)

    client.close()
