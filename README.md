# CAT Menus

CAT 메뉴 제작용 Blender Extension입니다. 기존 단일 파일 애드온을 기능별 모듈 구조로 분리했고, GitHub Releases와 GitHub Pages 기반 원격 저장소로 배포할 수 있게 구성했습니다.

## 구조

```text
__init__.py              Extension 등록 진입점
menu.py                  3D View CAT 메뉴
utils.py                 공통 Blender 데이터 헬퍼
operators/               기능별 operator 모듈
scripts/                 개발 실행기와 릴리스 빌드 스크립트
tests/                   Blender smoke test
```

## 사용자 설치

릴리스와 Pages 배포가 완료되면 Blender에서 다음 원격 저장소 URL을 등록합니다.

```text
https://zzamjak-cloud.github.io/CatMenus-Blender/index.json
```

Blender의 **Get Extensions > Repositories > Add Remote Repository**에서 위 URL을 추가한 뒤 `CAT Menus`를 설치합니다. 시작 시 업데이트 확인을 원하면 저장소 옵션에서 **Check for Updates on Startup**을 켭니다. 이 설정은 새 버전을 자동 확인하고 알리는 기능이며, 설치에는 사용자 승인이 필요합니다.

## macOS 개발 실행

```bash
scripts/dev_run.sh
scripts/dev_run.sh --background --python tests/smoke_test.py
```

기본 Blender 실행 파일은 `/Applications/Blender.app/Contents/MacOS/Blender`입니다. 다른 Blender를 쓰려면 `BLENDER_BINARY`를 지정합니다.

```bash
BLENDER_BINARY="/Applications/Blender.app/Contents/MacOS/Blender" scripts/dev_run.sh
```

개발 프로필은 `~/Library/Application Support/Blender/CatMenusBlenderDev/<BlenderVersion>` 아래에 만들어지며, 이 저장소가 `extensions/user_default/cat_menus`로 연결됩니다. 일반 Blender 프로필에는 개발 링크를 만들지 않습니다.

## Windows 개발 실행

```powershell
scripts\dev_run.ps1
scripts\dev_run.ps1 --background --python tests\smoke_test.py
```

명령 프롬프트에서는 래퍼를 사용할 수 있습니다.

```bat
scripts\dev_run.bat --background --python tests\smoke_test.py
```

기본 실행 파일은 `%ProgramFiles%\Blender Foundation\Blender 5.2\blender.exe`입니다. 다른 경로를 쓰려면 `BLENDER_BINARY` 환경 변수를 지정합니다. 개발 링크는 프로젝트 전용 프로필 아래에 Junction으로 생성됩니다.

## 로컬 빌드

```bash
python3 scripts/build_release.py
```

스크립트는 소스 검증, ZIP 빌드, ZIP 검증, `remote_repo/index.json` 생성을 순서대로 수행합니다. 생성물은 `dist/cat_menus-v0.1.1.zip`입니다.

## GitHub 배포

이 저장소를 `zzamjak-cloud/CatMenus-Blender` 공개 저장소로 push한 뒤 새 버전 태그를 만들면 GitHub Actions가 ZIP을 빌드하고 Release에 첨부합니다.

```bash
git tag v0.1.1
git push origin main --tags
```

Release 워크플로가 완료되면 Pages 워크플로가 릴리스 ZIP들로 Extension 원격 저장소의 `index.json`을 생성해 배포합니다.
