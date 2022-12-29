# Taken from https://stackoverflow.com/questions/43761004/fps-how-to-divide-count-by-time-function-to-determine-fps
import time
import collections

# average fps for some calls
class FPS:
    def __init__(self, avarageof=50):
        self.frametimestamps = collections.deque(maxlen=avarageof)

    def __call__(self):
        self.frametimestamps.append(time.perf_counter())
        if len(self.frametimestamps) > 1:
            return len(self.frametimestamps) / (self.frametimestamps[-1] - self.frametimestamps[0])
        else:
            return 0.0
