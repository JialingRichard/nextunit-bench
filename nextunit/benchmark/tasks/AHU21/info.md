# 空气处理机组：设备、测量与工况

[H01] 设备为空气处理机组，用于建筑通风；具备板式换热器进行热回收，并带旁通、加热和制冷功能。来源说明中还记载，其中一台机组带空气加湿器。

[H02] 运行涉及加热、通风和制冷过程。测量与控制字段覆盖风机、风阀、加热/制冷阀及水泵、热回收旁通、空气与水温，以及部分机组的过滤器状态、压差、湿度和蒸汽加湿控制。原始采集包括人为施加运行异常的过程；不提供异常发生时刻或对应实体。

[H03] 各机组名义采样间隔为 300 秒。字段名中的 `required_value` 表示所需/设定值，`real_value` 表示记录的实际值，`min`、`max` 表示记录的上下界；`logic` 是逻辑量字段，`signal` 是控制信号字段。字段名保留原有拼写，包括 `exahust`。来源卡将温度列标为温度量，其余大部分列的单位未指定；未给出逐通道传感器精度、校准信息、控制信号标度或压差单位。

[H04] 设备说明称一台机组带空气加湿器；通道元数据则在下表两台机组中登记了蒸汽加湿控制与相对湿度字段。两项来源描述同时保留，现有材料没有说明这一差异的原因。通道的登记本身未说明该部件是否始终安装或启用。

[H05-entity_0001] **entity_0001**：名义采样间隔 300 秒；未登记蒸汽加湿控制通道。完整测量/控制字段如下：

- `air_temperature__max__supply_air_outlet`
- `air_temperature__real_value__exahust_air_inlet`
- `signal__required_value__heater_valve`
- `signal__required_value__heat_recovery_bypass`
- `logic__required_value__valve_exahust_air_outlet`
- `water_temperature__real_value__chiller_behind`
- `air_temperature__required_value__exahust_air_inlet`
- `logic__real_value__fan_fresh_air`
- `signal__required_value__fan_fresh_air`
- `logic__required_value__valve_outdoor_air`
- `logic__real_value__fan_exahust_air`
- `logic__required_value__chiller`
- `water_temperature__real_value__heater_before`
- `water_temperature__real_value__heater_behind`
- `water_temperature__required_value__heater`
- `air_temperature__real_value__supply_air_outlet`
- `logic__required_value__chiller_pump`
- `air_temperature__min__supply_air_outlet`
- `logic__real_value__air_handling_unit`
- `signal__required_value__chiller_valve`
- `logic__required_value__heater_pump`
- `logic__required_value__heater`
- `signal__required_value__fan_exahust_air`

[H05-entity_0002] **entity_0002**：名义采样间隔 300 秒；未登记蒸汽加湿控制通道。完整测量/控制字段如下：

- `signal__required_value__fan_exahust_air`
- `logic__real_value__filter_exahust_air`
- `logic__real_value__fan_fresh_air`
- `logic__real_value__air_handling_unit`
- `signal__required_value__heater_valve`
- `water_temperature__required_value__heater`
- `air_temperature__required_value__exahust_air_inlet`
- `signal__min__fan_fresh_air`
- `logic__required_value__valve_exahust_air_outlet`
- `air_temperature__max__supply_air_outlet`
- `logic__real_value__filter_outdoor_air`
- `logic__required_value__valve_outdoor_air`
- `water_temperature__real_value__heater_behind`
- `air_temperature__real_value__exahust_air_inlet`
- `air_temperature__min__supply_air_outlet`
- `air_temperature__real_value__supply_air_outlet`
- `water_temperature__real_value__chiller_behind`
- `signal__required_value__heat_recovery_bypass`
- `water_temperature__real_value__heater_before`
- `logic__real_value__fan_exahust_air`
- `logic__required_value__heater`
- `logic__required_value__chiller_pump`
- `logic__required_value__heater_pump`
- `logic__required_value__chiller`
- `signal__required_value__chiller_valve`
- `signal__required_value__fan_fresh_air`
- `signal__max__fan_fresh_air`

[H05-entity_0003] **entity_0003**：名义采样间隔 300 秒；登记了蒸汽加湿控制通道。完整测量/控制字段如下：

- `logic__real_value__fan_exahust_air`
- `air_temperature__max__supply_air_outlet`
- `air_temperature__required_value__exahust_air_inlet`
- `logic__required_value__valve_outdoor_air`
- `air_temperature__real_value__supply_air_outlet`
- `logic__real_value__fan_fresh_air`
- `signal__required_value__chiller_valve`
- `air_temperature__min__supply_air_outlet`
- `logic__real_value__air_handling_unit`
- `pressure_dif__real_value__supply_air_outlet`
- `signal__required_value__steam_humidifier`
- `water_temperature__real_value__heater_before`
- `logic__required_value__valve_exahust_air_outlet`
- `water_temperature__real_value__chiller_behind`
- `logic__required_value__chiller_pump`
- `relative_humidity__real_value__supply_air_outlet`
- `water_temperature__real_value__heater_behind`
- `signal__required_value__heater_valve`
- `signal__required_value__heat_recovery_bypass`
- `signal__required_value__fan_fresh_air`
- `signal__required_value__fan_exahust_air`
- `logic__required_value__heater_pump`
- `relative_humidity__required_value__supply_air_outlet`
- `air_temperature__real_value__exahust_air_inlet`

[H05-entity_0004] **entity_0004**：名义采样间隔 300 秒；登记了蒸汽加湿控制通道。完整测量/控制字段如下：

- `water_temperature__real_value__chiller_behind`
- `air_temperature__max__supply_air_outlet`
- `logic__real_value__fan_exahust_air`
- `relative_humidity__real_value__supply_air_outlet`
- `air_temperature__required_value__exahust_air_inlet`
- `logic__required_value__valve_exahust_air_outlet`
- `signal__required_value__fan_exahust_air`
- `signal__required_value__fan_fresh_air`
- `logic__required_value__heater`
- `logic__required_value__valve_outdoor_air`
- `relative_humidity__required_value__supply_air_outlet`
- `air_temperature__min__supply_air_outlet`
- `water_temperature__required_value__chiller`
- `air_temperature__real_value__supply_air_outlet`
- `logic__real_value__fan_fresh_air`
- `logic__real_value__air_handling_unit`
- `water_temperature__real_value__heater_before`
- `signal__required_value__heater_valve`
- `logic__real_value__filter_outdoor_air`
- `logic__required_value__chiller_pump`
- `water_temperature__real_value__heater_behind`
- `signal__required_value__chiller_valve`
- `logic__real_value__filter_exahust_air`
- `pressure_dif__real_value__fan_fresh_air`
- `air_temperature__real_value__exahust_air_inlet`
- `signal__required_value__heat_recovery_bypass`
- `logic__required_value__heater_pump`
- `signal__required_value__steam_humidifier`

[H05-entity_0005] **entity_0005**：名义采样间隔 300 秒；未登记蒸汽加湿控制通道。完整测量/控制字段如下：

- `signal__required_value__heater_valve`
- `air_temperature__required_value__exahust_air_inlet`
- `air_temperature__real_value__supply_air_outlet`
- `water_temperature__real_value__chiller_behind`
- `signal__required_value__chiller_valve`
- `logic__real_value__air_handling_unit`
- `air_temperature__min__supply_air_outlet`
- `logic__required_value__heater`
- `logic__real_value__fan_exahust_air`
- `signal__required_value__heat_recovery_bypass`
- `signal__required_value__fan_fresh_air`
- `logic__required_value__valve_outdoor_air`
- `pressure_dif__real_value__fan_fresh_air`
- `logic__required_value__valve_exahust_air_outlet`
- `water_temperature__real_value__heater_behind`
- `logic__required_value__chiller_pump`
- `signal__required_value__fan_exahust_air`
- `air_temperature__real_value__exahust_air_inlet`
- `logic__required_value__chiller`
- `logic__required_value__heater_pump`
- `logic__real_value__fan_fresh_air`
- `air_temperature__max__supply_air_outlet`
- `water_temperature__required_value__heater`
- `water_temperature__real_value__heater_before`

[H05-entity_0006] **entity_0006**：名义采样间隔 300 秒；未登记蒸汽加湿控制通道。完整测量/控制字段如下：

- `water_temperature__required_value__heater`
- `air_temperature__real_value__exahust_air_inlet`
- `air_temperature__real_value__supply_air_outlet`
- `logic__required_value__valve_exahust_air_outlet`
- `air_temperature__required_value__exahust_air_inlet`
- `logic__required_value__heater_pump`
- `signal__required_value__fan_fresh_air`
- `logic__real_value__filter_outdoor_air`
- `signal__required_value__heater_valve`
- `air_temperature__min__supply_air_outlet`
- `logic__real_value__air_handling_unit`
- `air_temperature__max__supply_air_outlet`
- `water_temperature__real_value__heater_behind`
- `logic__required_value__chiller_pump`
- `pressure_dif__real_value__supply_air_outlet`
- `logic__required_value__valve_outdoor_air`
- `logic__required_value__chiller`
- `logic__real_value__fan_fresh_air`
- `signal__required_value__fan_exahust_air`
- `logic__real_value__filter_exahust_air`
- `logic__required_value__heater`
- `water_temperature__real_value__chiller_behind`
- `signal__required_value__chiller_valve`
- `water_temperature__real_value__heater_before`
- `logic__real_value__fan_exahust_air`
- `signal__required_value__heat_recovery_bypass`
