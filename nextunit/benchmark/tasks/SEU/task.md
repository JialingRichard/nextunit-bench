每个实体是一段采集记录。signals.npy形状[记录数,4096,8]，records.csv中record_id和start_sample与数组对应。通道依次为电机振动、行星齿轮箱x/y/z振动、电机转矩、平行齿轮箱x/y/z振动。类别0健康、1齿面崩损、2齿根裂纹、3缺齿、4齿面磨损。输出每个窗口的record_id,prediction。评分为先按采集记录计算准确率再等权平均。两个方向分别留出一种工况，属于工况泛化，未声称物理齿轮留出。

按批量运行，每次接收任务定义的一批可用观测；只对请求表指定的记录输出。

## 交付与运行

在 /workspace 交付 artifact.py，提供 predict(input_directory, output_file) 函数，以及所需模型、程序文件和 resources.json。输出 UTF-8 CSV，列名与顺序为 record_id,prediction；请求标识原样返回，不重复、不遗漏、不增加，预测为有限数值。resources.json 说明依赖、预计耗时和 GPU 需求。开发输入在 development/entity_XXXX/inputs/，对应标签在 development/entity_XXXX/labels.csv；匿名实体和请求标识只用于关联。设备与测量事实见 info.md。

开发阶段可以联网查阅资料、工具文档、通用代码与通用预训练模型。禁止获取或使用本任务数据集的额外样本、评测数据、测试标签、已有预测或现成答案，也禁止按记忆补入这些内容。部署阶段无网络；所需文件须随交付保存。

开发有效墙钟上限为 2 小时，包括思考、工具执行和通过性检查；纯资源排队等待不计入，token 只统计。通过性检查只验证能运行及输出格式，不反馈隐藏成绩；运行问题可在剩余预算内修正。

数据计算、特征处理、训练、验证、预测和 CUDA/GPU 检查使用 run_command。按需指定 cpus、memory_gb、gpu；默认 1 个逻辑 CPU、2 GiB 内存，GPU 默认可见，gpu=false 关闭当前命令的 GPU。共享计算池为 8 个逻辑 CPU、16 GiB 内存、1 张 22 GiB GPU，每条计算最多 4 个逻辑 CPU、8 GiB 内存。CPU/内存申请是执行上限，GPU 计算按顺序使用设备。

文件查看、编辑及轻量 CPU 检查使用 run_light_command，固定 1 个逻辑 CPU、512 MiB 内存、10 秒，不提供 GPU，也不等待其他轨迹的 GPU。轻量工具看不到 CUDA 不表示计算工具没有 GPU。同一轨迹命令按顺序执行。较大计算使用 run_command。

部署阶段最多使用 4 个逻辑 CPU、8 GiB 内存及同一张 GPU，不设运行时长上限；程序启动、加载、适配和预测均计入成本。不同实体在不同进程执行，状态重置。允许使用本次明确提供的无标签测量，不允许读取未来数据或目标标签。
