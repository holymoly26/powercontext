-- SDD 上下文模块：工程资料存储表
-- 用法：mysql -h127.0.0.1 -P2881 -uroot < schema.sql

CREATE DATABASE IF NOT EXISTS sdd DEFAULT CHARACTER SET utf8mb4;
USE sdd;

CREATE TABLE IF NOT EXISTS context_docs (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    path     VARCHAR(255) NOT NULL,          -- 来源文件路径，如 biz/todo.py
    symbol   VARCHAR(255) NOT NULL DEFAULT '', -- 符号名，如 function:list_items
    kind     VARCHAR(16)  NOT NULL,          -- spec / code / test
    title    VARCHAR(255) NOT NULL DEFAULT '',
    content  TEXT         NOT NULL,
    lineno   INT          NOT NULL DEFAULT 0,
    version  INT          NOT NULL DEFAULT 1,
    UNIQUE KEY uk_doc (path, symbol),
    KEY idx_kind (kind)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
