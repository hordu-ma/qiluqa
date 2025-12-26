import time

WORKER_ID_BITS = 5
SEQUENCE_BITS = 12
# 最大取值计算
MAX_WORKER_ID = -1 ^ (-1 << WORKER_ID_BITS)
# 移位偏移计算
WORKER_ID_SHIFT = SEQUENCE_BITS
TIMESTAMP_LEFT_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS
# 序号循环掩码
SEQUENCE_MASK = -1 ^ (-1 << SEQUENCE_BITS)
# 起始时间
START = 1594977661913


class IdWorker(object):

    def __init__(
            self,
            worker_id: int = 1,
            sequence: int = 0,
    ):
        """
        :param worker_id: 机房和机器的ID 最大编号可为00 - 31  实际使用范围 00 - 29  备用 30 31
        :param sequence: 初始码
        """
        if worker_id > MAX_WORKER_ID or worker_id < 0:
            raise ValueError('worker_id值越界')

        self.worker_id = worker_id
        self.sequence = sequence
        self.last_timestamp = -1  # 上次计算的时间戳

    def get_timestamp(self):
        """
        生成毫秒级时间戳
        :return: 毫秒级时间戳
        """
        return int(time.time() * 1000)

    def wait_next_millis(self, last_timestamp):
        """
        等到下一毫秒
        """
        timestamp = self.get_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self.get_timestamp()
        return timestamp

    def get_id(self):
        timestamp = self.get_timestamp()
        # 判断服务器的时间是否发生了错乱或者回拨
        if timestamp < self.last_timestamp:
            # 如果服务器发生错乱 应该抛出异常
            # 此处待完善
            pass

        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & SEQUENCE_MASK
            if self.sequence == 0:
                timestamp = self.wait_next_millis(self.last_timestamp)
        else:
            self.sequence = 0
        self.last_timestamp = timestamp
        return ((timestamp - START) << TIMESTAMP_LEFT_SHIFT) | (self.worker_id << WORKER_ID_SHIFT) | self.sequence
