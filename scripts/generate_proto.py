"""Compile .proto files into Python gRPC stubs for all services."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROTO_DIR = ROOT / "proto"
TARGET_DIRS = [
    ROOT / "product_service" / "generated",
    ROOT / "user_service" / "generated",
]


def compile_for_dir(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    init_file = output_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Generated stubs\n", encoding="utf-8")

    proto_files = list(PROTO_DIR.glob("*.proto"))
    for proto_file in proto_files:
        cmd = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"-I{PROTO_DIR}",
            f"--python_out={output_dir}",
            f"--grpc_python_out={output_dir}",
            str(proto_file),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error compiling {proto_file.name}: {result.stderr}")
            sys.exit(1)

    # Fix relative imports in all *_pb2_grpc.py files
    for grpc_file in output_dir.glob("*_pb2_grpc.py"):
        stem = grpc_file.stem.replace("_grpc", "")
        content = grpc_file.read_text(encoding="utf-8")
        content = content.replace(f"import {stem}", f"from . import {stem}")
        grpc_file.write_text(content, encoding="utf-8")


def main():
    proto_files = list(PROTO_DIR.glob("*.proto"))
    if not proto_files:
        print("No .proto files found in", PROTO_DIR)
        sys.exit(1)

    for target in TARGET_DIRS:
        print(f"Compiling protos into {target.relative_to(ROOT)}...")
        compile_for_dir(target)

    print("[SUCCESS] Proto compilation complete for all services.")


if __name__ == "__main__":
    main()
