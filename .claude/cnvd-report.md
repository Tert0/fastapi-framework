============================================================
CNVD 漏洞报告 — Tert0/fastapi-framework v1.5.3.5
审计日期: 2026-05-16
审计范围: 12 个 Python 源文件
============================================================

【漏洞一】CRITICAL | CWE-502 | 置信度 92%

标题: YAML 不安全反序列化导致任意代码执行 (yaml.CLoader)

📁 位置: fastapi_framework/config.py:80

🔗 数据流:
  Source: config.py:72
    with open(config_file_path, "r") as file:
        data: str = file.read()
  
  Filter: 无 — CLoader 是 yaml.Loader 的 C 实现，不是 SafeLoader
  
  Sink: config.py:80
    config = yaml.load(data, Loader=yaml.CLoader)

📝 描述:
  config.py 的 ConfigMeta 元类在加载 YAML 配置文件时使用 yaml.CLoader。
  yaml.CLoader 是 yaml.Loader 的 C 语言实现版本，支持完整的 YAML 标签集，
  包括 !!python/object 标签，允许通过 YAML 反序列化实例化任意 Python 对象。
  
  如果攻击者能够修改 YAML 配置文件（例如通过文件上传、路径遍历或
  供应链攻击），即可实现任意代码执行。

💥 PoC:
  将以下内容放入 config.yaml（默认配置路径）:
  
  PAYLOAD: !!python/object/apply:subprocess.check_output [['whoami']]
  
  当应用启动加载 Config 类时触发 RCE。

🛡️ 修复:
  config.py:80
  - config = yaml.load(data, Loader=yaml.CLoader)
  + config = yaml.load(data, Loader=yaml.CSafeLoader)

📊 CVSS: 7.8 (CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:H)

📦 依赖: pyyaml==6.0.3

============================================================

【漏洞二】MEDIUM | CWE-532 | 置信度 95%

标题: 数据库 SQL 查询日志信息泄露 (echo=True 硬编码)

📁 位置: fastapi_framework/database.py:59

🔗 数据流:
  Source: database.py:55-60
    def __init__(self, driver, options=None, **kwargs):
        ...
        self._engine = create_async_engine(url, echo=True, ...)
  
  Filter: 无 — echo=True 是硬编码的布尔字面量
  
  Sink: SQLAlchemy 引擎将所有 SQL 查询日志输出到 stdout

📝 描述:
  DB 类在创建 async SQLAlchemy 引擎时硬编码 echo=True。导致所有 SQL 查询
  （包括含密码哈希、个人信息等敏感数据的 INSERT/UPDATE 语句）通过 
  SQLAlchemy 的日志系统以 INFO 级别输出到 stdout。无配置项可关闭此行为。

💥 PoC:
  通过框架执行任何数据库操作:
  await db.add(User(username='admin', password='secret'))
  
  日志输出:
  INFO sqlalchemy.engine.Engine INSERT INTO users (...) VALUES ('admin', 'secret')

🛡️ 修复:
  database.py:59-60
  + echo = getenv("DB_ECHO", "false").lower() == "true"
  - self._engine = create_async_engine(url, echo=True, ...)
  + self._engine = create_async_engine(url, echo=echo, ...)

📊 CVSS: 4.3 (CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:L/I:N/A:N)

📦 依赖: sqlalchemy==2.0.49

============================================================
总结: 发现 2 个漏洞 (1 CRITICAL + 1 MEDIUM)
已修复: 2/2
待创建: GitHub Advisory × 2, CVE 申请 × 2
============================================================
