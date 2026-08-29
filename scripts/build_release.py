import hashlib
import pathlib
import shutil
import subprocess
import sys
import tomllib


ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
REMOTE_REPO = ROOT / "remote_repo"
BLENDER = pathlib.Path("/Applications/Blender.app/Contents/MacOS/Blender")


def run(args):
    print("+", " ".join(str(arg) for arg in args))
    subprocess.run(args, cwd=ROOT, check=True)


def main():
    manifest = tomllib.loads((ROOT / "blender_manifest.toml").read_text(encoding="utf-8"))
    addon_id = manifest["id"]
    version = manifest["version"]
    zip_path = DIST / f"{addon_id}-v{version}.zip"

    blender_binary = pathlib.Path(shutil.which("blender") or BLENDER)
    if not blender_binary.exists():
        raise SystemExit(f"Blender 실행 파일을 찾을 수 없습니다: {blender_binary}")

    DIST.mkdir(exist_ok=True)
    REMOTE_REPO.mkdir(exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()

    common = [str(blender_binary), "--background", "--factory-startup", "--command", "extension"]
    run([*common, "validate", str(ROOT)])
    run([*common, "build", "--source-dir", str(ROOT), "--output-filepath", str(zip_path)])
    run([*common, "validate", str(zip_path)])

    repo_zip = REMOTE_REPO / zip_path.name
    shutil.copy2(zip_path, repo_zip)
    run([*common, "server-generate", "--repo-dir", str(REMOTE_REPO), "--html"])

    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    print(f"빌드 완료: {zip_path}")
    print(f"SHA256: {digest}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
