声音来自五类工业设备：风机、齿轮箱、泵、滑轨和阀门。每段录音约10秒，单声道16kHz、16bit PCM。设备组大致对应一个产品，但组编号不保证是唯一物理设备身份。source与target代表运行转速、负载或环境噪声等条件变化，各条件变化方式依设备而异。训练录音为正常运行；目标域可供训练的正常录音很少，源域正常录音更多。测试含两种域的正常和异常运行声音；数据划分检验条件变化下的异常检测，并非严格新设备留出。齿轮箱由直流电机驱动曲柄滑块机构升降重物；泵持续循环水，滑轨重复预设运动，电磁阀周期控制气体或水流。记录使用麦克风阵列的第一通道；风机、齿轮箱、滑轨、阀门距离约0.6m，泵约0.6–1.0m。齿轮箱和滑轨在消声室录制后加入RT60约0.3秒的房间响应；其他设备在隔声间或普通房间录制。其后混入真实工厂背景声，SNR使用同设备组平均声音功率与噪声功率的比值定义，并非每段瞬时功率比。可能异常包括风机叶片损伤、失衡、堵塞、过电压；齿轮损伤、过载；泵污染、堵塞、泄漏、干转；轨道损伤、松带、缺润滑；阀内异物。

各匿名实体的设备与测量信息：
```json
[
  {
    "entity": "entity_0001",
    "facts": {
      "machine_type": "齿轮箱"
    }
  },
  {
    "entity": "entity_0002",
    "facts": {
      "machine_type": "风机"
    }
  },
  {
    "entity": "entity_0003",
    "facts": {
      "machine_type": "阀门"
    }
  },
  {
    "entity": "entity_0004",
    "facts": {
      "machine_type": "泵"
    }
  },
  {
    "entity": "entity_0005",
    "facts": {
      "machine_type": "齿轮箱"
    }
  },
  {
    "entity": "entity_0006",
    "facts": {
      "machine_type": "风机"
    }
  },
  {
    "entity": "entity_0007",
    "facts": {
      "machine_type": "风机"
    }
  },
  {
    "entity": "entity_0008",
    "facts": {
      "machine_type": "阀门"
    }
  },
  {
    "entity": "entity_0009",
    "facts": {
      "machine_type": "阀门"
    }
  },
  {
    "entity": "entity_0010",
    "facts": {
      "machine_type": "滑轨"
    }
  },
  {
    "entity": "entity_0011",
    "facts": {
      "machine_type": "阀门"
    }
  },
  {
    "entity": "entity_0012",
    "facts": {
      "machine_type": "阀门"
    }
  },
  {
    "entity": "entity_0013",
    "facts": {
      "machine_type": "风机"
    }
  },
  {
    "entity": "entity_0014",
    "facts": {
      "machine_type": "泵"
    }
  },
  {
    "entity": "entity_0015",
    "facts": {
      "machine_type": "滑轨"
    }
  },
  {
    "entity": "entity_0016",
    "facts": {
      "machine_type": "齿轮箱"
    }
  },
  {
    "entity": "entity_0017",
    "facts": {
      "machine_type": "阀门"
    }
  },
  {
    "entity": "entity_0018",
    "facts": {
      "machine_type": "滑轨"
    }
  },
  {
    "entity": "entity_0019",
    "facts": {
      "machine_type": "齿轮箱"
    }
  },
  {
    "entity": "entity_0020",
    "facts": {
      "machine_type": "泵"
    }
  },
  {
    "entity": "entity_0021",
    "facts": {
      "machine_type": "滑轨"
    }
  },
  {
    "entity": "entity_0022",
    "facts": {
      "machine_type": "风机"
    }
  },
  {
    "entity": "entity_0023",
    "facts": {
      "machine_type": "泵"
    }
  },
  {
    "entity": "entity_0024",
    "facts": {
      "machine_type": "风机"
    }
  },
  {
    "entity": "entity_0025",
    "facts": {
      "machine_type": "齿轮箱"
    }
  },
  {
    "entity": "entity_0026",
    "facts": {
      "machine_type": "阀门"
    }
  },
  {
    "entity": "entity_0027",
    "facts": {
      "machine_type": "滑轨"
    }
  },
  {
    "entity": "entity_0028",
    "facts": {
      "machine_type": "滑轨"
    }
  },
  {
    "entity": "entity_0029",
    "facts": {
      "machine_type": "泵"
    }
  },
  {
    "entity": "entity_0030",
    "facts": {
      "machine_type": "滑轨"
    }
  },
  {
    "entity": "entity_0031",
    "facts": {
      "machine_type": "泵"
    }
  },
  {
    "entity": "entity_0032",
    "facts": {
      "machine_type": "齿轮箱"
    }
  },
  {
    "entity": "entity_0033",
    "facts": {
      "machine_type": "齿轮箱"
    }
  },
  {
    "entity": "entity_0034",
    "facts": {
      "machine_type": "齿轮箱"
    }
  },
  {
    "entity": "entity_0035",
    "facts": {
      "machine_type": "风机"
    }
  },
  {
    "entity": "entity_0036",
    "facts": {
      "machine_type": "风机"
    }
  },
  {
    "entity": "entity_0037",
    "facts": {
      "machine_type": "阀门"
    }
  },
  {
    "entity": "entity_0038",
    "facts": {
      "machine_type": "风机"
    }
  },
  {
    "entity": "entity_0039",
    "facts": {
      "machine_type": "泵"
    }
  },
  {
    "entity": "entity_0040",
    "facts": {
      "machine_type": "滑轨"
    }
  },
  {
    "entity": "entity_0041",
    "facts": {
      "machine_type": "滑轨"
    }
  },
  {
    "entity": "entity_0042",
    "facts": {
      "machine_type": "泵"
    }
  },
  {
    "entity": "entity_0043",
    "facts": {
      "machine_type": "阀门"
    }
  },
  {
    "entity": "entity_0044",
    "facts": {
      "machine_type": "齿轮箱"
    }
  },
  {
    "entity": "entity_0045",
    "facts": {
      "machine_type": "泵"
    }
  }
]
```
