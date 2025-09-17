import os
import logging
from logging.handlers import TimedRotatingFileHandler

class Logger:
    def __init__(self, name=__name__, log_file='logs/log', level=logging.INFO, when='midnight', interval=1, backup_count=7):
        # 로그 디렉토리 생성
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # TimedRotatingFileHandler 설정
        handler = TimedRotatingFileHandler(log_file, when=when, interval=interval, backupCount=backup_count)
        handler.setLevel(level)
        handler.suffix = '%Y-%m-%d.log'  

        # 포맷터 설정
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # 핸들러를 로거에 추가
        self.logger.addHandler(handler)

        # 콘솔 핸들러도 추가하려면
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 로거 메서드를 직접 사용할 수 있도록 설정
        self.info = self.logger.info
        self.warning = self.logger.warning
        self.error = self.logger.error

    def get_logger(self):
        return self.logger