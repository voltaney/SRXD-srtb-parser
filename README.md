# インストール方法
```
pip install git+https://github.com/voltaney/SRXD-srtb-parser.git
```
タグ指定の場合は下記。
```
pip install git+https://github.com/voltaney/SRXD-srtb-parser.git@{tag}
```

# 開発環境
- Linter / Formatter: Ruff
- Type check: Mypy
- Unit test: pytest
- Task runner: taskipy

### 依存パッケージインストール
```bash
poetry install
```
### pre-commitでpre-commitフックをローカルに作成
```bash
pre-commit install
```
### VSCode拡張のインストール
- Mypy Type Checker
- Ruff
- autoDocstring
VSCode設定はすべて`.vscode/settings.json`で管理。