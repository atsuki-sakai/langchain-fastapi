# FastAPI Enterprise Application

実務レベルで堅牢かつ拡張性の高いFastAPIサーバーです。クリーンアーキテクチャとモダンなPythonベストプラクティスに基づいて構築されています。

## 🏗️ アーキテクチャ

- **クリーンアーキテクチャ**: 階層分離による高い保守性
- **依存性注入**: 疎結合な設計でテスタビリティ向上
- **型安全**: PydanticとTypeHintsによる型安全性
- **非同期処理**: asyncio/awaitによる高パフォーマンス

## 🚀 クイックスタート

### 前提条件
- Python 3.9+
- Docker & Docker Compose
- make

### セットアップ
```bash
# 自動セットアップ（推奨）
./scripts/dev-setup.sh

# 手動セットアップ
make install          # 依存関係インストール
make docker-up        # PostgreSQL起動
make migrate-dev      # DBテーブル作成
make dev             # 開発サーバー起動
```

### アクセス先
- **API**: http://localhost:8000
- **ドキュメント**: http://localhost:8000/api/v1/docs
- **ヘルスチェック**: http://localhost:8000/api/v1/health
- **pgAdmin**: http://localhost:5050 (admin@fastapi.com / admin123)

## 📁 プロジェクト構造

```
app/
├── core/           # 設定、セキュリティ、例外
├── models/         # Pydanticモデル（DTOs）
├── schemas/        # SQLAlchemyスキーマ
├── services/       # ビジネスロジック
├── repositories/   # データアクセス層
├── api/           # APIエンドポイント
├── middleware/    # ミドルウェア
├── utils/         # ユーティリティ
└── tests/         # テスト
```

## 🔑 主要機能

### 認証・認可
- JWT認証システム
- パスワードハッシュ化（bcrypt）
- ロールベースアクセス制御
- トークンリフレッシュ機能

### データベース
- 非同期PostgreSQL（SQLAlchemy + asyncpg）
- 開発環境：Docker PostgreSQL
- 本番環境：Render PostgreSQL
- マイグレーション対応

### API設計
- RESTful API
- OpenAPI自動ドキュメンテーション
- バージョニング対応
- 統一されたレスポンス形式
- ページネーション

### 品質保証
- 包括的テスト（pytest）
- 構造化ログ（structlog）
- エラーハンドリング
- 型チェック
- コードフォーマット（black, isort）
- リント（flake8）

## 🛠️ 開発コマンド

```bash
# 環境構築
make install         # 依存関係インストール
make docker-up      # PostgreSQL起動
make docker-down    # PostgreSQL停止

# 実行
make dev            # 開発サーバー起動（ローカルDB）
make dev-prod       # 本番設定で起動（リモートDB）

# データベース
make migrate-dev    # 開発環境マイグレーション
make migrate-prod   # 本番環境マイグレーション

# テスト
make test           # 全テスト実行
make test-unit      # 単体テスト
make test-integration # 統合テスト

# コード品質
make format         # フォーマット
make lint           # リント
make check          # フォーマット+リント+テスト

# その他
make help           # 全コマンド表示
make clean          # クリーンアップ
```

## 🗄️ データベース設定

### 開発環境
- **Docker PostgreSQL** (localhost:5432)
- 自動起動・初期化
- テスト用データベースも自動作成

### 本番環境
- **Render PostgreSQL**
- 環境変数で接続設定
- SSL接続対応

## 🔧 環境設定

### 開発環境 (.env.dev)
- デバッグ有効
- 詳細ログ出力
- 高速パスワードハッシュ
- 長いトークン有効期限

### 本番環境 (.env)
- セキュリティ強化
- JSON構造化ログ
- 本番用ハッシュ強度
- 短いトークン有効期限

## ⚠️ 既知の注意点・トラブルシューティング

- Pydantic v2 互換性: `app/core/config.py` では `BaseSettings` は `pydantic_settings` からインポートしてください。
  - 例: `from pydantic_settings import BaseSettings`
  - ImportError が出る場合: `pip install pydantic-settings`
- 依存関係: `requirements.txt` に `python-cors` がある場合は削除してください。CORS は FastAPI の `CORSMiddleware` で対応します。

### 環境ファイルの切替
- `ENVIRONMENT` 変数で読み込む `.env` を切り替えます。
  - `ENVIRONMENT=development` のとき `.env.dev`
  - `ENVIRONMENT=production` のとき `.env`
- 例: `ENVIRONMENT=development make dev`

## 📊 監視・ログ

- **構造化ログ**: JSON形式での出力
- **リクエストID**: 全ログにリクエストID付与
- **ヘルスチェック**: Kubernetes対応
- **メトリクス**: 将来的にPrometheus対応予定

## 🚢 デプロイ

### Render.com
- `render.yaml`で自動デプロイ設定
- 環境変数管理
- PostgreSQL連携

詳細は [DEPLOYMENT.md](DEPLOYMENT.md) を参照

## 🧪 テスト

```bash
# 全テスト
make test

# カテゴリ別
make test-unit          # 単体テスト
make test-integration   # 統合テスト

# 特定のテスト
pytest app/tests/unit/test_auth.py -v
```

## 🤝 開発ガイドライン

### コーディング規約
- PEP 8準拠
- Type Hintsの使用
- Docstringの記述
- テストファーストな開発

### コミット前チェック
```bash
make check  # フォーマット・リント・テストを実行
```

## 📚 参考資料

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)