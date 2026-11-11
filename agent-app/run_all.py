"""
TRUSTMATE - Master Runner Script
Starts all 3 tiers of TRUSTMATE:
1. Person A's TRUSTMATE MCP Server on http://127.0.0.1:8001
2. Person B's FastAPI Agent Backend API on http://127.0.0.1:8000
3. Next.js Frontend on http://127.0.0.1:3000
"""

import subprocess
import sys
import time
import os

def main():
    agent_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(agent_dir)
    trust_mcp_dir = os.path.join(root_dir, "Trust-mcp")
    frontend_dir = os.path.join(agent_dir, "frontend")
    next_bin = os.path.join(frontend_dir, "node_modules", "next", "dist", "bin", "next")

    print("==================================================")
    print("  TRUSTMATE System Launcher (Full Stack)")
    print("==================================================")

    # 1. Start TRUSTMATE MCP Server
    if os.path.exists(trust_mcp_dir):
        print("[1/3] Starting Person A's TRUSTMATE MCP Server on http://127.0.0.1:8001...")
        p_mcp = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001"], cwd=trust_mcp_dir)
    else:
        print("[1/3] Starting Mock TRUSTMATE MCP Server on http://127.0.0.1:8001...")
        mock_script = os.path.join(agent_dir, "mock", "mock_mcp_server.py")
        p_mcp = subprocess.Popen([sys.executable, mock_script], cwd=agent_dir)

    time.sleep(2.0)

    # 2. Start FastAPI Backend API
    print("[2/3] Starting FastAPI Agent Backend on http://127.0.0.1:8000...")
    main_script = os.path.join(agent_dir, "main.py")
    p_backend = subprocess.Popen([sys.executable, main_script], cwd=agent_dir)

    time.sleep(2.0)

    # 3. Start Next.js Frontend
    print("[3/3] Starting Next.js Frontend on http://127.0.0.1:3000...")
    if os.path.exists(next_bin):
        p_frontend = subprocess.Popen(["node", next_bin, "dev", "-p", "3000"], cwd=frontend_dir)
    else:
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        p_frontend = subprocess.Popen([npm_cmd, "run", "dev"], cwd=frontend_dir)

    print("==================================================")
    print("  🚀 ALL SERVICES RUNNING SUCCESSFULLY!")
    print("  👉 Next.js UI:            http://127.0.0.1:3000")
    print("  👉 FastAPI Agent Backend: http://127.0.0.1:8000")
    print("  👉 TRUSTMATE MCP Server:  http://127.0.0.1:8001")
    print("==================================================")

    try:
        p_frontend.wait()
    except KeyboardInterrupt:
        print("\nStopping all services...")
        p_mcp.terminate()
        p_backend.terminate()
        p_frontend.terminate()

if __name__ == "__main__":
    main()
