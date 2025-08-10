# デプロイメントガイド

## データベース接続設定

### 開発環境：Docker PostgreSQL
- **ホスト**: `localhost`
- **ポート**: `5432`
- **データベース**: `fastapi_dev_db`
- **ユーザー名**: `postgres`
- **パスワード**: `postgres`

### 本番環境：Render PostgreSQL

### データベース情報
- **ホスト名**: `dpg-d2c4tlur433s73ab3ubg-a.singapore-postgres.render.com`
- **ポート**: `5432`
- **データベース**: `langchain_fastapi_db`
- **ユーザー名**: `langchain_fastapi_db_user`
- **パスワード**: `vnsWJDgdgpMPwbSW0is6yE1UUyYOIoj8`

## クイックスタート

### 🚀 初回セットアップ
```bash
# 自動セットアップスクリプト実行
./scripts/dev-setup.sh
```

または手動でセットアップ：

```bash
# 1. 依存関係インストール
make install

# 2. PostgreSQL起動
make docker-up

# 3. データベーステーブル作成
make migrate-dev

# 4. 開発サーバー起動
make dev
```

### 環境設定

#### 開発環境 (.env.dev)
- **データベース**: ローカルDocker PostgreSQL
- **設定**: デバッグ有効、詳細ログ、高速パスワードハッシュ

```bash
# 開発環境で起動
make dev
```

#### 本番環境 (.env)
- **データベース**: Render PostgreSQL
- **設定**: セキュリティ強化、JSONログ、本番用ハッシュ

```bash
# 本番環境で起動
make dev-prod
```

## データベースマイグレーション

### 初回セットアップ
```bash
# 開発環境のテーブル作成
make migrate-dev

# 本番環境のテーブル作成
make migrate-prod
```

### 手動接続確認
```bash
# PSQLコマンドでデータベースに直接接続
PGPASSWORD=vnsWJDgdgpMPwbSW0is6yE1UUyYOIoj8 psql -h dpg-d2c4tlur433s73ab3ubg-a.singapore-postgres.render.com -U langchain_fastapi_db_user langchain_fastapi_db
```

## 環境別設定ファイル

### .env.dev (開発環境)
- デバッグモード有効
- 詳細ログ出力
- CORS設定緩和
- アクセストークン有効期限延長

### .env (本番環境)
- デバッグモード無効
- JSON形式ログ
- セキュリティ強化
- 短いトークン有効期限

## Renderデプロイ設定

### render.yaml設定例
```yaml
services:
  - type: web
    name: fastapi-enterprise-app
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DATABASE_URL
        value: postgresql+asyncpg://langchain_fastapi_db_user:vnsWJDgdgpMPwbSW0is6yE1UUyYOIoj8@dpg-d2c4tlur433s73ab3ubg-a.singapore-postgres.render.com/langchain_fastapi_db
      - key: SECRET_KEY
        generateValue: true
```

## 使用方法

### 1. 依存関係インストール
```bash
make install
```

### 2. 環境設定
```bash
# 開発環境用
cp .env.dev .env.local
# または本番環境用
cp .env .env.local
```

### 3. データベーステーブル作成
```bash
# 開発環境
make migrate-dev

# 本番環境  
make migrate-prod
```

### 4. サーバー起動
```bash
# 開発環境
make dev

# 本番環境
make dev-prod
```

### 5. API確認
- ヘルスチェック: `http://localhost:8000/api/v1/health`
- APIドキュメント: `http://localhost:8000/api/v1/docs`
- ルート: `http://localhost:8000/`

## セキュリティ注意事項

### 本番環境では必ず変更すること
1. **SECRET_KEY**: ランダムな32文字以上の文字列
2. **CORS_ORIGINS**: 実際のフロントエンドドメイン
3. **LOG_LEVEL**: INFO以上に設定
4. **ACCESS_TOKEN_EXPIRE_MINUTES**: セキュリティ要件に応じて調整

### 推奨設定
- Renderの環境変数でSECRET_KEYを管理
- データベースパスワードの定期的な変更
- アクセスログの監視設定