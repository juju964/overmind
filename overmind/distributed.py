from __future__ import annotations

import json
import queue
import socket
import threading
import time
from dataclasses import dataclass, field


@dataclass
class WorkerState:
    worker_id: str
    last_heartbeat: float = field(default_factory=time.time)
    completed_tasks: int = 0


class MasterNode:
    def __init__(self, host: str = "127.0.0.1", port: int = 9100, heartbeat_timeout: float = 5.0) -> None:
        self.host = host
        self.port = port
        self.heartbeat_timeout = heartbeat_timeout
        self.workers: dict[str, WorkerState] = {}
        self.task_queue: "queue.Queue[str]" = queue.Queue()
        self._running = False
        self._thread: threading.Thread | None = None

    def enqueue_tasks(self, tasks: list[str]) -> None:
        for task in tasks:
            self.task_queue.put(task)

    def _handle_client(self, conn: socket.socket) -> None:
        with conn:
            payload = conn.recv(4096)
            if not payload:
                return
            message = json.loads(payload.decode("utf-8"))
            command = message.get("command")
            worker_id = message.get("worker_id", "unknown")

            if command == "heartbeat":
                state = self.workers.setdefault(worker_id, WorkerState(worker_id=worker_id))
                state.last_heartbeat = time.time()
                conn.sendall(b'{"status":"ok"}')
                return

            if command == "request_task":
                state = self.workers.setdefault(worker_id, WorkerState(worker_id=worker_id))
                state.last_heartbeat = time.time()
                try:
                    task = self.task_queue.get_nowait()
                    conn.sendall(json.dumps({"task": task}).encode("utf-8"))
                except queue.Empty:
                    conn.sendall(b'{"task":null}')
                return

            if command == "task_done":
                state = self.workers.setdefault(worker_id, WorkerState(worker_id=worker_id))
                state.completed_tasks += 1
                state.last_heartbeat = time.time()
                conn.sendall(b'{"status":"recorded"}')

    def _monitor_dead_workers(self) -> None:
        now = time.time()
        dead = [wid for wid, state in self.workers.items() if now - state.last_heartbeat > self.heartbeat_timeout]
        for wid in dead:
            del self.workers[wid]

    def _serve(self) -> None:
        self._running = True
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, self.port))
            sock.listen(16)
            sock.settimeout(0.5)
            while self._running:
                self._monitor_dead_workers()
                try:
                    conn, _ = sock.accept()
                except socket.timeout:
                    continue
                threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()

    def start(self) -> None:
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)


class WorkerNode:
    def __init__(self, worker_id: str, master_host: str = "127.0.0.1", master_port: int = 9100) -> None:
        self.worker_id = worker_id
        self.master_host = master_host
        self.master_port = master_port

    def _send(self, message: dict) -> dict:
        with socket.create_connection((self.master_host, self.master_port), timeout=2) as sock:
            sock.sendall(json.dumps(message).encode("utf-8"))
            return json.loads(sock.recv(4096).decode("utf-8"))

    def heartbeat(self) -> None:
        self._send({"command": "heartbeat", "worker_id": self.worker_id})

    def request_task(self) -> str | None:
        response = self._send({"command": "request_task", "worker_id": self.worker_id})
        return response.get("task")

    def task_done(self, task: str) -> None:
        self._send({"command": "task_done", "worker_id": self.worker_id, "task": task})

    def run_once(self) -> str | None:
        self.heartbeat()
        task = self.request_task()
        if task is None:
            return None
        time.sleep(0.01)
        self.task_done(task)
        return task
