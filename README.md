# 🏛️ Tragedy — 基于智能体的社会经济模拟系统

**Tragedy** 是一个计算经济学模拟系统，通过异构智能体自底向上的交互，模拟宏观经济规律的涌现——不平等、商业周期、市场动力学——所有这些现象无需中央调控，仅从个体的局部规则中产生。

项目建立在 **基于智能体的计算经济学（Agent-Based Computational Economics, ACE）** 的学术基础之上，实现了该领域的经典模型，并提供实时可视化以观察经济现象的涌现过程。

> "If you didn't grow it, you didn't explain it." — Epstein & Axtell, *Growing Artificial Societies* (1996)

---

## 学术基础

Tragedy 实现的模型根植于 ACE 文献中的关键工作：

| 模型 | 参考文献 | 核心洞见 |
|------|---------|---------|
| **Yard-Sale** | Yakovenko & Rosser (2009), *Reviews of Modern Physics* | 随机配对交易中的乘法不对称性导致财富向单一智能体冷凝，形成帕累托幂律尾部 |
| **Sugarscape** | Epstein & Axtell (1996), *MIT Press* | 异构智能体遵循简单局部规则即可涌现财富不平等、环境承载力动态和去中心化价格均衡 |
| **K+S 宏观** | Dosi, Fagiolo & Roventini (2010), *J. Econ. Dyn. Control* | 熊彼特创新 + 凯恩斯需求 + 明斯基信贷 = 内生商业周期 |

### 核心机制

- **智能体决策**：有限理性启发式、模仿学习、遗传算法进化预测规则
- **市场匹配**：双边交易、标价市场、拍卖市场、工资议价
- **货币流动**：内生信用货币创造、复式记账、存量-流量一致性
- **生产与消费**：里昂惕夫/CES 生产函数、资本品创新、企业进入与退出
- **网络效应**：空间网格（环形拓扑）、社交网络（小世界/无标度）、供应链网络
- **不平等涌现**：基尼系数、洛伦兹曲线、帕累托尾部指数（Hill 估计量）

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    React 前端                            │
│  Canvas (空间视图) + D3 (图表) + Zustand (状态管理)       │
└────────────────┬────────────────────────────────────────┘
                 │ WebSocket (20 FPS 快照推送)
┌────────────────▼────────────────────────────────────────┐
│                  FastAPI 后端                            │
│  REST 端点 + WebSocket 流式推送 + 异步 SQLite            │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│               模拟引擎 (SimulationEngine)                 │
│  阶段化激活：生产 → 消费 → 结算 → 指标采集                │
│  AgentSet.do("step") 模式 (借鉴 Mesa 3)                   │
│  Numba JIT 加速热点计算                                   │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                 SQLite 数据库                            │
│  指标时序 + 运行元数据 + JSON 快照                        │
└─────────────────────────────────────────────────────────┘
```

**阶段化模拟循环**（每个 tick 按序执行）：

```
TICK t:
  1. PRODUCTION         — 企业生产、折旧、创新抽奖
  2. LABOR_MATCHING     — 劳动力市场匹配、工资议价
  3. GOODS_PRICING      — 企业设定价格 = 成本 × (1 + 加成率)
  4. CONSUMPTION        — 家庭消费、企业积累收入
  5. INVESTMENT         — 企业评估资本扩张、准备贷款
  6. CREDIT_MATCHING    — 银行发放贷款（内生货币创造）
  7. FINANCIAL_SETTLEMENT — 利息支付、债务清偿、股利分配
  8. TAXATION           — 政府税收与支出、央行利率政策
  9. ACCOUNTING         — 资产负债表更新、破产检查、企业进出
  10. METRICS           — 采集聚合统计量、推送 WebSocket
```

---

## 快速开始

### 环境要求

- **Python** 3.12+
- **Node.js** 20+（前端）
- pip 或 uv

### 安装

```bash
# 克隆仓库
git clone https://github.com/Theater-ahyeon/tragedy-socioeconomic-sim.git
cd tragedy-socioeconomic-sim

# 安装 Python 依赖
pip install -e "."

# 安装前端依赖
cd frontend
npm install
cd ..
```

### 命令行：运行模拟

```bash
# 运行 Yard-Sale 模型：1000 个智能体，5000 个 tick
python -m tragedy --model yard_sale --agents 1000 --ticks 5000

# 使用自定义配置文件
python -m tragedy --model yard_sale --config configs/yard_sale.yaml --ticks 10000

# 导出结果到 CSV
python -m tragedy --model yard_sale --agents 2000 --ticks 10000 --output results.csv
```

### Web 服务：实时可视化

```bash
# 终端 1：启动 API 服务器
tragedy-server
# → http://localhost:8000 （API 文档在 /docs）

# 终端 2：启动前端开发服务器
cd frontend
npm run dev
# → http://localhost:5173
```

然后在浏览器中：
1. 打开 http://localhost:5173
2. 点击 **▶ 启动** 按钮开始 Yard-Sale 模拟
3. 观察洛伦兹曲线实时动画、基尼系数攀升、财富分布直方图演化

---

## 项目结构

```
tragedy/
├── configs/                     # YAML 模拟配置文件
│   ├── defaults.yaml            # 全局默认参数
│   └── yard_sale.yaml           # Yard-Sale 模型参数
├── src/tragedy/
│   ├── core/                    # 模拟引擎核心
│   │   ├── engine.py            # 模拟循环、时钟、事件队列
│   │   ├── agent.py             # Agent 基类、AgentSet 集合（支持 filter/shuffle/do/groupby）
│   │   ├── scheduler.py         # SimulationStage 枚举、各模型的阶段顺序
│   │   ├── random.py            # 种子化 RNG 管理器（每个智能体独立随机子流）
│   │   └── space.py             # Grid2D 环形网格、Network 图拓扑
│   ├── economy/                 # 经济领域原语
│   │   ├── money.py             # Money 值对象、Account 账户、Ledger 复式账簿、Transaction 交易记录
│   │   ├── goods.py             # Good 商品、Inventory 库存、ProductionFunction 生产函数
│   │   ├── markets.py           # Market 抽象基类、BilateralMarket/PostedPriceMarket/BargainingMarket
│   │   └── accounting.py        # 财富守恒检验、复式记账平衡检验、资产负债表计算
│   ├── agents/                  # 智能体类型实现
│   │   └── household.py         # YardSaleAgent（Phase 1）、未来：Firm/Bank/Government
│   ├── models/                  # 模型组装（智能体 + 市场 + 阶段处理器）
│   │   ├── base.py              # BaseModel 抽象基类
│   │   └── yard_sale.py         # Yard-Sale 财富转移模型
│   ├── markets/                 # 市场机制具体实现（Phase 3 扩展）
│   ├── metrics/                 # 指标采集与分析
│   │   ├── collector.py         # MetricCollector：时序指标采集器
│   │   └── inequality.py        # Numba 加速：gini_coefficient()、lorenz_curve()、pareto_alpha()
│   ├── api/                     # FastAPI 应用
│   │   ├── app.py               # FastAPI 工厂函数、CORS、生命周期
│   │   ├── schemas.py           # Pydantic 请求/响应模型
│   │   ├── routes/              # REST 端点（simulation、config、metrics）
│   │   └── websocket.py         # WebSocket 流式推送（帧率解耦）
│   ├── storage/                 # 持久化层
│   │   ├── database.py          # 异步 SQLite 连接、schema 迁移
│   │   └── repository.py        # MetricRepository：运行管理、指标 CRUD
│   └── utils/                   # 工具函数
│       ├── config.py            # YAML 配置加载与合并
│       └── logging.py           # 结构化日志配置
├── frontend/                    # React 19 + TypeScript 单页应用
│   └── src/
│       ├── components/          # 可视化组件
│       │   ├── SimulationControl.tsx  # 模拟控制面板（启动/暂停/恢复/停止）
│       │   ├── MetricPanel.tsx        # KPI 指标卡片（基尼系数、财富份额等）
│       │   ├── LorenzCurve.tsx        # Canvas 洛伦兹曲线
│       │   ├── DistributionHistogram.tsx  # 财富分布直方图
│       │   └── TimeSeriesChart.tsx    # 指标时序折线图
│       ├── hooks/               # useWebSocket、useSimulation
│       └── store/               # Zustand 全局状态管理
├── tests/
│   ├── unit/                    # 单元测试（agent、money、inequality）
│   ├── integration/             # 集成测试（Yard-Sale 端到端）
│   └── conftest.py              # 共享 fixtures
└── docs/                        # 架构与模型文档
```

---

## API 参考

### REST 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/simulation/start` | 启动新的模拟运行 |
| `POST` | `/api/v1/simulation/pause` | 暂停模拟 |
| `POST` | `/api/v1/simulation/resume` | 恢复暂停的模拟 |
| `POST` | `/api/v1/simulation/stop` | 停止模拟 |
| `POST` | `/api/v1/simulation/step` | 单步推进一个 tick（需暂停状态） |
| `GET` | `/api/v1/simulation/status` | 获取当前模拟状态 |
| `GET` | `/api/v1/configs` | 列出所有可用配置 |
| `POST` | `/api/v1/configs` | 创建新配置 |
| `GET` | `/api/v1/configs/{name}` | 获取指定配置 |
| `PUT` | `/api/v1/configs/{name}` | 更新配置 |
| `DELETE` | `/api/v1/configs/{name}` | 删除配置 |
| `GET` | `/api/v1/metrics/timeseries` | 查询指标时序数据 |
| `GET` | `/api/v1/metrics/latest` | 获取最新指标快照 |
| `GET` | `/api/v1/metrics/summary` | 获取运行摘要 |

### 启动模拟请求示例

```json
POST /api/v1/simulation/start
Content-Type: application/json

{
  "config_id": "yard_sale",
  "max_ticks": 5000,
  "collect_every": 10
}
```

响应：
```json
{
  "status": "started",
  "model": "yard_sale",
  "seed": 42,
  "agents": 1000
}
```

### WebSocket 协议

```
ws://localhost:8000/ws/simulation
```

**服务器 → 客户端**（指标快照，每秒 20 帧）：
```json
{
  "type": "snapshot",
  "tick": 500,
  "metrics": {
    "gini": 0.4231,
    "total_wealth": 98500.0,
    "top_1_pct_share": 0.204,
    "top_10_pct_share": 0.471,
    "bottom_50_pct_share": 0.089,
    "pareto_alpha": 1.82
  },
  "lorenz": {
    "population": [0.0, 0.01, ..., 1.0],
    "wealth": [0.0, 0.002, ..., 1.0]
  },
  "distribution": {
    "bins": [0.1, 1.0, 10.0, ..., 10000.0],
    "counts": [0, 15, 234, ..., 3]
  }
}
```

**客户端 → 服务器**（控制命令）：
```json
{"type": "command", "action": "pause"}
{"type": "command", "action": "resume"}
{"type": "command", "action": "stop"}
```

---

## Yard-Sale 模型详解

### 模型机制

Yard-Sale 是研究财富不平等涌现的最简经典模型。每个 tick 中，智能体随机配对，每对中较贫穷的一方以 `fraction` 的比例拿出财富作为赌注，由一枚可能有偏的硬币决定赢家。

**核心动力学**：
- 硬币公平（bias=0）时，规则完全对称
- 但由于**乘法不对称性**——先赢 20% 再输 20% = 初始值的 96%——财富不可逆地向少数智能体集中
- 系统最终收敛到一个极端不平等稳态：基尼系数 ≈ 0.85，帕累托指数 α ≈ 1.5

### 配置参数

```yaml
# configs/yard_sale.yaml
agents:
  num_households: 1000      # 智能体数量
  initial_wealth: 100.0     # 初始财富（每人相等）

transfer:
  fraction: 0.05            # 转移比例（较贫穷方财富的 5%）
  bias: 0.0                 # 硬币偏差（-1 到 1，0=公平，正值=富人优势）

simulation:
  max_ticks: 5000           # 最大模拟步数
  collect_every: 10         # 每 N 个 tick 采集一次指标
```

### 典型实验结果（1000 智能体，5000 tick）

| 指标 | 初始值 | 最终值 | 说明 |
|------|--------|--------|------|
| **基尼系数** | 0.0 | ~0.85 | 从完全平等到高度不平等 |
| **Top 1% 财富份额** | 1% | ~40% | 最富有 10 人掌握四成财富 |
| **Top 10% 财富份额** | 10% | ~70% | 最富有 100 人掌握七成财富 |
| **底层 50% 份额** | 50% | ~5% | 半数人口仅拥有 5% 财富 |
| **帕累托指数 α** | — | ~1.5 | α<2 表示极端不平等（肥尾） |
| **总财富** | $100,000 | $100,000 | 守恒（无生产/消费） |

---

## 实施路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| **Phase 1** | Yard-Sale 模型 + 核心引擎 + Web 可视化 | ✅ 已完成 |
| **Phase 2** | Sugarscape 空间模型（环形网格、资源再生、智能体生命周期） | 🔜 计划中 |
| **Phase 3** | K+S 宏观模型（企业/银行/政府/央行、内生商业周期、明斯基信贷动态） | 🔜 计划中 |
| **Phase 4** | 参数扫描、C++ 热点加速、政策干预框架、经验数据校准 | 🔜 计划中 |

---

## 开发指南

```bash
# 运行全部测试（当前 59 个全部通过）
pytest tests/ -v

# 运行带基准测试
pytest --benchmark-enable

# 代码检查
ruff check src/

# 类型检查
mypy src/

# 安装开发依赖
pip install -e ".[dev]"
```

### 核心设计决策

1. **自定义引擎优于 Mesa**：经济模拟需要有序阶段（生产→消费→结算）、市场匹配机制、复式记账——这些是 Mesa 等通用 ABM 框架不具备的
2. **Python 优先于 C++**：开发速度优先，Numba JIT 对 50 万智能体规模足够；性能瓶颈可通过 pybind11 精准迁移到 C++
3. **AgentSet.do() 模式**：`firms.filter(active=True).shuffle().do("set_price")` 比手动循环更具表达力，便于未来并行化
4. **WebSocket 帧率解耦**：模拟全速运行（Yard-Sale 可达数千 tick/秒），可视化按 20 FPS 独立采样，互不阻塞
5. **每智能体独立 RNG 子流**：确保打乱顺序不影响结果，实现严格可复现性（A/B 测试必备）

---

## 参考文献

1. Epstein, J. M., & Axtell, R. L. (1996). *Growing Artificial Societies: Social Science from the Bottom Up.* MIT Press.
2. Yakovenko, V. M., & Rosser, J. B. (2009). "Statistical mechanics of money, wealth, and income." *Reviews of Modern Physics*, 81(4), 1703.
3. Dosi, G., Fagiolo, G., & Roventini, A. (2010). "Schumpeter meeting Keynes: A policy-friendly model of endogenous growth and business cycles." *Journal of Economic Dynamics and Control*, 34(9), 1748-1767.
4. Arthur, W. B. (1999). "Complexity and the Economy." *Science*, 284(5411), 107-109.
5. Farmer, J. D., & Foley, D. (2009). "The economy needs agent-based modelling." *Nature*, 460(7256), 685-686.
6. Tesfatsion, L., & Judd, K. L. (eds.) (2006). *Handbook of Computational Economics, Volume 2: Agent-Based Computational Economics.* Elsevier.

---

## 许可证

MIT License — 详见 [LICENSE](LICENSE) 文件。
