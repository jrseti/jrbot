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

    run()