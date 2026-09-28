# Conversational AI

这是一个基于 FastAPI 和 LangChain 的对话与 RAG 学习项目。代码展示了从用户认证、会话历史，到意图判断、混合检索、重排序和 SSE 流式回答的完整请求链路。项目仍处于学习阶段，运行依赖本地模型、知识库和外部服务。

## 已实现的能力

- 邮箱验证码注册、邮箱密码或验证码登录，以及 JWT + Redis 登录状态。
- 普通对话与知识库问答；聊天接口通过 SSE 返回消息，并保存问答记录。
- 使用本地 Ollama 模型结合会话历史判断意图，并在需要时生成独立检索问题。
- 对知识库问题使用 Chroma 向量检索、中文 BM25、RRF 融合和 reranker 重排序。
- 查询会话列表与详情、修改标题和删除会话。
- 使用示例制度文档进行离线解析与切块；知识库写入脚本与在线问答分开。

聊天请求的主要流程：

```text
Bearer 身份验证
  -> 读取近期历史与会话记忆
  -> 分析上下文和意图
  -> 普通对话，或 Chroma + BM25 -> RRF -> reranker
  -> 拼接 Prompt -> 大模型生成
  -> SSE 返回 -> 保存本轮问答
```

## 代码结构

| 目录 | 职责 |
| --- | --- |
| `main.py` | FastAPI 应用入口与路由注册 |
| `ai/` | 加载并复用聊天、意图、Embedding、Chroma、BM25 索引和重排序模型 |
| `chat/controller/` | 聊天与历史会话接口 |
| `chat/service/` | 上下文分析、检索、Prompt、回答和会话流程 |
| `chat/dao/` | 会话及消息数据访问 |
| `users/` | 注册、登录、认证与用户数据访问 |
| `common/` | 配置、MySQL、Redis、JWT、密码和邮件工具 |
| `create/` | 示例资料与离线知识库构建脚本 |
| `tests/` | 单元测试与部分依赖外部服务的验证脚本 |

## 运行前准备

1. 准备 Python 3.11 或更新版本，并安装项目依赖。代码使用 FastAPI、Pydantic Settings、LangChain 相关包、FlagEmbedding、jieba、rank-bm25、PyMySQL、Redis 客户端等。当前提交**没有依赖锁文件或已提交的 `requirements.txt`**，因此尚不能从全新环境一键安装。
2. 准备 MySQL、Redis、SMTP 服务，以及提供意图识别模型的 Ollama 和 OpenAI 兼容的回答模型接口。注册流程需要邮件验证码；仅调用健康检查不需要完成这些服务的业务验证。
3. 准备与现有 collection 兼容的 Chroma 数据，以及本地 Embedding 和 reranker 模型。Chroma 运行数据和模型文件不包含在 Git 仓库中。Embedding 的查询前缀与向量维度必须与存量数据一致。
4. 在项目目录复制 `.env.example` 为 `.env`，将其中的占位项和示例路径改为自己的配置。`RERANKER_MODEL_PATH` 是启动时必填项；还要将 `EMBEDDING_MODEL` 和 `EMBEDDING_DEVICE` 改为本机可用的模型路径与设备，并核对 `CHROMA_PATH`、`COLLECTION_NAME`、模型服务、MySQL、Redis、SMTP 和 `JWT_SECRET_KEY`。`.env` 含凭据，不要提交到 Git。
5. 准备业务所需的 MySQL 表结构。当前提交**没有建表脚本或数据库迁移**，仅克隆代码无法完成注册和会话保存。

在 `fastApiProject` 目录启动应用：

```powershell
python main.py
```

配置正确且依赖已安装时，可访问 `http://127.0.0.1:8000/docs` 查看接口文档。健康检查示例：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/live
```

预期响应包含 `status: ok`。健康检查只验证应用响应，不代表数据库、模型和知识库均可用。

## 主要接口

| 方法与路径 | 说明 |
| --- | --- |
| `GET /health/live` | 应用健康检查 |
| `POST /users/email-codes` | 发送注册或登录验证码 |
| `POST /users/register` | 使用邮箱验证码注册 |
| `POST /users/login` | 邮箱密码登录 |
| `POST /users/login/email-code` | 邮箱验证码登录 |
| `GET /users/me`、`POST /users/logout` | 获取当前用户、退出登录 |
| `GET /chat/chat` | 带 Bearer Token 的 SSE 聊天；`question` 必填，`conversation_id` 可选 |
| `GET /chat/history/conversations` | 列出当前用户的会话 |
| `GET /chat/history/conversations/{conversation_id}` | 查看会话详情 |
| `PATCH /chat/history/conversations/{conversation_id}` | 修改会话标题 |
| `DELETE /chat/history/conversations/{conversation_id}` | 删除会话 |

聊天 SSE 事件包含 `message`、`done` 和 `error`；`done` 事件会返回保存后的 `conversation_id`。认证与请求字段的完整格式以 `/docs` 中的接口定义为准。

## 示例资料与测试

`create/data/` 收录了用于学习的示例制度文档。`create/ingest.py` 提供只解析与切块的 `--dry-run`，也提供会替换同批 Chroma 数据的 `--write`。使用现有知识库时，请先核对数据和脚本行为，不要把写入命令作为启动步骤。

`tests/` 包含核心逻辑测试和部分集成验证。运行测试前需检查对应文件依赖的数据库、Redis、模型或知识库；本 README 不将健康检查等同于完整问答链路验证。

## 当前限制

- 仓库未包含 Chroma 运行数据、本地模型、真实 `.env`、依赖锁文件和 MySQL 建表脚本。
- 模型调用和邮件发送依赖用户自己的服务配置，可能产生外部费用。
- 这是学习项目；部署、安全和完整环境复现仍需单独完善。
