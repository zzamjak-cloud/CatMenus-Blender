# CAT Menus

CAT 메뉴 제작용 Blender Extension입니다. 기존 단일 파일 애드온을 기능별 모듈 구조로 분리했고, GitHub Releases와 GitHub Pages 기반 원격 저장소로 배포할 수 있게 구성했습니다.

## 구조

```text
__init__.py              Extension 등록 진입점
menu.py                  3D View CAT 메뉴
utils.py                 공통 Blender 데이터 헬퍼
export_presets.py        FBX/OBJ 내보내기 프리셋 저장소와 Blender 옵션 복제
operators/               기능별 operator 모듈
scripts/                 개발 실행기와 릴리스 빌드 스크립트
tests/                   Blender smoke test
```

## Export FBX / Export OBJ 프리셋

`Cat > Export FBX`와 `Cat > Export OBJ` 하위 메뉴에는 로컬에 저장된 내보내기 프리셋이 나열됩니다. 프리셋을 고르면 선택한 오브젝트가 곧바로 저장됩니다. 프리셋을 고르지 않고 실행할 수 있는 기본 항목은 없습니다.

### 프리셋 설정 항목

`프리셋`을 누르면 뜨는 대화창의 내보내기 옵션은 실행 중인 Blender의 `File > Export > FBX / Wavefront (.obj)` 설정에서 그대로 복제한 것입니다. 항목 구성, 영문 라벨, 설명, 기본값, 값 범위, 패널 묶음이 모두 같으므로 Blender 기본 내보내기 창과 같은 감각으로 설정하면 됩니다. Blender 버전이 올라가 옵션이 바뀌어도 대화창이 자동으로 따라갑니다.

FBX는 `Include / Transform / Geometry / Armature / Animation`, OBJ는 `Transform / Geometry / Materials / Grouping / Animation` 패널로 나뉩니다. `Animation` 패널의 체크박스(FBX `Baked Animation`, OBJ `Export Animation`)를 켜면 애니메이션 관련 옵션이 활성화됩니다.

여기에 CAT 전용 항목 세 가지가 앞쪽에 추가됩니다.

- **Preset Name**: 하위 메뉴에 표시할 이름. 같은 이름으로 저장하면 기존 프리셋을 덮어씁니다.
- **Export Folder**: 저장 위치. 아래 규칙을 따릅니다.
- **Export Mode**: 선택한 오브젝트를 파일로 나누는 방식.
  - `Per Object` — 오브젝트마다 오브젝트 이름의 파일을 하나씩 만듭니다.
  - `Single File` — 선택 전체를 액티브 오브젝트 이름의 파일 하나로 내보냅니다. 아마추어와 스킨 메시가 한 파일에 있어야 하는 애니메이션 내보내기에 사용합니다.

### 저장 위치

저장 위치는 **Export Folder** 설정 하나로 결정되며, 하위 폴더를 따로 만들지 않습니다.

- 폴더를 지정한 프리셋: 블렌드 파일 위치와 무관하게 그 폴더에 바로 저장합니다. 폴더가 없으면 만듭니다.
- 폴더를 비운 프리셋: 블렌드 파일이 있는 폴더에 바로 저장합니다. 이때는 블렌드 파일을 먼저 저장해야 합니다.
- `//assets/fbx`처럼 `//`로 시작하는 블렌드 파일 기준 상대 경로도 쓸 수 있습니다.

프리셋 항목 오른쪽의 X 버튼으로 삭제합니다.

### 프리셋 파일

프리셋은 Blender 사용자 설정 디렉터리에 저장되므로 블렌드 파일이나 애드온 재설치와 무관하게 유지됩니다. FBX와 OBJ 프리셋이 한 파일에 함께 들어갑니다.

```text
Windows  %APPDATA%\Blender Foundation\Blender\<버전>\config\cat_menus\export_presets.json
macOS    ~/Library/Application Support/Blender/<버전>/config/cat_menus/export_presets.json
```

0.1.4 이전에 만든 `cat_menus/fbx_presets.json`의 FBX 프리셋은 처음 읽을 때 자동으로 옮겨집니다.

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

기본 실행 파일은 `%ProgramFiles%\Blender Foundation\Blender 5.2\blender.exe`입니다. 다른 경로를 쓰려면 `BLENDER_BINARY` 환경 변수를 지정합니다.

개발 프로필은 `%LOCALAPPDATA%\Blender Foundation\Blender\CatMenusBlenderDev\<BlenderVersion>` 아래에 만들어지며, 이 저장소가 `extensions\user_default\cat_menus` Junction으로 연결됩니다. 프로필을 저장소 안에 두면 Extension 링크가 자기 자신을 가리켜 릴리스 빌드가 실패하므로 기본 위치는 저장소 밖입니다. 다른 위치를 쓰려면 `CATMENUS_BLENDER_PROFILE`을 지정합니다.

## 로컬 빌드

```bash
python3 scripts/build_release.py
```

Blender 실행 파일은 `PATH`의 `blender`, `BLENDER_BINARY` 환경 변수, macOS 기본 경로 순으로 찾습니다. Windows에서는 `BLENDER_BINARY`를 지정합니다.

```powershell
$env:BLENDER_BINARY = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"; python scripts/build_release.py
```

스크립트는 소스 검증, ZIP 빌드, ZIP 검증, `remote_repo/index.json` 생성을 순서대로 수행합니다. 생성물은 `dist/cat_menus-v0.2.0.zip`입니다.

## GitHub 배포

이 저장소를 `zzamjak-cloud/CatMenus-Blender` 공개 저장소로 push한 뒤 새 버전 태그를 만들면 GitHub Actions가 ZIP을 빌드하고 Release에 첨부합니다.

```bash
git tag v0.2.0
git push origin main --tags
```

Release 워크플로가 완료되면 Pages 워크플로가 릴리스 ZIP들로 Extension 원격 저장소의 `index.json`을 생성해 배포합니다.
