## Logging guide for aachen-termin-bot

This document explains where logs go, how they are formatted, which modules emit which messages, and how to control verbosity. It’s based on the current code in `aachen-termin-bot`.

### Quick summary

- Default sink: stdout/stderr (you typically redirect to a file via shell).
- Format: `%(asctime)s - %(levelname)s - %(message)s` (for example: `2025-09-21 12:34:56,789 - INFO - 启动 SuperC 预约检查程序...`).
- Levels used: INFO, WARNING, ERROR (no DEBUG in code). Some step logs are gated by a verbose flag.
- Verbose toggle: `superc/config.py` → `VERBOSE_LOGGING` controls extra “step” logs via `log_verbose()`.
- Artifacts saved for debugging: HTML pages and captcha images saved to disk; their paths are logged.


## Configuration and sinks

- Config file: `superc/config.py`
	- `LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'`
	- `LOG_LEVEL = 'INFO'` (note: the main script currently hard-codes `INFO` when calling `basicConfig`)
	- `VERBOSE_LOGGING = False` (set to `True` to see detailed step logs from the checker)

- Initialization:
	- `superc.py` and `infostelle.py` call: `logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)`
	- When running headless, recommended shell redirection (examples in `superc.py` header comments):
		- Interactive: `source .venv/bin/activate && python3 superc.py 2>&1`
		- Background: `source .venv/bin/activate && nohup python3 superc.py >> superc.log 2>&1 &`

- Handlers: no explicit file handler in production code. Logs go to stdout/stderr unless the shell redirects.
	- Tests sometimes add a file handler (e.g., `tests/test_form_parsing.py` writes `test_form_parsing.log`).


## Log entry format

- Format string: `%(asctime)s - %(levelname)s - %(message)s`
- Example:
	- `2025-09-21 00:05:32,102 - INFO - 启动 SuperC 预约检查程序，进程PID: 12345`
	- Some errors include tracebacks via `exc_info=True` (e.g., unexpected exceptions in the main loop).


## Verbose mode

- `superc/appointment_checker.py` defines `log_verbose(message: str, level=logging.INFO)`.
- When `VERBOSE_LOGGING` is `True` (in `superc/config.py`), step-by-step messages are emitted for navigation between pages (“Schritt 2…6”).
- Other modules’ info logs are not gated by `VERBOSE_LOGGING` and will still appear at level INFO.


## What gets logged, by module

### aachen-termin-bot/superc.py (main scheduler)

Key INFO logs:
- Process start with PID: `启动 SuperC 预约检查程序，进程PID: …`
- Profile loading: `已加载hanbin_profile` or `无法加载hanbin_profile` (WARNING)
- Current DB profile selected: `当前处理用户: {full_name} (ID: …)` and a printed block of profile details
- Queue state: `没有更多等待的用户` or `等待队列为空，仅使用hanbin profile进行检查`
- Hourly stop: at 01:00 → `已到凌晨 1 点，程序自动退出`
- Appointment flow:
	- No slot: loop sleeps silently for ~60s (message is suppressed, but step logs may show from checker)
	- Slot found → downstream modules report details
	- Success: `成功！ {message}`
	- Status updates:
		- On too-many-requests: sets DB status to `error`
		- On booking success: sets DB status to `booked` (may include the appointment datetime)
	- After processing: `处理完成！立即检查是否有下一个用户需要处理...` then either continues or exits

Error/Warning paths:
- File/profile issues: `无法读取hanbin profile文件 ...` (ERROR)
- DB issues: `获取数据库profile失败: ...` (ERROR) / `获取下一个用户profile失败: ...` (ERROR)
- Rate limit (German message “zu vieler Terminanfragen”): logged as ERROR and used to mark status `error`
- Unexpected messages forwarded from checker: `出现未预期的消息: ...` (WARNING)
- Unexpected exceptions in the loop: `检查过程中发生未预料的错误` with traceback


### aachen-termin-bot/superc/appointment_checker.py (Schritt 2–6)

Step navigation (gated by `VERBOSE_LOGGING` via `log_verbose`):
- `=== 进入Schritt 2页面 ===`
- `成功进入Schritt 2页面`
- `Schritt 2 完成: 成功选择服务类型`
- `=== 进入Schritt 3页面 ===`
- `成功进入Schritt 3页面` / `Schritt 3 完成: 成功提取位置信息`
- `=== 进入Schritt 4页面 ===`

Availability and selection:
- Page validation failures for steps 2/3/4/5 → ERROR/WARNING with reason
- When available slots exist: `Schritt 4 页面: 发现可用预约时间` (INFO)
- If no slots: `当前没有可用预约时间` (INFO returned up to caller)

Form and confirmation:
- Step 5 submit: `Schritt 5: 正在提交预约选择...` → on success: `Schritt 5: 成功选择时间，现在填写表单...`
- Which profile is used is logged in `appointment_selector` (see below)
- On captcha retries and form submission results, see `form_filler`
- Step 6: `Schritt 6: 预约已完成，等待邮件确认` then final success: `预约成功完成: ...`

Common error messages surfaced:
- 页面验证失败/未进入预期 Schritt
- 提交时间后未进入 Schritt 5
- 内部错误：form_data/selected_profile/soup 为空（defensive checks）


### aachen-termin-bot/superc/form_filler.py (form analysis, captcha, submit)

Field analysis and mapping (INFO unless noted):
- Begin analysis: `开始分析表单字段...` → `总共找到 N 个字段`
- Comparison with expected fields: missing/extra fields with details; unmatched required fields logged as WARNING
- Mapping summary: `开始映射Profile数据到表单字段...` → per-field mapping lines and fixed fields
- Hidden inputs discovered are logged: `隐藏字段: name = 'value'`
- Summary and validation: key fields (captcha, email, hunangskrukka) are echoed; validation errors are logged as ERROR

Captcha and submission:
- Captcha download: path logged by `utils.download_captcha`
- Captcha recognition: `开始识别验证码: ...` → `验证码识别结果: ...` or `验证码识别失败`
- Submit target and headers: `提交URL: ...` and `准备提交请求，headers: {...}`
- HTTP result: `表单提交响应状态码: ...`
- Success: `预约成功！`
- Known errors (mapped to Chinese):
	- `zu vieler Terminanfragen` → `提交过于频繁，请稍后再试` (ERROR)
	- `Sicherheitsfrage` → `验证码错误` (ERROR) with DOM-based detection
	- `Geburtsdatum` → `生日格式错误` (ERROR)
	- `Bitte überprüfen Sie Ihre Eingaben` / `fehlerhafte Eingaben` → input validation errors
	- Unknown error: logs first 500 chars of response and saves HTML

Captcha retry wrapper:
- On retryable captcha failure: `验证码错误 (第X次尝试)，准备重试...` (WARNING), final failure at max retries (ERROR)
- Non-captcha failure: `检测到非验证码错误，不进行重试`

PII note: This module logs personally identifiable information (name, email, phone) and full form data in INFO logs. Consider turning off background log collection or sanitizing in production environments.


### aachen-termin-bot/superc/utils.py (helpers)

- `save_page_content(...)`: saves HTML for debugging and logs the saved path: `页面内容已保存到: ...`
- `download_captcha(...)`: saves captcha image and logs path, or logs errors if fetch fails.

Note: HTML is saved under `data/pages/{location}/...`, captcha under `pages/{location}/captcha/...` (intentional but inconsistent base folder names).


### aachen-termin-bot/superc/appointment_selector.py

- When a slot is parsed: `找到可用时间: {date time}, 选择profile: {name}`
- Profile decision logs:
	- Before October → use `hanbin_profile`
	- From October → prefer `current_profile`, fallback to `hanbin_profile`
- Parsing issues: warnings like `无法从 '...' 解析日期...`


### aachen-termin-bot/infostelle.py (secondary entrypoint)

- Similar pattern to `superc.py` but without DB queue integration; emits start, success, and error/exception logs around the loop.


## Saved artifacts (for offline debugging)

- HTML snapshots:
	- `data/pages/{location}/step_{name}_{YYYYmmdd_HHMMSS}.html`
	- Created by `save_page_content`; used after form selection, submission, and on error paths.
- Captcha images:
	- `pages/{location}/captcha/captcha_{YYYYmmdd_HHMMSS}.png`
	- Created by `download_captcha` before solving.

These file writes are always accompanied by INFO logs with the full path.


## How to control logging

- Toggle verbose step logs:
	- Edit `superc/config.py`: set `VERBOSE_LOGGING = True`.
	- Affects only messages wrapped by `log_verbose` (mainly step transitions in the checker).

- Change log level/format:
	- Currently, `superc.py` hard-codes `level=logging.INFO` when calling `basicConfig`, so `LOG_LEVEL` in config is not applied programmatically.
	- You can lower noise by changing INFO lines in code to DEBUG and adjusting `basicConfig(level=logging.WARNING)`—or by adding your own `logging.FileHandler` with a higher level.

- Redirect logs to a file (typical production):
	- `source .venv/bin/activate && nohup python3 superc.py >> superc.log 2>&1 &`
	- Rotate externally (logrotate/cron) or use a Python `RotatingFileHandler` if you prefer in-code rotation.


## Common log sequences and troubleshooting

- No slots available:
	- Checker returns `当前没有可用预约时间` (INFO). Main loop sleeps ~60s and repeats.

- Slot appears, then captcha troubles:
	- See a series of `验证码错误 (第X次尝试)` and final `验证码重试失败...` if max retries reached.

- Rate-limited by the site:
	- ERROR: `提交过于频繁，请稍后再试 (关键词: zu vieler Terminanfragen)`
	- Main marks DB status `error` and fetches next user if any.

- Successful booking:
	- INFO: `Schritt 4 页面: 发现可用预约时间` → Step 5 → Step 6 → `预约成功完成: ...`
	- Main updates DB status to `booked` (possibly with the appointment datetime) and proceeds to next user.


## Known gaps and suggestions

- `LOG_LEVEL` isn’t currently honored by `superc.py`; consider wiring it through to `basicConfig`.
- Consider standardizing artifact folders (either all under `data/pages/...` or `pages/...`) for consistency.
- If PII logging is a concern, add a redact/sanitize layer or gate more INFO logs behind `VERBOSE_LOGGING`.


— End —

