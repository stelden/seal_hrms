# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt
"""Serve dev.local to the Self Service walk from ONE process, ONE connection and ONE transaction.

Copied from seal_desk's P3 harness (``.worktrees/p3-app/seal_desk/e2e/phone/harness.py``) and
extended, never edited there: the walk needs seal_desk's real shell, so this serves the worktree
code of seal_desk (P6 if it has commits, else P3), seal_frontend (P1), seal_common (P6 if ready,
else P2c) and this worktree's seal_hrms, with the DocTypes and columns those bring borrowed into
the transaction (seal_desk's notes below hold). The people and rules are seal_hrms' (``seed.py``).

- ``frappe.connect`` hands every request the held connection; ``close`` does nothing.
- each request starts at a savepoint; Frappe's ``commit`` moves the savepoint and its
  ``rollback`` returns to it, so a request behaves as on a real site while nothing is ever
  committed. Everything is rolled back when the server stops (SIGTERM from Playwright).
- Redis keys get their own prefix (sessions, rate limits, lockout counters, caches), so no
  other process on the bench ever sees them; they are deleted at the end.
- No text message leaves: the sender is replaced and the codes are kept for the suite.
  No mail leaves; no background job runs, except the push for a Notification Log, which is
  run at once (as a worker would); nobody in this walk has a phone subscribed, so none is sent.

The suite reads what it needs from ``/__harness/*`` (codes, seeded names, record states).

    /home/frappe/frappe-bench/env/bin/python e2e/phone/harness.py [port]
"""

import json
import os
import signal
import sys
from unittest.mock import patch

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = "/home/frappe/frappe-bench"
SITE = os.environ.get("PHONE_E2E_SITE", "dev.local")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PHONE_E2E_PORT", "8097"))
#: This worktree's seal_hrms first, then seal_desk's shell, seal_frontend (treated as installed) and seal_common.


def _worktree(env: str, later: str, base: str) -> str:
	"""``later`` (a P6 worktree) once it has commits of its own, else ``base``, unless the environment names one.

	A later phase's worktree that has only been branched holds work in progress (uncommitted
	edits); the walk runs on committed code only.
	"""
	import subprocess

	if os.environ.get(env):
		return os.environ[env]

	def head(path):
		try:
			return subprocess.run(["git", "-C", path, "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
		except Exception:
			return None

	return later if os.path.exists(os.path.join(later, ".git")) and head(later) not in (None, head(base)) else base


SEAL_HRMS = os.path.dirname(os.path.dirname(HERE))
SEAL_DESK = _worktree("PHONE_E2E_SEAL_DESK", f"{BENCH}/.worktrees/p6-desk/seal_desk", f"{BENCH}/.worktrees/p3-app/seal_desk")
SEAL_FRONTEND = os.environ.get("PHONE_E2E_SEAL_FRONTEND", f"{BENCH}/.worktrees/p1-pwa/seal_frontend")
SEAL_COMMON = _worktree("PHONE_E2E_SEAL_COMMON", f"{BENCH}/.worktrees/p6-common/seal_common", f"{BENCH}/.worktrees/p2c-push/seal_common")
PREFIX = f"phone-e2e-hr-{PORT}|"
SAVEPOINT = "phone_e2e_request"

for path in (SEAL_COMMON, SEAL_FRONTEND, SEAL_DESK, SEAL_HRMS):
	if path and os.path.isdir(path):
		sys.path.insert(0, path)
sys.path.insert(0, HERE)
os.chdir(os.path.join(BENCH, "sites"))

import frappe  # noqa: E402
import frappe.app  # noqa: E402
from frappe.utils.redis_wrapper import RedisWrapper  # noqa: E402

#: What every request's site config says on top of the site's own.
CONF = {"host_name": f"http://localhost:{PORT}", "developer_mode": 1, "seal_dev_otp": None}


# --- Redis: a prefix of our own ------------------------------------------------------------

_real_make_key = RedisWrapper.make_key


def _make_key(self, key, user=None, shared=False):
	made = _real_make_key(self, key, user=user, shared=shared)
	if isinstance(made, bytes):
		return made if made.startswith(PREFIX.encode()) else PREFIX.encode() + made
	return made if made.startswith(PREFIX) else PREFIX + made


def _forget_redis_keys() -> None:
	connection = frappe.cache
	for key in connection.scan_iter(match=PREFIX.encode() + b"*", count=1000):
		connection.delete(key)


# --- one connection, one transaction ------------------------------------------------------


class Held:
	"""The connection every request uses, and the patches that make it the only one."""

	def __init__(self):
		frappe.init(site=SITE, sites_path=".")
		frappe.local.conf.update(CONF)
		frappe.connect()
		self.db = frappe.local.db
		self.temporary: set[str] = set()
		db = self.db
		real_columns = db.get_db_table_columns
		real_tables = db.get_tables

		def commit(*, chain=False):
			db.before_commit.run()
			db.after_commit.reset()  # realtime, mail and queued jobs never leave
			db.value_cache.clear()
			db.sql(f"savepoint {SAVEPOINT}")

		def rollback(*, save_point=None, chain=False):
			if save_point:
				db.sql(f"rollback to savepoint {save_point}")
				db.value_cache.clear()
				return
			db.before_commit.reset()
			db.after_commit.reset()
			db.before_rollback.run()
			db.sql(f"rollback to savepoint {SAVEPOINT}")
			db.value_cache.clear()
			db.after_rollback.run()

		def refuse_ddl(query, *args, **kwargs):
			raise AssertionError(f"the phone harness never changes the schema: {query[:120]}")

		def columns(table):
			if table in self.temporary:
				return [row[0] for row in db.sql(f"show columns from `{table}`")]
			return real_columns(table)

		def tables(cached=True):
			return list(set(real_tables(cached=cached)) | self.temporary)

		for name, value in {
			"commit": commit,
			"rollback": rollback,
			"begin": lambda *, read_only=False: None,
			"close": lambda: None,
			"sql_ddl": refuse_ddl,
			"get_db_table_columns": columns,
			"get_tables": tables,
		}.items():
			setattr(db, name, value)

	def connect(self, site=None, db_name=None, set_admin_as_user=True):
		frappe.local.db = self.db
		if set_admin_as_user:
			frappe.set_user("Administrator")


_real_init = frappe.init


def _init(*args, **kwargs):
	_real_init(*args, **kwargs)
	frappe.local.conf.update(CONF)


# --- what the suite reads and asks for ------------------------------------------------------

SENT_CODES: list[dict] = []
#: ``/__harness/stale``: the next sensitive action finds no fresh check, as five minutes after
#: signing in would (seal_common otp.recent); a fresh check (password, passkey) ends it.
STALE = {"on": False}
PUSHES: list[dict] = []


def _send_text(contact, channel, otp_code, purpose):
	"""seal_common's sender, replaced: the code is kept here and never sent."""
	SENT_CODES.append({"to": contact, "channel": channel, "code": otp_code, "purpose": purpose})
	return True


def side_channel(path: str, query: dict, body: dict):
	"""``/__harness/<path>``: answers for the suite, run as Administrator in the transaction."""
	import seed

	if path == "ready":
		return {"ok": True}
	if path == "seeded":
		return seed.SEEDED
	if path == "codes":
		return SENT_CODES
	if path == "stale":
		STALE["on"] = True
		return {"ok": True}
	if path == "state":
		return seed.state()
	if path == "push":
		return seed.push_answers()
	if path == "set":
		# One Login Settings value for this run, e.g. ask_for_code (rolled back at the end).
		frappe.db.set_single_value("Login Settings", body["field"], body["value"])
		return {"ok": True}
	raise ValueError(f"unknown harness path {path}")


def side_channel_app(environ, start_response):
	from urllib.parse import parse_qsl

	path = environ["PATH_INFO"][len("/__harness/") :]
	query = dict(parse_qsl(environ.get("QUERY_STRING", "")))
	length = int(environ.get("CONTENT_LENGTH") or 0)
	body = json.loads(environ["wsgi.input"].read(length) or b"{}") if length else {}
	frappe.init(site=SITE, sites_path=".")
	HELD.connect()
	HELD.db.sql(f"savepoint {SAVEPOINT}")
	try:
		result = side_channel(path, query, body)
		status, payload = "200 OK", result
	except Exception as error:  # the suite prints it
		frappe.db.rollback()
		status, payload = "500 Internal Server Error", {"error": f"{type(error).__name__}: {error}"}
	finally:
		frappe.set_user("Administrator")
	frappe.destroy()
	data = json.dumps(payload, default=str).encode()
	start_response(status, [("Content-Type", "application/json"), ("Content-Length", str(len(data)))])
	return [data]


# --- serving -------------------------------------------------------------------------------


def build_app():
	from werkzeug.middleware.shared_data import SharedDataMiddleware

	frappe.app._site = SITE
	site_app = frappe.app.application

	def per_request(environ, start_response):
		# Every request starts at the savepoint its commit and rollback come back to
		# (through the cursor: there is no site context yet for frappe.db.sql's logging).
		HELD.db._cursor.execute(f"savepoint {SAVEPOINT}")
		return site_app(environ, start_response)

	app = SharedDataMiddleware(
		per_request,
		{
			"/assets/seal_desk": f"{SEAL_DESK}/seal_desk/public",
			"/assets/seal_frontend": f"{SEAL_FRONTEND}/seal_frontend/public",
			"/assets/seal_hrms": f"{SEAL_HRMS}/seal_hrms/public",
		},
		cache=False,
	)
	app = SharedDataMiddleware(app, {"/assets": f"{BENCH}/sites/assets", "/files": f"{BENCH}/sites/{SITE}/public/files"}, cache=False)

	def application(environ, start_response):
		if environ["PATH_INFO"].startswith("/__harness/"):
			return side_channel_app(environ, start_response)
		# PHONE_E2E_LOG=1: one line per request, with the session cookie sent and set (D181).
		if not os.environ.get("PHONE_E2E_LOG"):
			return app(environ, start_response)
		import re
		import time

		sent = re.search(r"sid=([^;]+)", environ.get("HTTP_COOKIE", ""))

		def logging_start(status, headers, *rest):
			got = [v for k, v in headers if k.lower() == "set-cookie" and v.startswith("sid=")]
			print(f"{time.time():.3f} {environ['REQUEST_METHOD']} {environ['PATH_INFO'][:70]} sent={sent and sent.group(1)[:8]} set={got and got[0][4:12]}", flush=True)
			return start_response(status, headers, *rest)

		return app(environ, logging_start)

	return application


def main() -> int:
	global HELD
	import seed
	from werkzeug.serving import WSGIRequestHandler, make_server

	class Quiet(WSGIRequestHandler):
		def log_request(self, *args, **kwargs):  # errors still print; each request does not
			pass

	RedisWrapper.make_key = _make_key
	HELD = Held()
	installed = frappe.get_installed_apps

	def with_seal_frontend(*args, **kwargs):
		apps = list(installed(*args, **kwargs))
		return apps if "seal_frontend" in apps else [*apps, "seal_frontend"]

	from seal_common.messaging import push
	from seal_common.otp import otp, recent

	real_is_recent, real_stamp = recent.is_recent, recent.stamp

	def is_recent(*args, **kwargs):
		return False if STALE["on"] else real_is_recent(*args, **kwargs)

	def stamp(*args, **kwargs):
		STALE["on"] = False
		return real_stamp(*args, **kwargs)

	real_enqueue = frappe.enqueue
	real_post = push.post

	def enqueue(method, **kwargs):
		# The push for a Notification Log runs at once, as a worker would; nothing else queues.
		if method == "seal_common.messaging.push.send_for_log":
			kwargs.pop("enqueue_after_commit", None)
			return real_enqueue(method, **{**kwargs, "now": True})
		return None

	def post_and_keep(sub, payload, key, conf):
		status = real_post(sub, payload, key, conf)
		PUSHES.append({"subscription": sub.name, "status": status})
		return status

	stubs = [
		patch.object(frappe, "init", _init),
		patch.object(frappe, "connect", HELD.connect),
		patch.object(frappe, "get_installed_apps", with_seal_frontend),
		patch.object(frappe, "enqueue", enqueue),
		patch.object(frappe, "sendmail", lambda *a, **k: None),
		patch.object(frappe, "publish_realtime", lambda *a, **k: None),
		patch.object(otp, "_send_otp_message", _send_text),
		patch.object(push, "post", post_and_keep),
		patch.object(recent, "is_recent", is_recent),
		patch.object(recent, "stamp", stamp),
	]
	for stub in stubs:
		stub.start()
	server = None
	stopping = {"now": False}

	def stop(*_):
		stopping["now"] = True
		raise KeyboardInterrupt

	signal.signal(signal.SIGTERM, stop)
	try:
		frappe.set_user("Administrator")
		HELD.temporary |= seed.borrow_schema()
		seed.seed()
		HELD.db.sql(f"savepoint {SAVEPOINT}")
		frappe.destroy()  # the held connection stays open (close does nothing)
		server = make_server("127.0.0.1", PORT, build_app(), threaded=False, request_handler=Quiet)
		print(f"phone harness: {SITE} on http://localhost:{PORT} (seal_hrms {SEAL_HRMS}, seal_desk {SEAL_DESK}, seal_common {SEAL_COMMON})", flush=True)
		server.serve_forever()
	except KeyboardInterrupt:
		pass
	finally:
		if server:
			server.server_close()
		for stub in reversed(stubs):
			stub.stop()
		try:
			HELD.db._cursor.execute("rollback")
		finally:
			HELD.db._conn.close()
			_forget_redis_keys()
			RedisWrapper.make_key = _real_make_key
		print("phone harness: rolled back and closed", flush=True)
	return 0


if __name__ == "__main__":
	sys.exit(main())
