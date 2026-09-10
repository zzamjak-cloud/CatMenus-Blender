# 변경 이력

## 0.3.0

- Collision maker가 원본 오브젝트의 pivot(원점)을 그대로 따라가도록 바꿨습니다. 생성된 Collision Cube의 원점은 원본 pivot과 같은 위치에 놓이고, 박스 형상은 원본의 실제 바운딩 박스를 감싸도록 배치됩니다. pivot이 형상 중심에서 벗어난 오브젝트에서도 Collision이 어긋나지 않습니다.
- Collision Cube 크기를 `dimensions` 대신 월드 공간 바운딩 박스에서 계산합니다. 회전·부모 변환이 걸린 오브젝트도 실제 차지하는 범위에 맞게 생성됩니다.
- Picking maker(`object.picking`)와 `Cat > Picking maker` 메뉴를 제거했습니다. 더 이상 사용하지 않는 기능입니다.
- Clean Setting의 제외 조건에서 `Picking` 이름 검사를 함께 제거했습니다.

## 0.2.0

- 프리셋 대화창의 옵션을 Blender 내보내기 연산자에서 그대로 복제하도록 바꿨습니다. 항목·영문 라벨·설명·기본값·범위가 Blender 기본 FBX/OBJ 내보내기 설정과 같고, `Include / Transform / Geometry / Armature / Animation` 패널 구성도 동일합니다.
- FBX 애니메이션 옵션(`Baked Animation`, `Key All Bones`, `NLA Strips`, `All Actions`, `Force Start/End Keying`, `Sampling Rate`, `Simplify`)을 프리셋에 추가했습니다. 그 밖에 빠져 있던 `Loose Edges`, `Tangent Space`, `Vertex Colors`, `Export Subdivision Surface`, `Use Space Transform`, `Apply Transform`, 아마추어 옵션 전체, `Embed Textures`도 포함됩니다.
- `Export Mode`(CAT 전용) 항목을 추가했습니다. `Per Object`는 기존처럼 오브젝트마다 파일을 만들고, `Single File`은 선택 전체를 액티브 오브젝트 이름의 파일 하나로 내보냅니다. 아마추어와 스킨 메시를 한 파일에 담아야 하는 애니메이션 내보내기에 사용합니다.
- Export OBJ에도 같은 프리셋 기능을 적용했습니다. `Cat > Export OBJ`가 하위 메뉴가 되고, 프리셋 등록·실행·삭제가 FBX와 동일하게 동작합니다.
- 하위 메뉴의 `+프리셋` 항목 이름을 `프리셋`으로 바꿨습니다.
- 프리셋 저장 파일을 `cat_menus/export_presets.json`으로 통합했습니다. 기존 `cat_menus/fbx_presets.json`의 FBX 프리셋은 처음 읽을 때 자동으로 옮겨집니다.
- 이 Blender 버전에 없는 옵션이 저장된 프리셋은 해당 항목만 기본값으로 처리하고 나머지는 그대로 유지합니다.

## 0.1.4

- 내보내기 폴더 아래에 `FBX` 하위 폴더를 자동으로 만드는 동작을 제거했습니다. 프리셋에 지정한 폴더에 FBX가 바로 저장됩니다.
- `+프리셋` 대화창의 `폴더 이름` 항목을 삭제했습니다. 저장 위치는 `내보내기 폴더` 하나로 결정됩니다.
- 내보내기 폴더를 비운 프리셋은 하위 폴더 없이 블렌드 파일이 있는 폴더에 바로 내보냅니다.
- 0.1.3 이전 프리셋에 남아 있는 `export_subdir` 값은 읽을 때 무시됩니다.

## 0.1.3

- Export FBX를 하위 메뉴로 바꾸고 로컬에 저장된 FBX 내보내기 프리셋 목록을 표시합니다.
- `+프리셋`으로 새 프리셋(내보내기 폴더, 오브젝트 타입, 스무딩, 스케일, 축, 텍스처 경로 등)을 등록할 수 있습니다.
- 프리셋에 내보내기 폴더를 지정해 두면 블렌드 파일 위치와 무관하게 그 폴더로 곧바로 내보냅니다. 비워 두면 블렌드 파일 옆의 폴더 이름(기본 `FBX`)을 사용합니다.
- 프리셋은 Blender 사용자 설정 디렉터리의 `cat_menus/fbx_presets.json`에 저장되어 블렌드 파일과 무관하게 유지됩니다.
- 프리셋 항목의 X 버튼으로 등록된 프리셋을 삭제할 수 있습니다.
- Export FBX 실행 시 블렌드 파일 저장 여부와 선택 오브젝트 유무를 검사하고, 실행 전 선택 상태를 복원합니다.

## 0.1.2

- Match Name 실행 시 링크된(에셋 라이브러리) 데이터에서 `name is read-only` 오류로 중단되던 문제를 수정했습니다.
- 이름 변경 대상을 오브젝트가 참조하는 데이터로 한정하고, 선택된 오브젝트가 있으면 선택분만 처리합니다.
- 라이브러리 오버라이드 데이터도 정상적으로 이름이 변경되도록 `is_editable` 기준으로 판정합니다.
- 임시 이름 충돌 가능성을 제거하고, 건너뛴 데이터 개수를 리포트합니다.

## 0.1.1

- 기존 단일 파일 애드온을 기능별 모듈 구조의 Blender Extension으로 이전했습니다.
- GitHub Release ZIP 빌드와 GitHub Pages 원격 저장소 생성을 위한 스크립트와 워크플로를 추가했습니다.
- macOS와 Windows 격리 개발 프로필 실행기를 추가했습니다.
