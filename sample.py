from multiprocessing import Process, Value
import time

class Sample:
    def __init__(self):
        self.cnt = 1
        self.shard_cnt = Value('i', 0)
        Process(target=self.increment).start()
        
    def increment(self):
        self.cnt += 1
        self.shard_cnt.value += 10
        
if __name__ == "__main__":
    instance = Sample()
    time.sleep(1)
    print(instance.cnt)
    print(instance.shard_cnt.value)