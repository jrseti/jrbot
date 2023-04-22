import time
import processes
import multiprocessing

def run():
    while True:
        pids_info = processes.get_pids()
        print(pids_info)
        # Sleep 5 seconds
        time.sleep(5)
if __name__ == "__main__":

    daemon_process = multiprocessing.Process(target=run)
    daemon_process.daemon = True
    daemon_process.start()
    daemon_process.join()
    print("FINISHED")