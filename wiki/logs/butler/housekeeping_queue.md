# Housekeeping Queue

内务整理任务队列。由 H10 全库扫描填充，由 W1 三队列选取算法消费。

---

## H-P1 — 立即内务

（暂无）

---

## H-P2 — 常规内务

（初始为空，等待第一次 H10 scan 填充）

---

## H-P3 — 扫描类（每11轮）

- [ ] H10 housekeeping-scan | all | 首次全库健康扫描
