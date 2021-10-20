# UCE-KAIST-Public
Undergraduate Course Explorer for KAIST
Website link: graduate-kaist.herokuapp.com

## 하나뿐인 KAIST 학부 졸업 길라잡이, 매화수
매화수는 학부 졸업 사정을 관리하고, 수강 계획을 설계하는데 도움을 주는 프로그램입니다.
앞으로 카이스트 학생이라면 누구나 참여할 수 있는 오픈소스 프로젝트로 확대할 계획입니다.

### 매화수의 시작은 엑셀
매화수는 본래 졸업 요건 확인을 돕는 엑셀 파일이었습니다. 엑셀은 사용자가 쉽게 함수를 수정하고 정보를 변경할 수 있다는 장점이 있지만, 업데이트 및 추가 기능 등을 제공하기 어렵다는 단점이 있었습니다. 초기에 배포했던 엑셀 파일은 여기에서 확인할 수 있습니다.

### 새롭게 만들어진 웹버전, 매화수
새롭게 웹사이트로 만들어진 매화수는 언제 어디서든 쉽고 간편하게 졸업 요건을 확인할 수 있도록 제작되었습니다. 나아가, 사용자의 익명 데이터들을 기반으로 AI 등을 활용해 스마트한 과목 추천 시스템을 구현할 예정입니다.

### 함께 만들어가는 프로젝트, 매화수
매화수에는 아직 많은 기능이 없습니다. 하지만, 여러분이 도와주신다면 다채로운 매화수를 함께 만들어갈 수 있을 것입니다. 베타 테스팅 기간이 끝난 이후에 매화수를 함께 개발할 분을 공개적으로 모집할 예정입니다.

### 파일 설명
매화수를 위한 코드 구성은 다음과 같습니다.
```
.
├── LICENSE
├── README.md
├── __init__.py
├── app
│   ├── __init__.py
│   ├── __pycache__
│   ├── forms.py
│   ├── models.py
│   ├── routes.py
│   ├── static
│   │   └── assets
│   │       ├── all_courses.csv
│   │       ├── css
│   │       ├── gulpfile.js
│   │       ├── img
│   │       ├── img-pixel
│   │       ├── js
│   │       ├── package.json
│   │       ├── scss
│   │       └── vendor
│   └── templates
│       ├── accounts
│       │   ├── login.html
│       │   ├── register.html
│       │   └── reset_password.html
│       ├── course_add.html
│       ├── course_analysis.html
│       ├── course_view.html
│       ├── includes
│       │   ├── footer.html
│       │   ├── navigation.html
│       │   ├── preloader.html
│       │   └── scripts.html
│       ├── index.html
│       ├── info.html
│       ├── layouts
│       │   ├── base-fullscreen.html
│       │   └── base.html
│       ├── page-404.html
│       ├── page-500.html
│       └── privacy.html
├── config.py
├── requirements.txt
└── run.py

```
매화수에 입력되는 정보에는 개인정보도 포함되어 있으므로, 개인정보 보호를 위해 해당 `git`에서는 config.py 파일이 빈 파일로 구성되어 있습니다.
