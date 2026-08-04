#!/usr/bin/env python3
"""
ECU API 接口测试工具
在服务器构建/部署阶段调用，测试 ECU 管理所有接口功能。

用法:
    python scripts/test_ecu_api.py
    python scripts/test_ecu_api.py --url http://localhost:9999
    python scripts/test_ecu_api.py --url http://example.com:9999 --username admin --password 123456
"""

import argparse
import asyncio
import io
import os
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

import httpx
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise

from app.models.ecu import EcuOperationLog
from app.settings.config import settings


class Tester:
    BASE = "/api/v1"

    def __init__(self, url: str, username: str, password: str):
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self.token = None
        self.results = []
        self.vin = None
        self.target_name = None
        self.history_id = None
        self.operator_name = f"test_api_{datetime.now().strftime('%H%M%S')}"

    def _path(self, *parts):
        path = self.BASE
        for p in parts:
            path = f"{path.rstrip('/')}/{p.lstrip('/')}"
        return path

    async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        if self.token:
            headers["token"] = self.token
        async with httpx.AsyncClient(base_url=self.url, headers=headers, timeout=30) as c:
            return await c.request(method, path, **kwargs)

    def ok(self, name: str, detail: str = ""):
        self.results.append(("PASS", name))
        print(f"  [OK] {name}")
        if detail:
            for line in detail.split("\n"):
                print(f"       {line}")

    def fail(self, name: str, detail: str = ""):
        self.results.append(("FAIL", name))
        print(f"  [FAIL] {name}")
        if detail:
            for line in detail.split("\n"):
                print(f"       {line}")

    # ------------------------------------------------------------------

    def _make_excel(self, data: dict) -> io.BytesIO:
        df = pd.DataFrame([data])
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        return buf

    def _make_ecu_html(self, *, sw_version: str = "3.0.1") -> io.BytesIO:
        html = f"""<html><body><table>
<tr><td>TEST_ECU</td><td>F100</td><td>零件号</td><td>TEST-PART-001</td></tr>
<tr><td>TEST_ECU</td><td>F200</td><td>硬件版本</td><td>1.2.0</td></tr>
<tr><td>TEST_ECU</td><td>F300</td><td>软件版本</td><td>{sw_version}</td></tr>
<tr><td>TEST_ECU</td><td>F400</td><td>供应商</td><td>API测试</td></tr>
</table></body></html>"""
        return io.BytesIO(html.encode("utf-8"))

    # ------------------------------------------------------------------

    async def test_login(self):
        name = "POST /base/access_token  \u767b\u5f55\u83b7\u53d6token"
        try:
            resp = await self.request("POST", self._path("base", "access_token"), json={
                "username": self.username,
                "password": self.password,
            })
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                self.token = body["data"]["access_token"]
                self.ok(name, f"token={self.token[:30]}...")
            else:
                self.fail(name, f"status={resp.status_code} body={body}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_download_template(self):
        name = "GET  /ecu/target/template  \u4e0b\u8f7d\u57fa\u7ebf\u6a21\u677f"
        try:
            resp = await self.request("GET", self._path("ecu", "target", "template"))
            if resp.status_code == 200:
                self.ok(name, f"\u6587\u4ef6\u5927\u5c0f={len(resp.content)} bytes  content-type={resp.headers.get('content-type')}")
            else:
                self.fail(name, f"status={resp.status_code}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_create_target(self):
        name = "POST /ecu/target/update  \u521b\u5efa\u6d4b\u8bd5\u57fa\u7ebf"
        self.target_name = f"test_api_{datetime.now().strftime('%m%d%H%M%S')}"
        try:
            excel = self._make_excel({
                "hw_version": "1.2.0",
                "sw_version": "3.0.1",
                "description": "\u6d4b\u8bd5\u57fa\u7ebf",
            })
            resp = await self.request("POST", self._path("ecu", "target", "update"),
                data={"target_name": self.target_name},
                files={"file": ("test.xlsx", excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                self.ok(name, f"target_name={body['data']['target_name']}")
            else:
                self.fail(name, f"status={resp.status_code} body={body}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_list_targets(self):
        name = "GET  /ecu/target/list  \u57fa\u7ebf\u5217\u8868"
        try:
            resp = await self.request("GET", self._path("ecu", "target", "list"))
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                cnt = len(body["data"])
                found = any(t["target_name"] == self.target_name for t in body["data"])
                self.ok(name, f"\u5171{cnt}\u6761  \u6d4b\u8bd5\u57fa\u7ebf{'[FOUND]' if found else '[NOT_FOUND]'}")
            else:
                self.fail(name, f"status={resp.status_code}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_detail_target(self):
        name = "GET  /ecu/target/detail  \u57fa\u7ebf\u8be6\u60c5"
        try:
            resp = await self.request("GET", self._path("ecu", "target", "detail", self.target_name))
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                self.ok(name, f"target_name={body['data']['target_name']}")
            else:
                self.fail(name, f"status={resp.status_code} body={body}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_create_ecu(self):
        name = "POST /ecu/update  \u521b\u5efa\u6d4b\u8bd5ECU"
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        self.vin = f"TESTAPI{ts}"[:17]
        try:
            resp = await self.request("POST", self._path("ecu", "update"),
                data={"vin": self.vin},
                files={"file": ("test.html", self._make_ecu_html(), "text/html")},
            )
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                self.ok(name, f"vin={body['data']['vin']}")
            else:
                self.fail(name, f"status={resp.status_code} body={body}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_list_ecus(self):
        name = "GET  /ecu/list  ECU\u5217\u8868"
        try:
            resp = await self.request("GET", self._path("ecu", "list"))
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                cnt = len(body["data"])
                found = any(e["vin"] == self.vin for e in body["data"])
                self.ok(name, f"\u5171{cnt}\u6761  \u6d4b\u8bd5ECU{'[FOUND]' if found else '[NOT_FOUND]'}")
            else:
                self.fail(name, f"status={resp.status_code}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_ecu_search(self):
        name = "GET  /ecu/list?search=  \u641c\u7d22ECU"
        try:
            resp = await self.request("GET", self._path("ecu", "list"), params={"search": "TESTAPI"})
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                cnt = len(body["data"])
                self.ok(name, f"\u547d\u4e2d{cnt}\u6761")
            else:
                self.fail(name, f"status={resp.status_code}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_detail_ecu(self):
        name = "GET  /ecu/detail  ECU\u8be6\u60c5"
        try:
            resp = await self.request("GET", self._path("ecu", "detail", self.vin))
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                self.ok(name, f"vin={body['data']['vin']}")
            else:
                self.fail(name, f"status={resp.status_code} body={body}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_update_ecu(self):
        name = "POST /ecu/update  \u66f4\u65b0ECU\u89e6\u53d1\u5386\u53f2"
        try:
            html = self._make_ecu_html(sw_version="9.9.9")
            resp = await self.request("POST", self._path("ecu", "update"),
                data={"vin": self.vin},
                files={"file": ("test.html", html, "text/html")},
            )
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                self.ok(name, f"\u5386\u53f2\u5df2\u89e6\u53d1")
            else:
                self.fail(name, f"status={resp.status_code} body={body}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_update_remark(self):
        name = "POST /ecu/remark  \u66f4\u65b0\u5907\u6ce8"
        try:
            resp = await self.request("POST", self._path("ecu", "remark", self.vin),
                json={"remark": "\u901a\u8fc7API\u6d4b\u8bd5\u521b\u5efa"},
            )
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                self.ok(name, body["data"].get("message", ""))
            else:
                self.fail(name, f"status={resp.status_code} body={body}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_create_log(self):
        name = "POST /ecu/log  \u8bb0\u5f55\u64cd\u4f5c\u65e5\u5fd7"
        try:
            resp = await self.request("POST", self._path("ecu", "log"), json={
                "operation_type": "\u65b0\u5efa\u57fa\u7ebf",
                "target_vin": self.vin,
                "target_name": self.target_name,
                "operator": self.operator_name,
            })
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                self.ok(name, body["data"].get("message", ""))
            else:
                self.fail(name, f"status={resp.status_code} body={body}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_log_list(self):
        name = "GET  /ecu/log/list  \u65e5\u5fd7\u5217\u8868"
        try:
            resp = await self.request("GET", self._path("ecu", "log", "list"),
                params={"page": 1, "page_size": 10})
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                total = body.get("total", 0)
                self.ok(name, f"\u5171{total}\u6761  \u5f53\u524d\u9875{len(body['data'])}\u6761")
            else:
                self.fail(name, f"status={resp.status_code}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_log_stats(self):
        name = "GET  /ecu/log/stats  \u7edf\u8ba1\u4fe1\u606f"
        try:
            resp = await self.request("GET", self._path("ecu", "log", "stats"))
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                data = body["data"]
                self.ok(name, f"vehicle_total={data['vehicle_total']} target_total={data['target_total']}")
            else:
                self.fail(name, f"status={resp.status_code}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_log_chart(self):
        name = "GET  /ecu/log/chart  \u56fe\u8868\u6570\u636e"
        try:
            resp = await self.request("GET", self._path("ecu", "log", "chart"),
                params={"days": 7})
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                self.ok(name, f"\u8fd4\u56de{len(body['data'])}\u5929\u6570\u636e")
            else:
                self.fail(name, f"status={resp.status_code}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_log_operators(self):
        name = "GET  /ecu/log/operators  \u64cd\u4f5c\u8d26\u53f7"
        try:
            resp = await self.request("GET", self._path("ecu", "log", "operators"))
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                self.ok(name, f"{len(body['data'])}\u4e2a\u8d26\u53f7")
            else:
                self.fail(name, f"status={resp.status_code}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_history(self):
        name = "GET  /ecu/history  \u5386\u53f2\u8bb0\u5f55"
        try:
            resp = await self.request("GET", self._path("ecu", "history", self.vin))
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                cnt = len(body["data"])
                self.ok(name, f"\u5171{cnt}\u6761\u5386\u53f2\u8bb0\u5f55")
                if cnt > 0:
                    self.history_id = body["data"][0]["id"]
            else:
                self.fail(name, f"status={resp.status_code} body={body}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_history_detail(self):
        if not self.history_id:
            self.fail("GET  /ecu/history/{id}  \u5386\u53f2\u8be6\u60c5", "\u65e0\u5386\u53f2\u8bb0\u5f55\u53ef\u67e5\u8be2")
            return
        name = "GET  /ecu/history/{id}  \u5386\u53f2\u8be6\u60c5"
        try:
            resp = await self.request("GET", self._path("ecu", "history", self.vin, str(self.history_id)))
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                self.ok(name, f"history_id={body['data']['id']}")
            else:
                self.fail(name, f"status={resp.status_code} body={body}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_restore(self):
        if not self.history_id:
            self.fail("POST /ecu/restore  \u6062\u590d\u5386\u53f2", "\u65e0\u5386\u53f2\u8bb0\u5f55\u53ef\u6062\u590d")
            return
        name = "POST /ecu/restore  \u6062\u590d\u5386\u53f2\u7248\u672c"
        try:
            resp = await self.request("POST", self._path("ecu", "restore", self.vin, str(self.history_id)))
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                self.ok(name, body["data"].get("message", ""))
            else:
                self.fail(name, f"status={resp.status_code} body={body}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_delete_ecu(self):
        name = "DELETE /ecu/delete  \u5220\u9664\u6d4b\u8bd5ECU"
        try:
            resp = await self.request("DELETE", self._path("ecu", "delete", self.vin))
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                self.ok(name, body["data"].get("message", ""))
            else:
                self.fail(name, f"status={resp.status_code} body={body}")
        except Exception as e:
            self.fail(name, str(e))

    async def test_delete_target(self):
        name = "DELETE /ecu/target/delete  \u5220\u9664\u6d4b\u8bd5\u57fa\u7ebf"
        try:
            resp = await self.request("DELETE", self._path("ecu", "target", "delete", self.target_name))
            body = resp.json()
            if resp.status_code == 200 and body.get("code") == 200:
                self.ok(name, body["data"].get("message", ""))
            else:
                self.fail(name, f"status={resp.status_code} body={body}")
        except Exception as e:
            self.fail(name, str(e))

    async def cleanup_logs(self):
        name = "\u6e05\u7406\u6d4b\u8bd5\u65e5\u5fd7"
        try:
            await Tortoise.init(config=settings.TORTOISE_ORM)
            deleted = await EcuOperationLog.filter(operator=self.operator_name).delete()
            await Tortoise.close_connections()
            self.ok(name, f"\u5df2\u5220\u9664{deleted}\u6761\u6d4b\u8bd5\u65e5\u5fd7")
        except Exception as e:
            self.fail(name, str(e))

    # ------------------------------------------------------------------

    async def run(self):
        sep = "=" * 64
        print(f"\n{sep}")
        print(f"  ECU API \u63a5\u53e3\u6d4b\u8bd5\u5de5\u5177")
        print(f"  \u670d\u52a1\u5668: {self.url}")
        print(f"  \u65f6\u95f4: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{sep}\n")

        tests = [
            ("\u767b\u5f55", self.test_login),
            ("\u6a21\u677f\u4e0b\u8f7d", self.test_download_template),
            ("\u521b\u5efa\u57fa\u7ebf", self.test_create_target),
            ("\u57fa\u7ebf\u5217\u8868", self.test_list_targets),
            ("\u57fa\u7ebf\u8be6\u60c5", self.test_detail_target),
            ("\u521b\u5efaECU", self.test_create_ecu),
            ("ECU\u5217\u8868", self.test_list_ecus),
            ("ECU\u641c\u7d22", self.test_ecu_search),
            ("ECU\u8be6\u60c5", self.test_detail_ecu),
            ("\u66f4\u65b0ECU\u89e6\u53d1\u5386\u53f2", self.test_update_ecu),
            ("\u66f4\u65b0\u5907\u6ce8", self.test_update_remark),
            ("\u64cd\u4f5c\u65e5\u5fd7", self.test_create_log),
            ("\u65e5\u5fd7\u5217\u8868", self.test_log_list),
            ("\u7edf\u8ba1\u4fe1\u606f", self.test_log_stats),
            ("\u56fe\u8868\u6570\u636e", self.test_log_chart),
            ("\u64cd\u4f5c\u8d26\u53f7", self.test_log_operators),
            ("\u5386\u53f2\u8bb0\u5f55", self.test_history),
            ("\u5386\u53f2\u8be6\u60c5", self.test_history_detail),
            ("\u6062\u590d\u5386\u53f2", self.test_restore),
            ("\u5220\u9664ECU", self.test_delete_ecu),
            ("\u5220\u9664\u57fa\u7ebf", self.test_delete_target),
            ("\u6e05\u7406\u65e5\u5fd7", self.cleanup_logs),
        ]

        for label, fn in tests:
            print(f"[{tests.index((label, fn))+1}/{len(tests)}] {label}")
            await fn()
            print()

        passed = sum(1 for s, _ in self.results if s == "PASS")
        failed = sum(1 for s, _ in self.results if s == "FAIL")
        total = len(self.results)

        print(f"{sep}")
        print(f"  \u6d4b\u8bd5\u5b8c\u6210: {passed}/{total} \u901a\u8fc7, {failed} \u5931\u8d25")
        print(f"{sep}\n")

        return failed == 0


def main():
    parser = argparse.ArgumentParser(
        description="ECU API \u63a5\u53e3\u6d4b\u8bd5\u5de5\u5177 - \u5728\u6784\u5efa/\u90e8\u7f72\u9636\u6bb5\u8c03\u7528")
    parser.add_argument("--url", default="http://localhost:9999", help="\u670d\u52a1\u5668\u5730\u5740 (default: http://localhost:9999)")
    parser.add_argument("--username", default="admin", help="\u767b\u5f55\u7528\u6237\u540d (default: admin)")
    parser.add_argument("--password", default="123456", help="\u767b\u5f55\u5bc6\u7801 (default: 123456)")
    args = parser.parse_args()

    tester = Tester(args.url, args.username, args.password)
    success = asyncio.run(tester.run())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
