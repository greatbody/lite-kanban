# Lite Kanban

一个简洁优雅的个人任务看板应用，用于本地任务管理。

> [!CAUTION]
> **⚠️ 安全声明与使用警告**
> - **仅限本地单用户使用**：本项目专为个人在本地内网环境使用设计，未考虑多用户并发或公共网络访问。
> - **无鉴权机制**：系统**没有**账户概念，**没有**密码保护，也**没有任何**身份验证（Authentication）或授权（Authorization）逻辑。
> - **风险自担**：请勿将其部署到公网或向不可信人员开放访问。因将其用于公网访问或多用户环境而导致的任何数据泄露、丢失或系统损坏，本项目及其作者概不负责。


## 特性

- 📋 **六列看板**: Backlog → Planned → In Progress → Pending (Short) → Pending (Long) → Done
- 🎯 **进行中唯一性**: 同时只能有一个任务处于进行中状态
- ⏱️ **时间追踪**: 自动追踪任务在进行中的累计时间（精确到分钟）
- 📅 **每日任务处理**: 自动处理昨日未完成的任务
- 🏷️ **多标签支持**: 为任务添加多个标签
- 📊 **状态历史**: 记录所有状态变更历史
- 🎨 **素雅设计**: 简洁的界面，淡雅的配色

## 技术栈

- **后端**: Python + Flask + SQLite
- **前端**: Vue.js 3 (CDN) + Sortable.js
- **数据库**: SQLite

## 安装

### 前置要求

- Python 3.7+
- 现代浏览器（Chrome、Firefox、Safari、Edge）

### 步骤

1. **克隆或下载项目**

2. **安装 Python 依赖**

```bash
cd backend
pip install -r requirements.txt
```

3. **启动应用**

**方式一：使用启动脚本（推荐）**

前台运行（可用 Ctrl+C 停止）：
```bash
./start.sh
```

后台运行：
```bash
./start-bg.sh    # 启动
./stop.sh        # 停止
```

**方式二：手动启动**

```bash
cd backend
python app.py
```

服务将在 `http://localhost:5001` 启动，同时提供前端界面和 API 服务。

4. **访问应用**

在浏览器中打开 `http://localhost:5001` 即可使用。

## 使用指南

### 基本操作

- **创建任务**: 点击右上角"+ 新建任务"按钮
- **移动任务**: 直接拖拽任务卡片到目标列
- **编辑任务**: 点击任务卡片打开编辑窗口
- **删除任务**: 点击任务卡片右上角的 × 按钮

### 工作流

```
Backlog (任务池)
  ↓
Planned (今日计划)
  ↓
In Progress (进行中，仅1个)
  ↓
Done (完成)

随时可以移至:
- Pending (Short-term): 短期搁置
- Pending (Long-term): 长期搁置
```

### 任务流转规则

| 从 | 可以移动到 |
|---|---|
| Backlog | Planned, 删除 |
| Planned | In Progress, Pending (Short), Pending (Long) |
| In Progress | Done, Pending (Short), Pending (Long), 删除 |
| Pending (Short) | Planned, In Progress, Pending (Long) |
| Pending (Long) | Planned, 删除 |

### 特殊规则

1. **进行中唯一性**: 当你将新任务拖入 In Progress 时，当前进行中的任务会自动移至 Pending (Short-term)，原因记录为"被新任务挤出"。

2. **每日任务处理**: 点击"处理昨日任务"按钮，系统会自动将昨日未完成的任务（Planned/In Progress/Pending Short-term）移至今日 Planned，原因记录为"昨日未完成"。

3. **时间追踪**: 
   - 任务移入 In Progress 时开始计时
   - 任务移出 In Progress 时结束计时
   - 累计所有在 In Progress 的时间
   - 精确到分钟（不足1分钟按1分钟计）

## API 文档

所有 API 端点都在 `/api` 路径下。

### 任务管理

- `GET /api/tasks` - 获取所有任务
- `POST /api/tasks` - 创建新任务
- `GET /api/tasks/<id>` - 获取单个任务
- `PUT /api/tasks/<id>` - 更新任务信息
- `PUT /api/tasks/<id>/move` - 移动任务状态
- `DELETE /api/tasks/<id>` - 删除任务

### 历史和追踪

- `GET /api/tasks/<id>/history` - 获取状态变更历史
- `GET /api/tasks/<id>/time-tracking` - 获取时间追踪记录

### 系统操作

- `POST /api/daily-process` - 处理昨日未完成任务
- `GET /api/health` - 健康检查

## 数据存储

所有数据存储在 `kanban.db` SQLite 数据库文件中，包含三个表：

- **tasks**: 任务信息
- **status_history**: 状态变更历史
- **time_tracking**: 时间追踪记录

## 开发

### 项目结构

```
lite-kanban/
├── start.sh                # 前台启动脚本
├── start-bg.sh             # 后台启动脚本
├── stop.sh                 # 停止后台服务脚本
├── .gitignore              # Git 忽略文件
├── README.md               # 项目文档
├── backend/
│   ├── app.py              # Flask 应用
│   ├── database.py         # 数据库操作
│   └── requirements.txt    # Python 依赖
├── frontend/
│   ├── index.html          # 主页面
│   ├── style.css           # 样式
│   └── app.js              # Vue.js 应用
└── kanban.db               # SQLite 数据库（运行时生成）
```

### 自定义

- **修改配色**: 编辑 `frontend/style.css` 中的颜色变量
- **调整列数**: 修改 `frontend/app.js` 中的 `columns` 数组
- **修改端口**: 在 `backend/app.py` 中修改 `port` 参数

### 架构说明

Flask 应用同时提供：
- **前端静态文件**: 通过 `static_folder` 配置，将 `frontend/` 目录作为静态资源目录
- **API 服务**: 所有 `/api/*` 路径的请求由 Flask 路由处理
- **根路由**: `/` 返回 `index.html`

这种架构的优点：
- 一键启动，无需单独启动前后端
- 避免 CORS 问题
- 部署简单

## 许可

MIT License

## 作者

个人项目
