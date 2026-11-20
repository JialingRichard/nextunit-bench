# 风力发电机组：设备、测量和工况

共有三种场站测量配置。配置 site_1 来自葡萄牙陆上风电场，site_2 和 site_3 来自德国海上风电场。机组、传感器和时间经过匿名化；额定功率与机组型号没有公开。原始功率及无功功率按机组额定功率缩放，不能直接据表中名义功率单位推回原始功率。

测量通常按十分钟汇总，包括平均值以及部分传感器的最小值、最大值和标准差。原始值未做统一缺失处理、数值校验或归一化，提供的数值可能缺失或不符合物理关系。特征名后缀 avg/min/max/std 分别对应上述统计量；无后缀列按来源描述解释。

来源的状态标记在配置 site_1 中由事后故障日志构建，在 site_2/site_3 中来自运营者记录的状态代码。这些状态标记均不作为本任务输入，历史与观察段只保留测量，历史段不保证全为正常。这两种来源并不完全等价。运营者记录为正常的时段也可能包含事后确认的异常征兆。事件正常/异常标注在前一配置中依据故障记录，在后两种配置中依据运营者反馈和服务报告。

不同观察记录的日期独立平移，不能把日期当成跨记录统一日历。记录中保留相对时间、采样间隔及匿名日历的年内日序。来源没有提供所有传感器的精度、校准系数和故障机理参数。

来源报告了以下测量质量问题，数据按原样保留：某些最小值大于平均值，某些最大值小于平均值，某些标准差超过同记录最小/最大/平均值可支持的范围，另有最小/最大/标准差全部为零的传感器。平均值整体上较为合理，但这不是逐值有效性保证。

配置 site_1 中，电网无功功率的最小/最大/标准差有明显不一致；桨距角的异常可能与角度环绕有关。其他传感器这些统计量的不合理比例通常低于5%。配置 site_2 中 sensor_0、sensor_1、sensor_2、sensor_3、sensor_5、sensor_9 的最小/最大/标准差均为零；sensor_6、sensor_54、sensor_55、sensor_56、wind_speed_60 的上述不一致约涉及5%的记录；其余具有这些统计量的特征往往有超过50%的不一致，部分接近全部记录。

配置 site_3 中，sensor_11、sensor_15、sensor_40、sensor_61、sensor_62、sensor_63、sensor_64、sensor_74、sensor_194、sensor_195、sensor_197、sensor_198、sensor_205、sensor_206、sensor_207、sensor_217、sensor_218 的上述统计量不一致约涉及20%至30%的记录。其他传感器的污染程度不一。sensor_40 与 sensor_61 的单位在来源修订中从 bar 更正为 hPa。

以下逐项转录公开传感器说明，包括不明确与编码损坏的单位。符号 � 是来源文件已有的不可恢复字符，这些单位的缺损部分未获确认。angle/counter 是来源给定的角度量/累积量指示，并未独立核验。

配置 site_3 中，来源列出的以下90个传感器，其最小/最大/标准差上述不一致约涉及10%至15%的记录：power_5、power_6、sensor_7、sensor_9、sensor_10、sensor_12、sensor_13、sensor_14、sensor_18、sensor_19、sensor_20、sensor_21、sensor_23、sensor_24、sensor_26、sensor_39、sensor_41、sensor_44、sensor_45、sensor_65、sensor_71、sensor_72、sensor_73、sensor_77、sensor_78、sensor_79、sensor_80、sensor_87、sensor_88、sensor_89、sensor_95、sensor_96、sensor_104、sensor_105、sensor_106、sensor_149、sensor_150、sensor_151、sensor_152、sensor_153、sensor_154、sensor_155、sensor_156、sensor_157、sensor_158、sensor_159、sensor_160、sensor_161、sensor_162、sensor_163、sensor_164、sensor_165、sensor_166、sensor_167、sensor_168、sensor_169、sensor_170、sensor_171、sensor_176、sensor_178、sensor_179、sensor_180、sensor_181、sensor_182、sensor_183、sensor_184、sensor_185、sensor_186、sensor_187、sensor_188、sensor_189、sensor_190、sensor_191、sensor_192、sensor_193、sensor_196、sensor_199、sensor_200、sensor_201、sensor_202、sensor_203、sensor_204、sensor_210、sensor_212、sensor_213、sensor_225、sensor_231、sensor_232、sensor_233、sensor_234。

配置 site_3 中，来源列出的以下131个传感器，其上述统计量不一致比例低于5%：sensor_0、sensor_1、power_2、sensor_3、sensor_4、sensor_8、sensor_16、power_17、sensor_22、sensor_25、sensor_27、sensor_28、sensor_29、sensor_30、sensor_31、sensor_32、sensor_33、sensor_34、sensor_35、sensor_36、sensor_37、sensor_38、sensor_42、sensor_43、sensor_46、sensor_47、sensor_48、sensor_49、sensor_50、sensor_51、sensor_52、sensor_53、sensor_54、sensor_55、sensor_56、sensor_57、sensor_58、sensor_59、sensor_60、sensor_66、sensor_67、sensor_68、sensor_69、sensor_70、sensor_75、sensor_76、sensor_81、sensor_82、sensor_83、sensor_84、sensor_85、sensor_86、sensor_90、sensor_91、sensor_92、sensor_93、sensor_94、sensor_97、sensor_98、sensor_99、sensor_100、sensor_101、sensor_102、sensor_103、sensor_108、sensor_107、sensor_109、sensor_110、sensor_111、sensor_112、sensor_113、sensor_114、sensor_115、sensor_116、sensor_117、sensor_118、reactive_power_119、reactive_power_120、reactive_power_121、reactive_power_122、sensor_123、sensor_124、sensor_125、sensor_126、sensor_127、sensor_128、sensor_129、sensor_130、sensor_131、sensor_132、sensor_133、sensor_134、sensor_135、sensor_136、sensor_137、sensor_138、sensor_139、sensor_140、sensor_141、sensor_142、sensor_143、sensor_144、sensor_145、sensor_146、sensor_147、sensor_148、sensor_172、sensor_173、sensor_174、sensor_175、sensor_177、sensor_208、sensor_209、sensor_211、sensor_214、sensor_215、sensor_216、sensor_219、sensor_220、sensor_221、sensor_222、sensor_223、sensor_224、sensor_226、sensor_227、sensor_228、sensor_229、sensor_230、wind_speed_236、wind_speed_235、wind_speed_237。这些比例指该配置跨事件的平均受影响比例，不是逐值质量标记。

## site_1 的传感器说明

| sensor | statistics | description | unit | angle | counter |
| --- | --- | --- | --- | --- | --- |
| sensor_0 | average | Ambient temperature | �C | False | False |
| sensor_1 | average | Wind absolute direction | � | True | False |
| sensor_2 | average | Wind relative direction | � | True | False |
| wind_speed_3 | maximum,minimum,average,std_dev | Windspeed | m/s | False | False |
| wind_speed_4 | average | Estimated windspeed | m/s | False | False |
| sensor_5 | maximum,minimum,std_dev,average | Pitch angle | � | True | False |
| sensor_6 | average | Temperature in the hub controller | �C | False | False |
| sensor_7 | average | Temperature in the top nacelle controller | �C | False | False |
| sensor_8 | average | Temperature in the choke coils on the VCS-section | �C | False | False |
| sensor_9 | average | Temperature on the VCP-board | �C | False | False |
| sensor_10 | average | Temperature in the VCS cooling water | �C | False | False |
| sensor_11 | average | Temperature in gearbox bearing on high speed shaft | �C | False | False |
| sensor_12 | average | Temperature oil in gearbox | �C | False | False |
| sensor_13 | average | Temperature in generator bearing 2 (Drive End) | �C | False | False |
| sensor_14 | average | Temperature in generator bearing 1 (Non-Drive End) | �C | False | False |
| sensor_15 | average | Temperature inside generator in stator windings phase 1 | �C | False | False |
| sensor_16 | average | Temperature inside generator in stator windings phase 2 | �C | False | False |
| sensor_17 | average | Temperature inside generator in stator windings phase 3 | �C | False | False |
| sensor_18 | maximum,minimum,average,std_dev | Generator rpm in latest period | rpm | False | False |
| sensor_19 | average | Temperature in the split ring chamber | �C | False | False |
| sensor_20 | average | Temperature in the busbar section | �C | False | False |
| sensor_21 | average | Temperature measured by the IGBT-driver on the grid side inverter | �C | False | False |
| sensor_22 | average | Actual phase displacement |  | False | False |
| sensor_23 | average | Averaged current in phase 1 | A | False | False |
| sensor_24 | average | Averaged current in phase 2 | A | False | False |
| sensor_25 | average | Averaged current in phase 3 | A | False | False |
| sensor_26 | average | Grid frequency | Hz | False | False |
| reactive_power_27 | average,maximum,minimum,std_dev | Possible grid capacitive reactive power | kVAr | False | False |
| reactive_power_28 | average,maximum,minimum,std_dev | Possible grid inductive reactive power | kVAr | False | False |
| power_29 | maximum,std_dev,average,minimum | Possible grid active power | kW | False | False |
| power_30 | maximum,std_dev,minimum,average | Grid power | kW | False | False |
| sensor_31 | average,maximum,minimum,std_dev | Grid reactive power | kVAr | False | False |
| sensor_32 | average | Averaged voltage in phase 1 | V | False | False |
| sensor_33 | average | Averaged voltage in phase 2 | V | False | False |
| sensor_34 | average | Averaged voltage in phase 3 | V | False | False |
| sensor_35 | average | Temperature measured by the IGBT-driver on the rotor side inverter phase1 | �C | False | False |
| sensor_36 | average | Temperature measured by the IGBT-driver on the rotor side inverter phase2 | �C | False | False |
| sensor_37 | average | Temperature measured by the IGBT-driver on the rotor side inverter phase3 | �C | False | False |
| sensor_38 | average | Temperature in HV transformer phase L1 | �C | False | False |
| sensor_39 | average | Temperature in HV transformer phase L2 | �C | False | False |
| sensor_40 | average | Temperature in HV transformer phase L3 | �C | False | False |
| sensor_41 | average | Temperature oil in hydraulic group | �C | False | False |
| sensor_42 | average | Nacelle direction | � | True | False |
| sensor_43 | average | Nacelle temperature | �C | False | False |
| sensor_44 | average | Active power - generator disconnected | Wh | False | False |
| sensor_45 | average | Active power - generator connected in delta | Wh | False | False |
| sensor_46 | average | Active power - generator connected in star | Wh | False | False |
| sensor_47 | average | Reactive power - generator disconnected | VArh | False | False |
| sensor_48 | average | Reactive power - generator connected in delta | VArh | False | False |
| sensor_49 | average | Reactive power - generator connected in star | VArh | False | False |
| sensor_50 | average | Total active power | Wh | False | False |
| sensor_51 | average | Total reactive power | VArh | False | False |
| sensor_52 | minimum,average,std_dev,maximum | Rotor rpm | rpm | False | False |
| sensor_53 | average | Temperature in the nose cone | �C | False | False |

## site_2 的传感器说明

| sensor | statistics | description | unit | angle | counter |
| --- | --- | --- | --- | --- | --- |
| sensor_0 | maximum,minimum,average,std_dev | Total negative reactive power | kvarh | False | True |
| sensor_1 | maximum,std_dev,average,minimum | Total negative active power | kWh | False | True |
| sensor_2 | average,minimum,maximum,std_dev | Total positive reactive power | kvarh | False | True |
| sensor_3 | maximum,std_dev,minimum,average | Total positive active power | kWh | False | True |
| sensor_4 | average,maximum,minimum,std_dev | Absolute wind direction | � | True | False |
| sensor_5 | average,maximum,std_dev,minimum | Torque delta calculated | kNm | False | False |
| sensor_6 | average,minimum,std_dev,maximum | Wind speed anemometer 2 calculated | m/s | False | False |
| sensor_7 | std_dev,maximum,minimum,average | Cable load | % | False | False |
| sensor_8 | maximum,average,minimum,std_dev | Outside temperature | �C | False | False |
| sensor_9 | average,minimum,maximum,std_dev | Estimated tower natural frequency | mHz | False | False |
| sensor_10 | maximum,std_dev,average,minimum | Pitch angle | � | True | False |
| reactive_power_11 | average,std_dev,maximum,minimum | Reactive power | kvar | False | False |
| sensor_12 | average,maximum,std_dev,minimum | Torque estimated | Nm | False | False |
| sensor_13 | std_dev,average,maximum,minimum | RMS voltage L1 | V | False | False |
| sensor_14 | maximum,std_dev,average,minimum | RMS voltage L2 | V | False | False |
| sensor_15 | average,std_dev,maximum,minimum | RMS voltage L3 | V | False | False |
| sensor_16 | maximum,minimum,average,std_dev | RMS current L1 | A | False | False |
| sensor_17 | average,maximum,minimum,std_dev | RMS current L2 | A | False | False |
| sensor_18 | average,minimum,std_dev,maximum | RMS current L3 | A | False | False |
| sensor_19 | maximum,minimum,average,std_dev | Generator converter rotational peed | rpm | False | False |
| sensor_20 | std_dev,maximum,minimum,average | Gearbox rotational speed | rpm | False | False |
| sensor_21 | minimum,maximum,std_dev,average | Nacelle direction | � | True | False |
| sensor_22 | std_dev,maximum,minimum,average | Hub temperature | �C | False | False |
| sensor_23 | minimum,average,maximum,std_dev | Grid frequency | Hz | False | False |
| sensor_24 | average,maximum,minimum,std_dev | Grid voltage | V | False | False |
| sensor_25 | average,maximum,minimum,std_dev | Rotor speed | rpm | False | False |
| sensor_26 | minimum,std_dev,average,maximum | Apparent power | kVA | False | False |
| sensor_27 | maximum,minimum,std_dev,average | Current | A | False | False |
| sensor_28 | std_dev,minimum,average,maximum | Motor current axis 1 | A | False | False |
| sensor_29 | average,minimum,std_dev,maximum | Motor current axis 2 | A | False | False |
| sensor_30 | maximum,std_dev,minimum,average | Motor current axis 3 | A | False | False |
| sensor_31 | average,minimum,std_dev,maximum | Temperature internal consumption transformer | �C | False | False |
| sensor_32 | average,maximum,minimum,std_dev | Generator bearing temperature 1 | �C | False | False |
| sensor_33 | average,maximum,minimum,std_dev | Generator bearing temperature 2 | �C | False | False |
| sensor_34 | average,maximum,std_dev,minimum | Gearbox bearing temperature 1 | �C | False | False |
| sensor_35 | minimum,std_dev,average,maximum | Gearbox bearing temperature 2 | �C | False | False |
| sensor_36 | minimum,std_dev,maximum,average | Gearbox bearing temperature 3 | �C | False | False |
| sensor_37 | minimum,maximum,std_dev,average | Gearbox bearing temperature 4 | �C | False | False |
| sensor_38 | maximum,minimum,std_dev,average | Gearbox oil inlet temperature | �C | False | False |
| sensor_39 | average,maximum,minimum,std_dev | Gearbox oil tank temperature | �C | False | False |
| sensor_40 | minimum,std_dev,average,maximum | Transformator core temperature | �C | False | False |
| sensor_41 | average,std_dev,maximum,minimum | Transformer L1 (mid-voltage) temperature  | �C | False | False |
| sensor_42 | maximum,minimum,std_dev,average | Transformer L1 (undervoltage) temperature  | �C | False | False |
| sensor_43 | maximum,average,minimum,std_dev | Transformer L2 (mid-voltage) temperature  | �C | False | False |
| sensor_44 | maximum,average,minimum,std_dev | Transformer L2 (undervoltage) temperature  | �C | False | False |
| sensor_45 | average,maximum,minimum,std_dev | Transformer L3 (mid-voltage) temperature  | �C | False | False |
| sensor_46 | std_dev,average,maximum,minimum | Transformer L3 (undervoltage) temperature  | �C | False | False |
| sensor_47 | maximum,minimum,std_dev,average | Transformer cell temperature | �C | False | False |
| sensor_48 | maximum,std_dev,average,minimum | Motor temperature axis 1 | �C | False | False |
| sensor_49 | average,minimum,maximum,std_dev | Motor temperature axis 2 | �C | False | False |
| sensor_50 | std_dev,maximum,minimum,average | Motor temperature axis 3 | �C | False | False |
| sensor_51 | average,std_dev,maximum,minimum | Rotor bearing temperature 1 | �C | False | False |
| sensor_52 | maximum,minimum,std_dev,average | Rotor bearing temperature 2 | �C | False | False |
| sensor_53 | maximum,minimum,average,std_dev | Slip ring temperature Generator | �C | False | False |
| sensor_54 | maximum,minimum,std_dev,average | Drive train vibration axis Z | mG | False | False |
| sensor_55 | average,maximum,minimum,std_dev | Tower vibration axis X | mG | False | False |
| sensor_56 | maximum,minimum,average,std_dev | Tower vibration axis Y | mG | False | False |
| sensor_57 | average,std_dev,maximum,minimum | Inverter torque | Nm | False | False |
| power_58 | maximum,minimum,average,std_dev | Available power | kW | False | False |
| wind_speed_59 | average,maximum,minimum,std_dev | Wind speed 1 | m/s | False | False |
| wind_speed_60 | average,minimum,maximum,std_dev | Wind speed 2 | m/s | False | False |
| wind_speed_61 | minimum,average,maximum,std_dev | Wind speed | m/s | False | False |
| power_62 | minimum,std_dev,maximum,average | Active power | kW | False | False |

## site_3 的传感器说明

| sensor | statistics | description | unit | angle | counter |
| --- | --- | --- | --- | --- | --- |
| sensor_0 | maximum,minimum,std_dev,average | ABB-LS Input K1, IL1 | A | False | False |
| sensor_1 | maximum,minimum,std_dev,average | Generator acceleration | rpm/s | False | False |
| power_2 | average,maximum,std_dev,minimum | ABB-LS Active Power | kW | False | False |
| sensor_3 | average,maximum,minimum,std_dev | Active power aeration motor A | % | False | False |
| sensor_4 | average,maximum,minimum,std_dev | Active power aeration motor B | % | False | False |
| power_5 | average,maximum,minimum,std_dev | Active power grid side converter | kW | False | False |
| power_6 | average,maximum,minimum,std_dev | Active power HV grid | kW | False | False |
| sensor_7 | average,maximum,minimum,std_dev | Ambient temperature | Celsius | False | False |
| sensor_8 | average,maximum,minimum,std_dev | Generator angle speed | rad/s | False | False |
| sensor_9 | average,maximum,minimum,std_dev | Battery charge 1 | A | False | False |
| sensor_10 | average,maximum,minimum,std_dev | Battery charge 2 | A | False | False |
| sensor_11 | average,maximum,minimum,std_dev | Battery charge 3 | A | False | False |
| sensor_12 | average,maximum,minimum,std_dev | Battery discharge current axis 1 | A | False | False |
| sensor_13 | average,maximum,minimum,std_dev | Battery discharge current axis 2 | A | False | False |
| sensor_14 | average,minimum,std_dev,maximum | Battery discharge current axis 3 | A | False | False |
| sensor_15 | average,maximum,minimum,std_dev | Board temperature | Celsius | False | False |
| sensor_16 | average,maximum,minimum,std_dev | Compensation angle I/U converter | deg | True | False |
| power_17 | average,minimum,std_dev,maximum | Active power converter | kW | False | False |
| sensor_18 | average,maximum,minimum,std_dev | Generator cooling air temperature A | Celsius | False | False |
| sensor_19 | average,maximum,minimum,std_dev | Generator cooling air temperature B | Celsius | False | False |
| sensor_20 | average,maximum,minimum,std_dev | Generator cooling air temperature C | Celsius | False | False |
| sensor_21 | average,maximum,std_dev,minimum | Generator cooling air temperature D | Celsius | False | False |
| sensor_22 | average,maximum,minimum,std_dev | Current hydraulic tank heating | A | False | False |
| sensor_23 | average,maximum,minimum,std_dev | Current water cooler pump 1 | A | False | False |
| sensor_24 | average,maximum,minimum,std_dev | Current water cooler pump 2 | A | False | False |
| sensor_25 | average,maximum,minimum,std_dev | Current drain 24V nacelle | A | False | False |
| sensor_26 | std_dev,minimum,average,maximum | Current drain pitch L1 | A | False | False |
| sensor_27 | average,std_dev,maximum,minimum | Current yaw motor A | A | False | False |
| sensor_28 | average,maximum,minimum,std_dev | Current yaw motor B | A | False | False |
| sensor_29 | average,maximum,minimum,std_dev | Current yaw motor C | A | False | False |
| sensor_30 | average,maximum,std_dev,minimum | Current yaw motor D | A | False | False |
| sensor_31 | average,maximum,minimum,std_dev | Current yaw motor E | A | False | False |
| sensor_32 | average,maximum,minimum,std_dev | Current yaw motor F | A | False | False |
| sensor_33 | average,maximum,minimum,std_dev | Current yaw motor G | A | False | False |
| sensor_34 | average,minimum,std_dev,maximum | Current yaw motor H | A | False | False |
| sensor_35 | maximum,std_dev,average,minimum | DC link voltage converter | V | False | False |
| sensor_36 | average,minimum,std_dev,maximum | Direct current link volt axis 1 | V | False | False |
| sensor_37 | average,minimum,std_dev,maximum | Direct current link volt axis 2 | V | False | False |
| sensor_38 | average,maximum,minimum,std_dev | Direct current link volt axis 3 | V | False | False |
| sensor_39 | average,maximum,minimum,std_dev | Electrical cabinet ambient temperature | Celsius | False | False |
| sensor_40 | average,maximum,minimum,std_dev | Nacelle external air pressure | hPa | False | False |
| sensor_41 | average,maximum,minimum,std_dev | Nacelle outside temperature | Celsius | False | False |
| sensor_42 | average,maximum,minimum,std_dev | Rotor bearing flow rate | L/min | False | False |
| sensor_43 | average,maximum,minimum,std_dev | Flow meter stator cooler | l/h | False | False |
| sensor_44 | average,maximum,minimum,std_dev | Fluid level oil container A1 | % | False | False |
| sensor_45 | maximum,minimum,std_dev,average | Fluid level oil container A2 | % | False | False |
| sensor_46 | average,maximum,minimum,std_dev | Water temperature flow TT1 | Celsius | False | False |
| sensor_47 | average,maximum,minimum,std_dev | Mains frequency OS-side | Hz | False | False |
| sensor_48 | average,maximum,minimum,std_dev | Hydraulic pressure Aggregate System pressure | bar | False | False |
| sensor_49 | average,minimum,maximum,std_dev | Hydraulic pressure azimuth circuit A | bar | False | False |
| sensor_50 | average,minimum,std_dev,maximum | Hydraulic pressure azimuth circuit B | bar | False | False |
| sensor_51 | average,maximum,minimum,std_dev | Hydraulic pressure azimuth memory A | bar | False | False |
| sensor_52 | maximum,minimum,std_dev,average | Hydraulic pressure azimuth memory B | bar | False | False |
| sensor_53 | average,minimum,std_dev,maximum | Hydraulic pressure locking memory  | bar | False | False |
| sensor_54 | average,maximum,minimum,std_dev | Hydraulic pressure rotor brake B | bar | False | False |
| sensor_55 | average,maximum,minimum,std_dev | Hydraulic pressure rotor brake A | bar | False | False |
| sensor_56 | average,maximum,minimum,std_dev | ABB-LS Input K1, IL2 | A | False | False |
| sensor_57 | average,maximum,minimum,std_dev | ABB-LS Input K1, IL3 | A | False | False |
| sensor_58 | average,maximum,minimum,std_dev | ABB-LS Input K4, UL1 | V | False | False |
| sensor_59 | average,maximum,minimum,std_dev | ABB-LS Input K4, UL2 | V | False | False |
| sensor_60 | average,maximum,minimum,std_dev | ABB-LS Input K4, UL3 | V | False | False |
| sensor_61 | average,maximum,std_dev,minimum | Nacelle air pressure | hPa | False | False |
| sensor_62 | maximum,std_dev,average,minimum | Temperature Axis 1 | Celsius | False | False |
| sensor_63 | average,maximum,std_dev,minimum | Temperature Axis 2 | Celsius | False | False |
| sensor_64 | maximum,std_dev,minimum,average | Temperature Axis 3 | Celsius | False | False |
| sensor_65 | maximum,std_dev,minimum,average | Hub temperature | Celsius | False | False |
| sensor_66 | average,maximum,std_dev,minimum | Internal consumption current L1 | A | False | False |
| sensor_67 | average,maximum,minimum,std_dev | Internal consumption current L2 | A | False | False |
| sensor_68 | average,maximum,std_dev,minimum | Internal consumption current L3 | A | False | False |
| sensor_69 | average,maximum,minimum,std_dev | Internal consumption power L2 | kW | False | False |
| sensor_70 | average,maximum,std_dev,minimum | Internal consumption power L3 | kW | False | False |
| sensor_71 | average,maximum,std_dev,minimum | Internal consumption voltage L1 | V | False | False |
| sensor_72 | average,maximum,std_dev,minimum | Internal consumption voltage L2 | V | False | False |
| sensor_73 | average,maximum,std_dev,minimum | Internal consumption voltage L3 | V | False | False |
| sensor_74 | average,maximum,std_dev,minimum | Hydraulic oil tank level | L | False | False |
| sensor_75 | average,maximum,std_dev,minimum | Maximum reactive power HV converter | kvar | False | False |
| sensor_76 | average,maximum,std_dev,minimum | Min pitch angle | deg | True | False |
| sensor_77 | average,maximum,std_dev,minimum | Motor current generator cooler 1 | A | False | False |
| sensor_78 | average,maximum,minimum,std_dev | Motor current generator cooler 2 | A | False | False |
| sensor_79 | average,maximum,minimum,std_dev | Motor current generator cooler 3 | A | False | False |
| sensor_80 | average,maximum,minimum,std_dev | Motor current generator cooler 4 | A | False | False |
| sensor_81 | average,maximum,minimum,std_dev | Motor current hydraulic pump A | A | False | False |
| sensor_82 | average,maximum,minimum,std_dev | Motor current hydraulic pump B | A | False | False |
| sensor_83 | average,maximum,minimum,std_dev | Motor current water cooler fan 1 | A | False | False |
| sensor_84 | average,maximum,minimum,std_dev | Motor current water cooler fan 2 | A | False | False |
| sensor_85 | average,maximum,minimum,std_dev | Motor current water cooler fan 3 | A | False | False |
| sensor_86 | average,maximum,minimum,std_dev | Motor current water cooler fan 4 | A | False | False |
| sensor_87 | average,maximum,minimum,std_dev | Motor current gear oil pump A | A | False | False |
| sensor_88 | average,maximum,minimum,std_dev | Motor current gear oil pump B | A | False | False |
| sensor_89 | average,maximum,minimum,std_dev | Motor current gear oil pump C | A | False | False |
| sensor_90 | maximum,minimum,std_dev,average | Nacelle vibration longitudinal 1 | m/s^2 | False | False |
| sensor_91 | average,maximum,minimum,std_dev | Nacelle vibration longitudinal 2 | m/s^2 | False | False |
| sensor_92 | average,minimum,std_dev,maximum | Nacelle vibration transverse 1 | m/s^2 | False | False |
| sensor_93 | average,maximum,minimum,std_dev | Nacelle vibration transverse 2 | m/s^2 | False | False |
| sensor_94 | average,maximum,minimum,std_dev | gearbox oil level | L | False | False |
| sensor_95 | average,minimum,std_dev,maximum | Pollution indicator filter pump 1 | bar | False | False |
| sensor_96 | std_dev,average,minimum,maximum | Pollution indicator filter pump 2 | bar | False | False |
| sensor_97 | std_dev,average,maximum,minimum | Pollution indicator gearbox filter A | bar | False | False |
| sensor_98 | std_dev,average,minimum,maximum | Pollution indicator gearbox filter B | bar | False | False |
| sensor_99 | average,std_dev,maximum,minimum | Pollution indicator gearbox filter C | bar | False | False |
| sensor_100 | average,minimum,std_dev,maximum | Position motor axis 1 | deg | True | False |
| sensor_101 | average,minimum,maximum,std_dev | Position motor axis 2 | deg | True | False |
| sensor_102 | average,std_dev,minimum,maximum | Position motor axis 3 | deg | True | False |
| sensor_103 | maximum,std_dev,average,minimum | Position rotor blade axis 1 | deg | True | False |
| sensor_104 | average,maximum,std_dev,minimum | Position rotor blade axis 2 | deg | True | False |
| sensor_105 | average,maximum,std_dev,minimum | Position rotor blade axis 3 | deg | True | False |
| sensor_106 | average,maximum,minimum,std_dev | RM position bypass valve gearbox radiator | % | False | False |
| sensor_107 | average,maximum,minimum,std_dev | Internal consumption | kW | False | False |
| sensor_108 | average,maximum,minimum,std_dev | Internal consumption power L1 | kW | False | False |
| sensor_109 | average,maximum,minimum,std_dev | Pressure difference aeration 1st filter stage 1 | Pa | False | False |
| sensor_110 | average,maximum,minimum,std_dev | Pressure difference aeration 1st filter stage 2 | Pa | False | False |
| sensor_111 | average,maximum,minimum,std_dev | Pressure difference aeration 2nd filter stage A 1 | Pa | False | False |
| sensor_112 | average,maximum,minimum,std_dev | Pressure difference aeration 2nd filter stage A 2 | Pa | False | False |
| sensor_113 | average,maximum,minimum,std_dev | Pressure difference aeration 2nd filter stage B 1 | Pa | False | False |
| sensor_114 | average,maximum,minimum,std_dev | Pressure difference aeration 2nd filter stage B 2 | Pa | False | False |
| sensor_115 | average,maximum,minimum,std_dev | Pressure difference spinner 1 | Pa | False | False |
| sensor_116 | average,maximum,minimum,std_dev | Pressure difference spinner 2 | Pa | False | False |
| sensor_117 | average,minimum,std_dev,maximum | Gearbox oil pressure input 1 | bar | False | False |
| sensor_118 | average,maximum,std_dev,minimum | Gearbox oil pressure input 2 | bar | False | False |
| reactive_power_119 | maximum,minimum,std_dev,average | ABB-LS Reactive Power | kvar | False | False |
| reactive_power_120 | average,std_dev,maximum,minimum | Reactive power converter | kvar | False | False |
| reactive_power_121 | maximum,std_dev,average,minimum | Reactive power GS converter | kvar | False | False |
| reactive_power_122 | maximum,std_dev,average,minimum | Reactive power HV grid | kvar | False | False |
| sensor_123 | maximum,average,std_dev,minimum | Relative wind direction 1+2 | deg | True | False |
| sensor_124 | average,std_dev,minimum,maximum | Relative wind direction Yaw | deg | True | False |
| sensor_125 | average,minimum,std_dev,maximum | Relative wind direction 1 | deg | True | False |
| sensor_126 | average,std_dev,minimum,maximum | Relative wind direction 2 | deg | True | False |
| sensor_127 | average,maximum,minimum,std_dev | RMS current phase 1 HV grid | A | False | False |
| sensor_128 | average,maximum,minimum,std_dev | RMS current phase 2 HV grid | A | False | False |
| sensor_129 | average,maximum,std_dev,minimum | RMS current phase 3 HV grid | A | False | False |
| sensor_130 | average,maximum,std_dev,minimum | Generator RMS current L1 | A | False | False |
| sensor_131 | average,maximum,minimum,std_dev | Generator RMS current L2 | A | False | False |
| sensor_132 | maximum,minimum,std_dev,average | Generator RMS current L3 | A | False | False |
| sensor_133 | average,maximum,minimum,std_dev | RMS line to line current axis 1 | A | False | False |
| sensor_134 | average,maximum,minimum,std_dev | RMS line to line current axis 2 | A | False | False |
| sensor_135 | maximum,average,minimum,std_dev | RMS line to line current axis 3 | A | False | False |
| sensor_136 | average,minimum,maximum,std_dev | Generator RMS voltage L1-L2 | V | False | False |
| sensor_137 | average,maximum,std_dev,minimum | Generator RMS voltage L2-L3 | V | False | False |
| sensor_138 | average,maximum,minimum,std_dev | Generator RMS voltage L3-L1 | V | False | False |
| sensor_139 | maximum,std_dev,minimum,average | RMS voltage phase 1 HV grid | V | False | False |
| sensor_140 | average,maximum,minimum,std_dev | RMS voltage phase 2 HV grid | V | False | False |
| sensor_141 | average,maximum,minimum,std_dev | RMS voltage phase 3 HV grid | V | False | False |
| sensor_142 | average,maximum,minimum,std_dev | Rotational speed aerator A | Hz | False | False |
| sensor_143 | average,maximum,minimum,std_dev | Rotational speed aerator B | Hz | False | False |
| sensor_144 | average,maximum,minimum,std_dev | Rotor speed 1 | 1/min | False | False |
| sensor_145 | average,maximum,minimum,std_dev | Rotor speed 2 | 1/min | False | False |
| sensor_146 | minimum,std_dev,maximum,average | Rotor speed gearbox main shaft 1 | 1/min | False | False |
| sensor_147 | maximum,minimum,std_dev,average | Rotor speed gearbox main shaft 2 | 1/min | False | False |
| sensor_148 | maximum,minimum,std_dev,average | RPM motor axis 1 | 1/min | False | False |
| sensor_149 | maximum,minimum,std_dev,average | RPM motor axis 2 | 1/min | False | False |
| sensor_150 | minimum,std_dev,maximum,average | RPM motor axis 3 | 1/min | False | False |
| sensor_151 | maximum,minimum,std_dev,average | Temperature 1 planetary bearing A1 | Celsius | False | False |
| sensor_152 | average,maximum,minimum,std_dev | Temperature 1 planetary bearing A2 | Celsius | False | False |
| sensor_153 | average,maximum,minimum,std_dev | Temperature 1 planetary bearing B1 | Celsius | False | False |
| sensor_154 | average,maximum,std_dev,minimum | Temperature 1 planetary bearing B2 | Celsius | False | False |
| sensor_155 | maximum,minimum,std_dev,average | Temperature 1 planetary bearing C1 | Celsius | False | False |
| sensor_156 | average,maximum,minimum,std_dev | Temperature 1 planetary bearing C2 | Celsius | False | False |
| sensor_157 | average,maximum,minimum,std_dev | Temperature 1 planetary bearing D1 | Celsius | False | False |
| sensor_158 | average,minimum,std_dev,maximum | Temperature 1 planetary bearing D2 | Celsius | False | False |
| sensor_159 | average,maximum,minimum,std_dev | Temperature 2 planetary bearing A1 | Celsius | False | False |
| sensor_160 | average,maximum,minimum,std_dev | Temperature 2 planetary bearing A2 | Celsius | False | False |
| sensor_161 | average,maximum,minimum,std_dev | Temperature 2 planetary bearing B1 | Celsius | False | False |
| sensor_162 | average,maximum,minimum,std_dev | Temperature 2 planetary bearing B2 | Celsius | False | False |
| sensor_163 | maximum,minimum,average,std_dev | Temperature 2 planetary bearing C1 | Celsius | False | False |
| sensor_164 | average,maximum,minimum,std_dev | Temperature 2 planetary bearing C2 | Celsius | False | False |
| sensor_165 | average,maximum,std_dev,minimum | Temperature 2 planetary bearing D1 | Celsius | False | False |
| sensor_166 | average,maximum,minimum,std_dev | Temperature 2 planetary bearing D2 | Celsius | False | False |
| sensor_167 | average,std_dev,minimum,maximum | Air temp. transformer container | Celsius | False | False |
| sensor_168 | maximum,std_dev,minimum,average | Temperature of axial bearing 1 | Celsius | False | False |
| sensor_169 | average,maximum,minimum,std_dev | Temperature of axial bearing 2 | Celsius | False | False |
| sensor_170 | average,maximum,std_dev,minimum | Control box temperature | Celsius | False | False |
| sensor_171 | average,maximum,std_dev,minimum | Temperature converter room | Celsius | False | False |
| sensor_172 | average,maximum,std_dev,minimum | Converter cabinet temperature | Celsius | False | False |
| sensor_173 | maximum,average,std_dev,minimum | Generator temperature 1 cooling air inlet | Celsius | False | False |
| sensor_174 | minimum,std_dev,average,maximum | Generator temperature 2 cooling air inlet | Celsius | False | False |
| sensor_175 | average,minimum,std_dev,maximum | Axis 3 cooling element temperature | Celsius | False | False |
| sensor_176 | average,maximum,minimum,std_dev | Temperature cooling air exit | Celsius | False | False |
| sensor_177 | average,maximum,minimum,std_dev | Outside temperature | Celsius | False | False |
| sensor_178 | average,maximum,minimum,std_dev | Hydraulic oil tank temperature 1 | Celsius | False | False |
| sensor_179 | average,maximum,minimum,std_dev | Hydraulic oil tank temperature 2 | Celsius | False | False |
| sensor_180 | average,maximum,std_dev,minimum | Axis1 Motor temperature KTY84 | Celsius | False | False |
| sensor_181 | average,maximum,std_dev,minimum | Axis2 Motor temperature KTY84 | Celsius | False | False |
| sensor_182 | std_dev,average,minimum,maximum | Axis3 Motor temperature KTY84 | Celsius | False | False |
| sensor_183 | average,minimum,std_dev,maximum | Axis 1 Motor temperature PT100 | Celsius | False | False |
| sensor_184 | minimum,std_dev,average,maximum | Axis 2 Motor temperature PT100 | Celsius | False | False |
| sensor_185 | minimum,std_dev,average,maximum | Axis 3 Motor temperature PT100 | Celsius | False | False |
| sensor_186 | maximum,minimum,std_dev,average | Gearbox oil temperature 1  | Celsius | False | False |
| sensor_187 | average,maximum,minimum,std_dev | Gearbox oil temperature 2 | Celsius | False | False |
| sensor_188 | average,maximum,minimum,std_dev | Oil temperature EB transformer | Celsius | False | False |
| sensor_189 | average,maximum,minimum,std_dev | Gearbox oil inlet temperature 1 | Celsius | False | False |
| sensor_190 | average,maximum,minimum,std_dev | Gearbox oil inlet temperature 2 | Celsius | False | False |
| sensor_191 | maximum,minimum,average,std_dev | Oil temperature 1 main transformer | Celsius | False | False |
| sensor_192 | minimum,maximum,average,std_dev | Oil temperature 2 main transformer | Celsius | False | False |
| sensor_193 | maximum,minimum,std_dev,average | Temperature platform TBC200 | Celsius | False | False |
| sensor_194 | maximum,minimum,std_dev,average | Axis 1 Rotor bearing inner ring temperature | Celsius | False | False |
| sensor_195 | maximum,minimum,std_dev,average | Axis 2 Rotor bearing inner ring temperature | Celsius | False | False |
| sensor_196 | maximum,minimum,std_dev,average | Rotor bearing temperature 1 | Celsius | False | False |
| sensor_197 | maximum,minimum,std_dev,average | Rotor bearing temperature 2 | Celsius | False | False |
| sensor_198 | maximum,minimum,std_dev,average | Rotor bearing temperature 3 | Celsius | False | False |
| sensor_199 | maximum,minimum,std_dev,average | Temperature of stator winding U1 | Celsius | False | False |
| sensor_200 | maximum,minimum,average,std_dev | Temperature of stator winding U2 | Celsius | False | False |
| sensor_201 | maximum,minimum,average,std_dev | Temperature of stator winding V1 | Celsius | False | False |
| sensor_202 | average,maximum,minimum,std_dev | Temperature of stator winding V2 | Celsius | False | False |
| sensor_203 | average,minimum,maximum,std_dev | Temperature of stator winding W1 | Celsius | False | False |
| sensor_204 | average,maximum,minimum,std_dev | Temperature of stator winding W2 | Celsius | False | False |
| sensor_205 | average,minimum,std_dev,maximum | Temperature electrical cabinet  | Celsius | False | False |
| sensor_206 | average,maximum,minimum,std_dev | Temperature electrical cabinet 1 | Celsius | False | False |
| sensor_207 | average,maximum,minimum,std_dev | Temperature electrical cabinet 2 | Celsius | False | False |
| sensor_208 | minimum,std_dev,average,maximum | Axis 1 cooling element temperature | Celsius | False | False |
| sensor_209 | minimum,std_dev,maximum,average | Axis 2 cooling element temperature | Celsius | False | False |
| sensor_210 | maximum,minimum,std_dev,average | Electrical cabinet temperature 3/4 | Celsius | False | False |
| sensor_211 | maximum,minimum,average,std_dev | Trigger bypass valve gearbox | % | False | False |
| sensor_212 | maximum,std_dev,average,minimum | 24VDC power pack 1 | V | False | False |
| sensor_213 | average,maximum,minimum,std_dev | 24VDC power pack 2 | V | False | False |
| sensor_214 | maximum,average,minimum,std_dev | Axis 1 voltage 1 battery 100% | V | False | False |
| sensor_215 | maximum,average,minimum,std_dev | Axis 2 Voltage 1 battery 100% | V | False | False |
| sensor_216 | maximum,std_dev,minimum,average | Axis 3 Voltage 1 battery 100% | V | False | False |
| sensor_217 | maximum,std_dev,average,minimum | Voltage 24 VDC hub | V | False | False |
| sensor_218 | maximum,std_dev,minimum,average | Voltage 24 VDC nacelle | V | False | False |
| sensor_219 | maximum,std_dev,average,minimum | Axis 1 Voltage 2 Battery 100% | V | False | False |
| sensor_220 | maximum,std_dev,minimum,average | Axis 2 Voltage 2 Battery 100% | V | False | False |
| sensor_221 | maximum,std_dev,average,minimum | Axis 3 voltage 2 battery 100% | V | False | False |
| sensor_222 | average,maximum,minimum,std_dev | Axis 1 Voltage battery 50% | V | False | False |
| sensor_223 | average,maximum,minimum,std_dev | Axis 2 Voltage battery 50% | V | False | False |
| sensor_224 | average,maximum,minimum,std_dev | Axis 3 Voltage battery 50% | V | False | False |
| sensor_225 | average,maximum,minimum,std_dev | Water conductivity QIT1 | DL | False | False |
| sensor_226 | average,maximum,minimum,std_dev | Water pressure PT1 | bar | False | False |
| sensor_227 | average,maximum,minimum,std_dev | Water pressure PT2 | bar | False | False |
| sensor_228 | average,maximum,minimum,std_dev | Cooling water temp. generator inlet 1 | Celsius | False | False |
| sensor_229 | average,minimum,std_dev,maximum | Cooling water temp. generator inlet 2 | Celsius | False | False |
| sensor_230 | average,minimum,std_dev,maximum | Water flow | DL | False | False |
| sensor_231 | average,minimum,std_dev,maximum | Water pressure 1 cooling system | bar | False | False |
| sensor_232 | average,minimum,std_dev,maximum | Water pressure 2 cooling system | bar | False | False |
| sensor_233 | average,maximum,minimum,std_dev | Cooling water temp. generator outlet 1 | Celsius | False | False |
| sensor_234 | average,maximum,minimum,std_dev | Cooling water temp. generator outlet 2 | Celsius | False | False |
| wind_speed_235 | average,maximum,minimum,std_dev | Wind speed 1 | m/s | False | False |
| wind_speed_236 | average,maximum,minimum,std_dev | Wind speed 1+2 | m/s | False | False |
| wind_speed_237 | average,minimum,std_dev,maximum | Wind speed 2 | m/s | False | False |
