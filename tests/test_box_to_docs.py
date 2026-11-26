import importlib.util
import json
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent


def load_module():
    spec = importlib.util.spec_from_file_location(
        "box_to_docs", ROOT / "box-to-docs.py"
    )
    module = importlib.util.module_from_spec(spec)
    import sys

    sys.path.insert(0, str(ROOT))
    spec.loader.exec_module(module)
    return module


OLD = "https://www.hackthebox.com/storage/avatars/{}.png"
NEW = "https://cdn.services-k8s.prod.aws.htb.systems/content/machines/avatar/{}.png"


def ext(url):
    return {"type": "external", "external": {"url": url}}


def page(page_id, box_id, icon, cover):
    return {
        "object": "page",
        "id": page_id,
        "properties": {"Box ID": {"number": box_id}},
        "icon": icon,
        "cover": cover,
    }


def machine(mod, box_id, name):
    return mod.Machine(
        id=box_id,
        name=name,
        os="Linux",
        release="2024-01-01T00:00:00.000000Z",
        isTodo=False,
        difficultyText="Easy",
        star=4.5,
        playInfo={"isActive": None, "expires_at": None},
        authUserInUserOwns=False,
        authUserInRootOwns=None,
        avatar=NEW.format(name),
    )


class FakeResponse:
    def __init__(self, status, body=None, headers=None):
        self.status_code = status
        self._body = body or {}
        self.headers = headers or {}
        self.text = json.dumps(self._body)

    def json(self):
        return self._body


class FakeNotion:
    """Serves a database query in pages of two and records writes."""

    def __init__(self, pages, fail_create=()):
        self.pages = pages
        self.fail_create = set(fail_create)
        self.calls = []

    def __call__(self, method, url, headers=None, json=None):
        self.calls.append((method, url, json))
        if method == "POST" and url.endswith("/query"):
            start = int((json or {}).get("start_cursor") or 0)
            chunk = self.pages[start : start + 2]
            more = start + 2 < len(self.pages)
            return FakeResponse(
                200,
                {
                    "results": chunk,
                    "has_more": more,
                    "next_cursor": str(start + 2) if more else None,
                },
            )
        if method == "POST" and url.endswith("/pages"):
            name = json["properties"]["Name"]["title"][0]["text"]["content"]
            if name in self.fail_create:
                return FakeResponse(400, {"message": "bad"})
            return FakeResponse(200, {"id": "new"})
        if method == "PATCH":
            return FakeResponse(200, {})
        raise AssertionError(f"unexpected call {method} {url}")

    def writes(self):
        return [(m, u, j) for m, u, j in self.calls if not u.endswith("/query")]


class TestBoxToDocs(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()
        self.mod.args = Namespace(database_id="db", dry_run=False)
        self.mod.notion_token = "token"
        self.mod.NOTION_DB_CACHE.clear()
        self.mod.NOTION_DB_LOADED = False
        patcher = mock.patch.object(self.mod, "sleep", lambda s: None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_with(self, fake, machines):
        with mock.patch.object(self.mod.requests, "request", fake):
            self.mod.update_notion_database(machines)

    def test_avatar_url_forms(self):
        f = self.mod.htb_avatar_url
        want = "https://labs.hackthebox.com/storage/avatars/a.png"
        self.assertEqual(f("/storage/avatars/a.png"), want)
        self.assertEqual(f("storage/avatars/a.png"), want)
        self.assertEqual(f("avatars/a.png"), want)
        self.assertEqual(f(NEW.format("a")), NEW.format("a"))

    def test_staleness_rules(self):
        stale = self.mod.art_is_stale
        new = NEW.format("a")
        self.assertTrue(stale(ext(OLD.format("a")), new))
        self.assertTrue(
            stale(ext("https://labs.hackthebox.com/storage/avatars/a.png"), new)
        )
        self.assertFalse(stale(ext(new), new))
        self.assertFalse(stale(None, new))
        self.assertFalse(stale({"type": "emoji", "emoji": "📦"}, new))
        self.assertFalse(stale({"type": "file", "file": {"url": "https://s3/x"}}, new))
        self.assertFalse(stale(ext("https://images.unsplash.com/x.jpg"), new))
        self.assertFalse(stale(ext("https://evilhackthebox.com/x.png"), new))

    def test_repairs_stale_art_and_creates_missing(self):
        pages = [
            page("p-old", 1, ext(OLD.format("x")), ext(OLD.format("x"))),
            page("p-ok", 2, ext(NEW.format("ok")), ext(NEW.format("ok"))),
            page("p-custom", 3, {"type": "emoji", "emoji": "🔥"}, ext(OLD.format("y"))),
            page("p-dup", 1, ext(OLD.format("x")), ext(OLD.format("x"))),
            page("p-noart", 5, None, None),
        ]
        fake = FakeNotion(pages)
        machines = [
            machine(self.mod, 1, "old"),
            machine(self.mod, 2, "ok"),
            machine(self.mod, 3, "custom"),
            machine(self.mod, 4, "brandnew"),
            machine(self.mod, 5, "noart"),
        ]
        self.run_with(fake, machines)

        queries = [c for c in fake.calls if c[1].endswith("/query")]
        self.assertEqual(len(queries), 3, "should page through the whole database once")

        writes = {(m, u.rsplit("/", 1)[-1]): j for m, u, j in fake.writes()}
        self.assertEqual(
            writes[("PATCH", "p-old")],
            {"icon": ext(NEW.format("old")), "cover": ext(NEW.format("old"))},
        )
        self.assertIn(("PATCH", "p-dup"), writes)
        self.assertEqual(
            writes[("PATCH", "p-custom")], {"cover": ext(NEW.format("custom"))}
        )
        self.assertNotIn(("PATCH", "p-ok"), writes)
        self.assertNotIn(("PATCH", "p-noart"), writes)
        created = writes[("POST", "pages")]
        self.assertEqual(created["icon"], ext(NEW.format("brandnew")))
        self.assertEqual(created["properties"]["Box ID"], {"number": 4})
        self.assertEqual(len(fake.writes()), 4)

    def test_dry_run_writes_nothing(self):
        self.mod.args.dry_run = True
        fake = FakeNotion(
            [page("p-old", 1, ext(OLD.format("x")), ext(OLD.format("x")))]
        )
        self.run_with(fake, [machine(self.mod, 1, "old"), machine(self.mod, 2, "new")])
        self.assertEqual(fake.writes(), [])

    def test_failed_create_does_not_stop_run(self):
        fake = FakeNotion([], fail_create={"bad"})
        self.run_with(
            fake,
            [machine(self.mod, 1, "bad"), machine(self.mod, 2, "good")],
        )
        names = [
            j["properties"]["Name"]["title"][0]["text"]["content"]
            for m, u, j in fake.writes()
        ]
        self.assertEqual(names, ["bad", "good"])

    def test_retries_rate_limits(self):
        responses = iter(
            [
                FakeResponse(429, headers={"Retry-After": "0"}),
                FakeResponse(200, {"ok": 1}),
            ]
        )
        with mock.patch.object(
            self.mod.requests, "request", lambda *a, **k: next(responses)
        ):
            r = self.mod.notion_request(
                "PATCH", "https://api.notion.com/v1/pages/x", json={}
            )
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main()
