-- 開発用データベース初期化スクリプト

-- テスト用データベースも作成
CREATE DATABASE fastapi_test_db;

-- 開発用ユーザーに権限付与（既にpostgresユーザーが存在するため不要だが、参考として記載）
-- CREATE USER fastapi_dev_user WITH PASSWORD 'fastapi_dev_pass';
-- GRANT ALL PRIVILEGES ON DATABASE fastapi_dev_db TO fastapi_dev_user;
-- GRANT ALL PRIVILEGES ON DATABASE fastapi_test_db TO fastapi_dev_user;

-- 拡張機能を有効化（必要に応じて）
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";