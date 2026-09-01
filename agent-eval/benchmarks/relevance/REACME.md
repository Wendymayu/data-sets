# Agent Relevance Evaluation Dataset

用于评估 LLM / Agent 输出与用户输入之间的相关性。

| 字段             | 类型   | 含义                                                         |
| ---------------- | ------ | ------------------------------------------------------------ |
| `id`             | string | 样本唯一标识                                                 |
| `input`          | string | 用户输入、问题或任务描述                                     |
| `output`         | string | LLM / Agent 针对 `input` 生成的输出                          |
| `label`          | int    | 相关性标签：`1` = 相关，`0` = 不相关                         |
| `sample_type`    | enum   | 样本类型：`positive` = 相关样本；`strong_negative` = 明显不相关样本；`hard_negative` = 与输入主题相关但没有真正回答用户需求的样本 |
| `construction`   | string | 样本构造方式，说明该样本是如何生成或处理得到的               |
| `source_dataset` | string | 原始数据集来源，用于记录样本的来源和数据溯源信息             |