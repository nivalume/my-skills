# 系统 / 数据库 / 分布式论文

包括：共识协议（Paxos、Raft）、复制与一致性（Dynamo、Chain Replication、CRDT）、存储引擎（LSM-tree、B-tree 变体）、事务与并发控制（MVCC、2PL、OCC）、调度与资源管理、MapReduce 类计算框架、缓存与负载均衡。

核心挑战：真实系统需要集群、磁盘、网络，notebook 里没有。解决办法是**确定性模拟**，在模拟中保留论文机制的本质，同时获得真实系统很难提供的东西：可控的故障注入和全局可观测性。

## 实现什么

- **离散事件模拟器（discrete-event simulation）**：一个 `heapq` 事件队列 + 模拟时钟 + 可配置的网络模型。所有随机性来自单一种子的 `rng`，因此任何 bug 都可以通过种子复现。

  ```python
  import heapq, itertools
  class Sim:
      def __init__(self, seed):
          self.now, self.q, self.rng = 0.0, [], np.random.default_rng(seed)
          self._seq = itertools.count()          # 同一时刻事件的稳定排序
          self.trace = []                        # (time, node, event, details) 用于画时序图
      def schedule(self, delay, fn, *args):
          heapq.heappush(self.q, (self.now + delay, next(self._seq), fn, args))
      def run(self, until):
          while self.q and self.q[0][0] <= until:
              self.now, _, fn, args = heapq.heappop(self.q)
              fn(*args)
  ```

- **网络模型**：可配置的延迟分布、丢包率、重复、乱序、网络分区（节点集合间的连通矩阵）。
- **节点**：按论文描述实现状态机和消息处理，**尽量逐条对应论文的规则**（Raft 的 Figure 2 就是天然的实现清单）。
- **存储类论文**：用内存结构模拟磁盘，但显式计数 I/O 次数、写入字节数、读放大/写放大/空间放大。

## 正确性检查

系统论文的核心 claim 通常是 **safety**（坏事永不发生）和 **liveness**（好事最终发生）。

- **Safety**：把论文陈述的每条性质写成检查函数，模拟中**每个事件之后**调用。例如：
  - 同一 term 最多一个 leader（election safety）
  - 已提交的日志不会丢失或被覆盖
  - 线性一致性 / 快照隔离不被违反
- **随机故障注入**：在很多个种子下随机崩溃/重启节点、制造分区、丢包，检查 safety 是否始终成立。报告"N 次随机运行、M 个事件、0 次违反"。
- **反例演示**：去掉论文的某条关键规则（例如 Raft 的"只提交当前 term 的条目"），用故障注入找到违反 safety 的种子，重放并画出时序图。这是展示"为什么需要这条规则"最有力的方式。
- **Liveness**：统计在故障停止后多长时间内系统恢复（选出 leader、请求完成），画分布。

## 验证实验设计

- **复现论文的时序/场景图**：论文中的场景图（如 Raft Figure 7、8）可以用模拟精确构造出来，再展示协议如何处理。
- **性能趋势而非绝对数字**：模拟中的吞吐量、延迟绝对值没有意义，但**趋势**有意义（随节点数、故障率、读写比、数据量的变化）。对照表中注明。
- **分析模型交叉验证**：论文给出分析公式（例如 LSM-tree 写放大 ≈ 层数 × size ratio、quorum 可用性概率）时，模拟测量值与公式对比。
- **排队论估算**：延迟/吞吐类 claim 可以用简单排队模型（M/M/1：$W = 1/(\mu-\lambda)$）估算，与模拟对比。

## 高价值可视化

- **消息时序图（message sequence chart）**：横轴时间、纵轴节点，箭头表示消息，颜色区分消息类型，标注崩溃/分区时刻。从 `sim.trace` 生成，这是系统论文最重要的图。
- **状态时间线**：每个节点在各时刻的角色（follower/candidate/leader）画成色块条（`broken_barh`）。
- **日志/存储结构状态**：各节点日志的方块图，LSM-tree 各层的 SSTable 分布。
- **故障注入统计**：恢复时间 CDF、不同参数下的可用性。

## 常见陷阱

- 模拟器本身的 bug 会被误认为协议问题：先用最简单的无故障场景验证模拟器行为符合手算预期。
- 同一模拟时刻的事件顺序必须确定（用递增序号打破平局），否则结果无法复现。
- 模拟时间和墙钟时间分开，不要在模拟里 `time.sleep`。
- 故障注入实验的运行次数要足够多才有说服力，但注意总运行时间预算，优先减小每次运行的时长。
- 论文正文里的协议描述常常省略边界情况（如 Raft 的 membership change 细节、日志压缩），明确说明 notebook 实现覆盖了哪些部分。