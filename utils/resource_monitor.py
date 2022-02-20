import time
from contextlib import contextmanager
from datetime import datetime
from threading import Event, Thread

import psutil
from guppy import hpy  # noqa: F401  #

__all__ = [
    'resource_monitor',
]

# def eng_string(x, sig_figs=3, si=True):
#     """
#     Returns float/int value <x> formatted in a simplified engineering format -
#     using an exponent that is a multiple of 3.

#     sig_figs: number of significant figures

#     si: if true, use SI suffix for exponent, e.g. k instead of e3, n instead of
#     e-9 etc.
#     """
#     x = float(x)
#     sign = ''
#     if x < 0:
#         x = -x
#         sign = '-'
#     if x == 0:
#         exp = 0
#         exp3 = 0
#         x3 = 0
#     else:
#         exp = int(math.floor(math.log10(x)))
#         exp3 = exp - (exp%3)
#         x3 = x / (10**exp3)
#         x3 = round(x3, -int(math.floor(math.log10(x3)) - (sig_figs-1)))
#         if x3 == int(x3):  # prevent from displaying .0
#             x3 = int(x3)

#     if si and exp3 >= -24 and exp3 <= 24 and exp3 != 0:
#         exp3_text = 'yzafpnum kMGTPEZY' [exp3//3 + 8]
#     elif exp3 == 0:
#         exp3_text = ''
#     else:
#         exp3_text = 'e%s' % exp3

#     return ('%s%s%s') % (sign, x3, exp3_text)


class Ticker(Thread):

    def __init__(self, target_fn, interval=0.5):
        super().__init__()
        self.target_fn = target_fn
        self.interval = interval
        self.started = Event()
        self.stop = Event()
        self.finished = Event()

    def start(self):
        super().start()
        self.started.wait()

    def run(self):
        self.started.set()
        while not self.stop.wait(self.interval):
            self.target_fn()
        self.finished.set()

    def end(self):
        self.stop.set()
        self.finished.wait()


@contextmanager
def resource_monitor(process=None, interval=2):
    print('time, rss, vms, pct, heap')
    start_time = datetime.utcnow()

    # hp = hpy()

    def tick():
        # h = lambda v: eng_string(v, sig_figs=4, si=False)
        h = str
        mem = process.memory_info()
        pct = process.memory_percent()
        t = datetime.utcnow() - start_time
        # heap = hp.heap()
        # print(f'{t.total_seconds()}, {h(mem.rss)}, {h(mem.vms)}, {pct:.1f}%, {h(heap.size)}')
        print(f'{t.total_seconds()}, {h(mem.rss)}, {h(mem.vms)}, {pct:.1f}%')

    process = process or psutil.Process()
    # hp.setrelheap()
    ticker = Ticker(tick, interval=interval)
    ticker.start()
    tick()
    try:
        yield ticker
    finally:
        ticker.end()


if __name__ == "__main__":
    with resource_monitor():
        max_entries = 2500
        delay = .005

        large_dict = {}
        entries = 0

        while (1):
            time.sleep(delay)
            entries += 1
            large_dict[entries] = list(range(10000))

            if entries > max_entries:
                break
