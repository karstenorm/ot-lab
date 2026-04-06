import logging
import threading
from process import Process
from plc import PLC


def main():
    logging.basicConfig(level=logging.INFO)

    ip = "127.0.0.1"
    port = 5020

    process = Process()
    plc = PLC(process, ip, port)

    t1 = threading.Thread(target=process.run)
    t2 = threading.Thread(target=plc.start_server)
    t3 = threading.Thread(target=plc.run)

    t1.start()
    t2.start()
    t3.start()

    t1.join()
    t2.join()
    t3.join()


if __name__ == "__main__":
    main()

