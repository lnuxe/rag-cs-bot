# rag-cs-bot — 基于 Dify RAG 的电商客服自动化 Demo

> 面向 TikTok Shop 店铺客服的「售前 AI 自动回复 + 售后转人工」全链路 Demo。
> 已跑通：本地 Dify + RAG 知识库 → 客服聊天前端 → 浏览器自动化（UI-TARS）读取消息 → 调 Dify API 自动回复。

---

## 项目背景

电商店铺客服每天 **99+ 条客户消息**，回复率受 TikTok **24h / 48h 考核**约束。本项目用 **本地私有化部署的 RAG 检索增强生成（Retrieval-Augmented Generation）** 实现客服自动化：

- **售前问题**（产品 / 发货 / 物流 / 价格 / 尺码 / 咨询）→ AI 基于知识库自动回复
- **售后问题**（退换 / 退款 / 投诉 / 赔偿）→ 转人工处理（不喂给 AI，避免乱承诺）

> 关键设计：**知识库只放售前内容**，售后内容不喂给 AI，从而强制售后转人工，规避 AI 在退款/赔偿上做出无法兑现的承诺。

---

## 仓库结构

```
rag-cs-bot/
├── README.md                 # 项目说明（本文件）
├── 售前AI客服搭建操作指南.md   # Dify 侧完整搭建步骤
├── cs_web/                   # 客服聊天前端 + 后端代理
│   ├── app.py                # Flask 后端：转发到 Dify API + 去 DeepSeek 思考
│   └── static/index.html     # 聊天界面
├── ui_tars_demo/             # UI-TARS 浏览器自动化 Demo
│   ├── tars_demo.py          # 读取浏览器消息框 → 调 Dify API → 回填回复
│   └── demo_msg.html         # 模拟消息框页面
└── dify/                     # Dify 开源平台源码（langgenius/dify，已去除运行时产物）
```

---

## 快速开始

### 1. 启动本地 Dify

```bash
cd dify/docker
docker compose up -d
# 访问 http://localhost:80，完成管理员初始化
```

### 2. 配置模型与知识库

见 `售前AI客服搭建操作指南.md`：
- 接入大模型（DeepSeek / 通义千问 / 智谱）
- 建「售前知识库」（高质量索引 + Embedding）
- 搭「售前AI / 售后人工」分流 Chatflow 工作流

### 3. 启动客服前端

```bash
cd cs_web
pip install -r requirements.txt   # flask, requests
python3 app.py
# 访问 http://localhost:8000
```

环境变量（可选）：
- `DIFY_BASE_URL`：Dify API 地址（默认 `http://localhost/v1`）
- `DIFY_API_KEY`：Dify Chatflow 应用 API Key

### 4. 浏览器自动化（UI-TARS）

```bash
cd ui_tars_demo
python3 tars_demo.py
```

读取浏览器消息框中的买家消息 → 调 Dify API 生成回答 → 回填到消息框，实现自动回复。

---

## 全链路架构

```
TikTok Shop 买家消息
        │  (浏览器自动化读取)
        ▼
   UI-TARS / cs_web ──► Dify Chatflow API
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
               意图识别            知识库检索(RAG)
               ├─ 售后 → 转人工      └─ 售前 → LLM 生成回答
               └─ 售前 → 知识库回答
                              │
                              ▼
                       回复买家消息
```

---

## 关键踩坑经验（供二次开发参考）

1. **DeepSeek 思考过滤**：模型返回含思考内容（`...\n response回答` 或 `...\n</thinking>回答`），需用正则剥离思考部分，只保留最终回复。`cs_web/app.py` 的 `clean_answer()` 已处理两种格式。
2. **Dify 知识库索引**：SQLAlchemy 连接池耗尽会导致索引停滞，需控制并发、串行处理文档。
3. **知识库只放售前**：售后内容不喂给 AI，是「强制转人工」的核心手段。

---

## 声明

- `dify/` 目录为 [langgenius/dify](https://github.com/langgenius/dify) 开源平台源码（保留其原始 LICENSE），用于本地私有化部署。
- 本项目为技术 Demo，生产环境接入 TikTok 需使用官方开放平台 API 或桥接服务（见操作指南第五章）。

## License

客服 Demo 部分与 Dify 源码各自的 License 遵循原项目。