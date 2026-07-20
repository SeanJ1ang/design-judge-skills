# 获奖作品观察基准覆盖

[English](benchmark-coverage_EN.md)

Design Judge 当前包含 **22,125 条**来自公开设计奖来源的获奖或入围作品聚合观察记录。它们用于解释类别、学科与竞赛背景，不参与核心评分，也不代表官方评审权重或获奖概率。

## 覆盖范围

| 来源项目 | 观察记录 | 年份 | 规范类别 | 聚合配置 |
|---|---:|---|---:|---:|
| International Design Excellence Awards (IDEA) | 1,024 | 2022–2025 | 24 | 22 |
| iF DESIGN AWARD | 10,644 | 2024–2026 | 104 | 41 |
| iF DESIGN TALENT AWARD / iF DESIGN STUDENT AWARD | 427 | 2022–2026 | 15 | 6 |
| Red Dot Award | 10,030 | 2024–2026 | 106 | 47 |

## 生成与质量约束

- 表格由四份版本化 `manifest.json` 自动生成，总量不是人工填写。
- 当前质量门均报告重复 entry key 为 0，类别和年份缺失为 0。
- 原始作品记录、标题、设计者、公司、图片和来源 URL 不在公共仓库发布。
- 所有聚合配置的 `score_effect` 均为 `none`；观察背景不得改变核心量表分数。
- 当前配置标记为 `machine_generated_needs_human_review`，映射结论应保持描述性和可复核。

## 不能推出的结论

- 样本只包含获奖或入围作品，没有未获奖对照组。
- 不能从这些数据估计获奖概率、官方权重或未公开评委偏好。
- 不同奖项的类别体系和年度覆盖不同，不能直接比较获奖数量。
- iF Student 观察背景只适用于 `student_concept`；不能用于成熟作品轨道。

## 可复现入口

运行以下命令可根据 manifests 重新生成本页：

```powershell
python tools/generate_benchmark_coverage.py
python tools/generate_benchmark_coverage.py --check
```
