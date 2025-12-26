from loguru import logger


def init_log_config():
    """
    日志框架 Loguru 初始化配置
    :return: None
    """
    logger.add(
        sink='./log/info.log',
        rotation='00:00',
        retention='30 days',
        level="INFO",
        encoding='utf8',
        enqueue=True,
        serialize=True,
    )

    logger.add(
        sink='./log/error.log',
        rotation='00:00',
        retention='30 days',
        level="ERROR",
        encoding='utf8',
        enqueue=True,
        serialize=True,
        filter=lambda record: record["level"].name == "ERROR",
    )
