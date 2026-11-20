按独立电芯顺序处理已完成的有效放电观测，每次只得到当前观测目录。query.csv 含record_id、从1开始的observed_cycle和forecast_horizon=10；observation.csv 提供当前已测得的容量measured_capacity_Ah及当时可观测量；signals.npz为当前观测的信号。数组包括time_s、voltage_V、current_A、step_index、charge_capacity_Ah、discharge_capacity_Ah、internal_resistance_ohm；记录自前次放电结束后的充电/休息过程至本次完整放电结束。charge_capacity_Ah和discharge_capacity_Ah是测试仪累计计数，跨循环不一定清零。步骤2为恒流充电、4为恒压充电、7为放电，其他步骤为源测试流程；各数组对齐。预测当前观测之后第10次有效完整放电观测的测得容量，单位Ah；不是估计当前放电量。间隔按有效观测次数计，不按天数或源文件重置的循环号计。可使用同电芯过去调用的状态，跨电芯重置。输入不会给出目标期曲线、容量或剩余观测数量。主指标先计算每个电芯所有预测的MAE，再对电芯等权平均。

按流式运行，每次只接收当前块及该块明确包含的过去信息；同一实体的调用可保留历史状态。

## 交付与运行

在 /workspace 交付 artifact.py，提供 predict(input_directory, output_file) 函数，以及所需模型、程序文件和 resources.json。输出 UTF-8 CSV，列名与顺序为 record_id,prediction；请求标识原样返回，不重复、不遗漏、不增加，预测为有限数值。resources.json 说明依赖、预计耗时和 GPU 需求。开发输入在 development/entity_XXXX/inputs/，对应标签在 development/entity_XXXX/labels.csv；匿名实体和请求标识只用于关联。设备与测量事实见 info.md。

开发阶段可以联网查阅资料、工具文档、通用代码与通用预训练模型。禁止获取或使用本任务数据集的额外样本、评测数据、测试标签、已有预测或现成答案，也禁止按记忆补入这些内容。部署阶段无网络；所需文件须随交付保存。

开发有效墙钟上限为 2 小时，包括思考、工具执行和通过性检查；纯资源排队等待不计入，token 只统计。通过性检查只验证能运行及输出格式，不反馈隐藏成绩；运行问题可在剩余预算内修正。

数据计算、特征处理、训练、验证、预测和 CUDA/GPU 检查使用 run_command。按需指定 cpus、memory_gb、gpu；默认 1 个逻辑 CPU、2 GiB 内存，GPU 默认可见，gpu=false 关闭当前命令的 GPU。共享计算池为 8 个逻辑 CPU、16 GiB 内存、1 张 22 GiB GPU，每条计算最多 4 个逻辑 CPU、8 GiB 内存。CPU/内存申请是执行上限，GPU 计算按顺序使用设备。

文件查看、编辑及轻量 CPU 检查使用 run_light_command，固定 1 个逻辑 CPU、512 MiB 内存、10 秒，不提供 GPU，也不等待其他轨迹的 GPU。轻量工具看不到 CUDA 不表示计算工具没有 GPU。同一轨迹命令按顺序执行。较大计算使用 run_command。

部署阶段最多使用 4 个逻辑 CPU、8 GiB 内存及同一张 GPU，不设运行时长上限；程序启动、加载、适配和预测均计入成本。不同实体在不同进程执行，状态重置。允许使用本次明确提供的无标签测量，不允许读取未来数据或目标标签。
