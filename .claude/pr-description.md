## Summary

This PR fixes **2 security vulnerabilities** discovered during a security audit of the fastapi-framework codebase.

### 🔴 1. CWE-502: YAML Unsafe Deserialization — Arbitrary Code Execution

📁 `fastapi_framework/config.py:80`  
📊 CVSS: 7.8 (HIGH) — `CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:H`

**Data Flow:**
```
config.py:72 open(config_file_path) → config.py:80 yaml.load(data, Loader=yaml.CLoader)
```

`yaml.CLoader` is the C implementation of `yaml.Loader` — **not** `yaml.SafeLoader`. It supports the full YAML tag set including `!!python/object` which allows instantiation of arbitrary Python classes. An attacker who can modify the YAML config file can achieve RCE.

**PoC (malicious config.yaml):**
```yaml
PAYLOAD: !!python/object/apply:subprocess.check_output [['whoami']]
```

**Fix:** Replace `yaml.CLoader` with `yaml.CSafeLoader` (the safe C-based loader).

### 🟡 2. CWE-532: SQL Query Information Leakage via Hardcoded `echo=True`

📁 `fastapi_framework/database.py:59`  
📊 CVSS: 4.3 (MEDIUM) — `CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:L/I:N/A:N`

**Data Flow:**
```
database.py:59 echo=True → create_async_engine() → SQLAlchemy logging → stdout
```

`echo=True` is **hardcoded** in `DB.__init__()`, causing ALL SQL queries (including INSERT with password hashes, PII) to be logged to stdout. No configuration option exists to disable it.

**Fix:** Replace hardcoded `echo=True` with `getenv("DB_ECHO", "false").lower() == "true"`, defaulting to `false`.

## Checklist
- [x] Tested locally
- [x] Backward compatible (default behavior preserved where safe)
- [x] Non-breaking changes
- [ ] Please request CVE via GitHub Advisory after merge

🤖 Generated with [Claude Code](https://claude.com/claude-code)
