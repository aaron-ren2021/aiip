-- 初始化資料庫腳本
-- RPA自動專利比對機器人系統

-- 建立擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 任務狀態枚舉類型
CREATE TYPE task_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');

-- 專利資料庫枚舉類型
CREATE TYPE patent_database AS ENUM ('twpat', 'uspto', 'epo', 'wipo', 'jpo', 'cnipa', 'kipo');

-- 任務表
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    request_data JSONB NOT NULL,
    status task_status DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    result_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 專利資訊表
CREATE TABLE IF NOT EXISTS patents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patent_id VARCHAR(255) UNIQUE NOT NULL,
    patent_number VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    inventors TEXT[],
    applicants TEXT[],
    application_date DATE,
    publication_date DATE,
    grant_date DATE,
    ipc_classes TEXT[],
    claims TEXT,
    description TEXT,
    images TEXT[],
    source_database patent_database NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 檢索結果表
CREATE TABLE IF NOT EXISTS search_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) NOT NULL REFERENCES tasks(task_id),
    patent_id UUID NOT NULL REFERENCES patents(id),
    relevance_score NUMERIC(3,2),
    similarity_score NUMERIC(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 分析結果表
CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) NOT NULL REFERENCES tasks(task_id),
    analysis_type VARCHAR(50) NOT NULL,
    result_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_patents_number ON patents(patent_number);
CREATE INDEX IF NOT EXISTS idx_patents_source_db ON patents(source_database);
CREATE INDEX IF NOT EXISTS idx_search_results_task_id ON search_results(task_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_task_id ON analysis_results(task_id);

-- 更新時間戳觸發器函數
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 建立觸發器
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_patents_updated_at BEFORE UPDATE ON patents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入一些測試資料
INSERT INTO tasks (task_id, user_id, request_data, status) VALUES
('test-task-1', 'test-user', '{"keywords": ["人工智慧"], "databases": ["twpat"]}', 'completed'),
('test-task-2', 'test-user', '{"patent_number": "US1234567", "databases": ["uspto"]}', 'pending');

-- 授權
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO patent_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO patent_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO patent_user;