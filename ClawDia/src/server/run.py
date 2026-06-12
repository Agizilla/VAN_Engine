"""Run the ClawDia Dashboard server.

Usage:
    python ClawDia/src/server/run.py
"""
import uvicorn


def main():
    uvicorn.run("src.server.app:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
