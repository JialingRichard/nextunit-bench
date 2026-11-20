你是一名刚到任的运维工程师。这里的设备是同型号旋转机械，你需要为它们搭建一套自动化的状态判别工具，并交付一个可运行的预测程序。

## 你获得的数据

一个数据目录，包含若干台设备的测量记录：

- 开发数据按匿名设备目录组织，例如 `development/entity_0001/inputs/`；对应标签位于 `development/entity_0001/labels.csv`。设备目录名与记录标识只用于关联记录。
- 输入目录的 `records.json` 是一个列表，每项包含字符串 `record_id` 和相对路径 `signal_file`；每个信号文件为 NPZ，对应一次完整测量。
- NPZ 内含一维数值数组 `force`、`phase_current_1`、`phase_current_2`、`speed`、`temp_2_bearing_module`、`torque`、`vibration_1`。各数组长度以文件自身为准，通道之间长度不一定相同。每个数组的下标表示该通道在本次测量内的采样顺序；测量之间没有累计寿命时间轴。
- 部分设备的测量带有状态标签。标签 CSV 的列为 `record_id,target`；`target` 取值为 `0`=正常、`1`=外圈故障、`2`=内圈故障、`3`=复合故障，按 `record_id` 与测量一一对应。

## 设备与测量信息

随附一份关于设备与测量条件的信息文档 `info.md`。其中内容来自设备方的技术资料，我们未做核验，其可信度由你自行判断。

## 你要交付的

一个预测程序，接口为 `predict(input_directory, output_file)`：

- 部署输入目录保持 `development/entity_XXXX/inputs` 中相同的匿名设备目录名；设备目录名仅用于关联记录。
- 输入：一台设备的测量记录目录，包含 `records.json` 及其引用的 NPZ 文件，结构与你获得的数据一致。
- 输出：一个 UTF-8 CSV 文件，列名及顺序为 `record_id,prediction`。每次完整测量一行；`prediction` 为状态编码 `0`、`1`、`2` 或 `3`。 `record_id` 原样返回，不重复、不遗漏、不增加；预测值为有限数值。
- 程序入口放在 `artifact.py`，并随附程序所需文件和 `resources.json`，说明依赖、预计耗时与 GPU 需求。
- 部署运行时，程序可以读取目标设备自身在上述范围内的无标签测量记录。
- 交付后我们会先用少量样本运行该程序做基础通过性检查；无法运行会退回给你修改。


## 评价方式

你的程序将用于未见过的设备。主指标：先对每个轴承计算预测正确的测量数占该轴承总测量数的比例，再对轴承等权平均。


按批量运行，每次接收任务定义的一批可用观测；只对请求表指定的记录输出。

## 交付与运行

在 /workspace 交付 artifact.py，提供 predict(input_directory, output_file) 函数，以及所需模型、程序文件和 resources.json。输出 UTF-8 CSV，列名与顺序为 record_id,prediction；请求标识原样返回，不重复、不遗漏、不增加，预测为有限数值。resources.json 说明依赖、预计耗时和 GPU 需求。开发输入在 development/entity_XXXX/inputs/，对应标签在 development/entity_XXXX/labels.csv；匿名实体和请求标识只用于关联。设备与测量事实见 info.md。

开发阶段可以联网查阅资料、工具文档、通用代码与通用预训练模型。禁止获取或使用本任务数据集的额外样本、评测数据、测试标签、已有预测或现成答案，也禁止按记忆补入这些内容。部署阶段无网络；所需文件须随交付保存。

开发有效墙钟上限为 2 小时，包括思考、工具执行和通过性检查；纯资源排队等待不计入，token 只统计。通过性检查只验证能运行及输出格式，不反馈隐藏成绩；运行问题可在剩余预算内修正。

数据计算、特征处理、训练、验证、预测和 CUDA/GPU 检查使用 run_command。按需指定 cpus、memory_gb、gpu；默认 1 个逻辑 CPU、2 GiB 内存，GPU 默认可见，gpu=false 关闭当前命令的 GPU。共享计算池为 8 个逻辑 CPU、16 GiB 内存、1 张 22 GiB GPU，每条计算最多 4 个逻辑 CPU、8 GiB 内存。CPU/内存申请是执行上限，GPU 计算按顺序使用设备。

文件查看、编辑及轻量 CPU 检查使用 run_light_command，固定 1 个逻辑 CPU、512 MiB 内存、10 秒，不提供 GPU，也不等待其他轨迹的 GPU。轻量工具看不到 CUDA 不表示计算工具没有 GPU。同一轨迹命令按顺序执行。较大计算使用 run_command。

部署阶段最多使用 4 个逻辑 CPU、8 GiB 内存及同一张 GPU，不设运行时长上限；程序启动、加载、适配和预测均计入成本。不同实体在不同进程执行，状态重置。允许使用本次明确提供的无标签测量，不允许读取未来数据或目标标签。
