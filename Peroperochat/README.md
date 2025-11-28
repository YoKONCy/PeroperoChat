<div align="center">

<h1>Peroperochat — 更懂你的 AI 伙伴</h1>

<img alt="Peroperochat" src="https://img.shields.io/badge/Python-3.10%2B-blue"> <img alt="Frontend" src="https://img.shields.io/badge/Node.js-18%2B-success"> <img alt="License" src="https://img.shields.io/badge/License-MIT-green">

<p>一个友好、可配置、带长记忆与人格评估的本地 AI 伙伴。支持 Live2D 展示与 3D 模型上传。</p>

</div>

---

**零门槛启动、易于扩展，写给热爱创造的你。**

---

## 简介

Peroperochat 是一个前后端分离的开源 AI 伙伴项目：
- 前端基于 `Vue 3 + Vite + Element Plus`，提供聊天区、模型参数设置、系统/人设提示词、提示词查看器、长记忆中心与 Live2D 展示。
- 后端基于 `FastAPI`，提供会话、模型列表、记忆读写/维护、3D 模型上传等 REST 接口，可适配不同模型提供商。

愿景：打造一个“同一位 AI 伙伴，在不同场景同享记忆”的统一陪伴体验。

## 功能亮点
- 聊天区 Markdown 渲染、复制/编辑/重生成；支持流式与非流式回复。
- 模型参数可视化配置（温度/Top P/惩罚等），一键获取并筛选模型列表。
- 系统/人设/后置提示词管理，提示词查看器一键导出请求序列。
- 人格评估：按轮次自动触发，生成十二维人格画像并迭代更新。
- 长记忆中心：事件/爱好记录的查询、插入、删除与合并维护。
- Live2D 控件：更换模型、随机换装；支持 3D 模型上传与静态访问。

## 快速开始

前置要求：`Python 3.10+`、`Node.js 18+`。

- 安装并启动后端（FastAPI）
  - 在项目根目录执行：
    - `pip install -r backend/requirements.txt`
    - 启动：`uvicorn Peroperochat.backend.app.main:app --host 0.0.0.0 --port 8000 --reload`
  - 默认后端地址：`http://localhost:8000`

- 安装并启动前端（Vite）
  - `cd frontend`
  - `npm install`
  - `npm run dev`
  - 默认前端地址：`http://localhost:5173`

## 进阶用法

### 模型 API 配置与获取模型
- 前端“API 设置”弹窗支持配置 `API 地址` 与 `API 秘钥`，并调用后端列出模型：
  - `GET /api/models`
  - 请求头：`Authorization: Bearer <key>`；查询参数：`api_base`

### 会话调用
- 非流式：`POST /api/chat`
- 流式：`POST /api/chat/stream`
- 副模型（可选）参与记忆预处理：在请求头与查询参数中提供：
  - `X-Assistant-Authorization: Bearer <副模型秘钥>`
  - `X-Assistant-Model: <副模型模型名>`（支持 URL 编码）
  - 查询参数：`assistant_api_base`
- 可用 `X-Disable-Memory: 1` 暂时关闭长记忆写入。

### 长记忆中心
- 列表：`GET /api/memory/list?type=&limit=&offset=`
- 插入：`POST /api/memory/insert { type, text }`
- 删除：`POST /api/memory/delete?id=...`
- 预选：`POST /api/memory/select { messages, model }`
- 维护/合并：`POST /api/memory/maintain { model }`

### 默认提示词
- 后端 `backend/config.ini` 的 `prompts` 段提供默认的：
  - `system_prompt_default`
  - `persona_prompt_default`
  - `post_prompt_default`
- 后端解析位于 `backend/app/config_loader.py`，前端初次加载会读取并填充为空的输入框。

### Live2D 与 3D 模型
- 前端会加载 `public/live2d-widget/autoload.js` 的 Live2D 组件，提供“更换模型”“随机换装”等操作。
- 3D 模型上传：`POST /api/models/3d/upload`（接受 `.glb`/`.gltf`）；静态访问路径：`/static/models/<filename>`。

### 数据重置
- 清空所有本地数据：`POST /api/reset`

## 项目架构

```
Peroperochat/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI 入口（会话/模型/记忆/3D 上传）
│   │   ├── config_loader.py       # INI 配置加载/保存
│   │   ├── db.py                  # 记忆存取封装（SQLite 等）
│   │   ├── memory_service.py      # 记忆预处理与维护逻辑
│   │   └── static/models/         # 3D 模型静态目录
│   ├── requirements.txt
│   └── config.ini
└── frontend/
    ├── src/
    │   ├── App.vue                # 主界面与功能入口
    │   └── components/
    │       ├── ChatArea.vue       # 聊天区
    │       ├── MemoryCenter.vue   # 长记忆中心
    │       └── Live2DWidget.vue   # Live2D 控件
    ├── public/live2d-widget/      # Live2D 资源
    ├── package.json
    └── vite.config.js
```

## 接口速查
- `GET /api/models`：列出模型；需 `Authorization`；`api_base` 可选。
- `POST /api/chat`：非流式聊天；可用副模型与禁用记忆头。
- `POST /api/chat/stream`：流式聊天；同上。
- 记忆：
  - `GET /api/memory/list`
  - `POST /api/memory/insert`
  - `POST /api/memory/delete`
  - `POST /api/memory/select`
  - `POST /api/memory/maintain`
- 3D：`POST /api/models/3d/upload`、`GET /api/models/3d/sample`
- 重置：`POST /api/reset`

## 配置说明
- 后端 INI：`backend/config.ini`
  - `openai.api_base` / `openai.api_key`
  - `prompts.*` 默认提示词
  - `timeouts.*` 接口超时参数
  - `semantic.*` 语义写入频率等
- 环境变量（后端可选）：
  - `OPENAI_API_KEY`、`OPENAI_API_BASE`、`POST_SYSTEM_PROMPT`、`SEMANTIC_WRITE_EVERY_N`
- 前端本地存储键：
  - `ppc.apiBase`、`ppc.apiKey`、`ppc.modelName`、`ppc.modelSettings`、`ppc.messages`、`ppc.personaProfile`、`ppc.evalWindow`、`ppc.assist.*`

## 开发与部署
- 开发：本地双端启动（见“快速开始”），前端默认自动连到 `http://localhost:8000`。如需指定，可设置 `VITE_API_BASE` 或在 UI 中配置。
- 部署：后端使用 `uvicorn` 或容器运行；前端使用 `vite build` 输出静态资源，部署到任意静态服务器（Nginx、Netlify 等）。

## TODO
- Live2D 本地模型管理完善
- 向量检索管线重建与记忆回注
- 人格评估与提示词工作台增强
- 多模型路由与提供商适配

