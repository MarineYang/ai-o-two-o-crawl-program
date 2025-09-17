from configs.config import ConfigModel

class MySQLConfig(ConfigModel):
    user: str = ""
    pw: str = ""
    host: str = ""
    port: int = 0
    db: str = ""

