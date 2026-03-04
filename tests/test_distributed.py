import time

from overmind.distributed import MasterNode, WorkerNode


def test_master_worker_lifecycle() -> None:
    master = MasterNode(port=9200, heartbeat_timeout=1.0)
    master.enqueue_tasks(["crawl:https://example.com"])
    master.start()

    worker = WorkerNode("w-1", master_port=9200)
    task = worker.run_once()
    assert task == "crawl:https://example.com"

    time.sleep(0.05)
    assert master.workers["w-1"].completed_tasks == 1

    master.stop()
