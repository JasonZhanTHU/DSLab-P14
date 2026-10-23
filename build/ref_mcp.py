#!/usr/bin/env python3
"""Minimal MCP (stdio) server exposing the ref_tools.py reference tools.

No dependencies: speaks newline-delimited JSON-RPC 2.0 as per the MCP stdio transport.
Register it with an MCP client, e.g. Claude Code:

  claude mcp add study-refs -- python3 /home/xizhan/scrapbot/ref_mcp.py
"""
import json
import sys

from ref_tools import TOOLS, RefLibrary

PROTOCOL = "2025-06-18"


def main():
    lib = None
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        mid, method = msg.get("id"), msg.get("method")
        if mid is None:  # notification (e.g. notifications/initialized)
            continue
        if method == "initialize":
            result = {"protocolVersion": msg.get("params", {}).get("protocolVersion", PROTOCOL),
                      "capabilities": {"tools": {}},
                      "serverInfo": {"name": "study-refs", "version": "1.0"},
                      "instructions": "Search/read ~1000 English Wikipedia articles on earth "
                                      "sciences, physics, chemistry and maths. Query in English."}
        elif method == "tools/list":
            result = {"tools": [{"name": t["name"], "description": t["description"],
                                 "inputSchema": t["input_schema"]} for t in TOOLS]}
        elif method == "tools/call":
            lib = lib or RefLibrary()  # lazy: keeps the handshake fast
            p = msg.get("params", {})
            text = lib.call(p.get("name", ""), p.get("arguments") or {})
            result = {"content": [{"type": "text", "text": text}],
                      "isError": json.loads(text).get("error") is not None}
        elif method == "ping":
            result = {}
        else:
            reply = {"jsonrpc": "2.0", "id": mid,
                     "error": {"code": -32601, "message": f"method not found: {method}"}}
            print(json.dumps(reply), flush=True)
            continue
        print(json.dumps({"jsonrpc": "2.0", "id": mid, "result": result}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
