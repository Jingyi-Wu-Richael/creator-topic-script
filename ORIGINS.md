# 方法来源与改编

制作日期：2026-09-15。技能名：creator-topic-script；显示名：创作者选题脚本助手。

## ai-topic-scout

来源：https://github.com/Jingyi-Wu-Richael/ai-topic-scout 。读取版本：44def0302aff5784fd8e7121411f5940ba9d271f 。已读取README、SKILL.md、references/sources.md、agents/openai.yaml及LICENSE。

继承：10类AI默认信息源、当期事实核验、同事件去重、观众价值与创作空间判断。改编：每日默认交付5张精选卡，资料备稿最多3张；来源受限时明确实际覆盖；以文字理由取代默认数值打分。用户指定数量优先。

原仓库为MIT许可，版权声明保留于LICENSE。原仓库代码/说明的许可不自动覆盖用户附件中的所有材料。

## 用户提供的x-collect.zip

已读取：SKILL.md、x-skills-optimization.md、X-For-You-Feed-Algorithm.md、Humanizer-zh.md。附件没有提供完整x-filter、x-create、ContextStore实现；不会假定这些工具已安装。

本技能重新编写流程，吸收：官方→机制→对比→缺口的研究框架、每轮去重、主题聚类、偏好反馈与自然语言编辑原则。

没有移植：固定2024/2025年份、固定个人目录、未提供的脚本调用、强制20%探索、0.6来源衰减、未校准的互动概率、模拟用户打分与自动重写循环。附件中的推荐算法描述仅为参考材料，不作为已核实的X当前算法事实或本技能的实际机器学习能力。

没有将附件原文整份复制进公开包；原作者信息、可能的原始许可与附件中的示例陈述仍归原材料，不声称其示例内容已经核实。Humanizer相关方法改写为简短编辑原则，保留事实限定优先，避免为“自然”添加虚构反馈或经历。

## 本次新增

按当前用户工作流增加：选题确认或授权自动选择、默认90秒但可变时长、口播与镜头对应、brief要求核对、本地引用关系检查与估时工具。

通用部分是Markdown说明与Python标准库辅助工具。agents/openai.yaml用于Codex展示。其他Skill运行器的安装兼容性及商店上架需要在实际平台另行验证；本文件不是兼容性认证。
