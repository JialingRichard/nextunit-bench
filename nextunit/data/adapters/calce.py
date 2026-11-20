"""CALCE CS2 and CX2 cells 33-38 (raw: CALCE_CS2/data/CS2/, CALCE_CX2/data/CX2/ from the PHMD archives CALCE_CS2.zip,
CALCE_CX2.zip, where the official spreadsheets are already converted to CSV)."""
from pathlib import Path

import numpy as np
import pandas as pd

from ._capacity import forecast_unit

RAW_DIRS = ('CALCE_CS2', 'CALCE_CX2')
COLUMNS = ['Date_Time', 'Test_Time(s)', 'Step_Index', 'Cycle_Index', 'Current(A)', 'Voltage(V)',
           'Charge_Capacity(Ah)', 'Discharge_Capacity(Ah)', 'Internal_Resistance(Ohm)']


def build(raw: Path, out: Path) -> None:
    for family, nominal in [('CS2', 1.1), ('CX2', 1.35)]:
        for cell in sorted((raw / f'CALCE_{family}/data' / family).iterdir()):
            if not cell.is_dir():
                continue
            frame = pd.concat([pd.read_csv(path, usecols=COLUMNS) for path in sorted(cell.glob('*.csv'))], ignore_index=True)
            frame['Date_Time'] = pd.to_datetime(frame['Date_Time'], format='mixed')
            frame = frame.drop_duplicates(['Date_Time', 'Test_Time(s)', 'Step_Index', 'Cycle_Index']) \
                .sort_values(['Date_Time', 'Test_Time(s)'], kind='stable').reset_index(drop=True)
            is_discharge = frame.Step_Index.eq(7)
            starts = is_discharge & (~is_discharge.shift(fill_value=False) | frame.Cycle_Index.ne(frame.Cycle_Index.shift())
                                     | frame['Test_Time(s)'].diff().lt(0))
            group_ids = starts.cumsum()
            observations, previous_end = [], -1
            for _, discharge in frame[is_discharge].groupby(group_ids[is_discharge], sort=False):
                first, last = int(discharge.index[0]), int(discharge.index[-1])
                complete = first > 0 and frame.Step_Index.iloc[first - 1] != 7 and last + 1 < len(frame) \
                    and int(frame.Step_Index.iloc[last + 1]) == 8
                # The tester's counter can accumulate over cycles: take the increment during this discharge.
                capacity = float(discharge['Discharge_Capacity(Ah)'].iloc[-1] - frame['Discharge_Capacity(Ah)'].iloc[max(first - 1, 0)])
                if not complete or len(discharge) < 2 or not np.isfinite(capacity) or capacity <= 0:
                    previous_end = last
                    continue
                segment = frame.iloc[previous_end + 1:last + 1]
                signals = {
                    'time_s': (segment.Date_Time - segment.Date_Time.iloc[0]).dt.total_seconds().to_numpy(dtype=np.float32),
                    'voltage_V': segment['Voltage(V)'].to_numpy(dtype=np.float32),
                    'current_A': segment['Current(A)'].to_numpy(dtype=np.float32),
                    'step_index': segment.Step_Index.to_numpy(dtype=np.float32),
                    'charge_capacity_Ah': segment['Charge_Capacity(Ah)'].to_numpy(dtype=np.float32),
                    'discharge_capacity_Ah': segment['Discharge_Capacity(Ah)'].to_numpy(dtype=np.float32),
                    'internal_resistance_ohm': segment['Internal_Resistance(Ohm)'].to_numpy(dtype=np.float32),
                }
                observations.append({'capacity': capacity, 'signals': signals, 'measurements': {
                    'elapsed_days': float((frame.Date_Time.iloc[last] - frame.Date_Time.iloc[0]).total_seconds() / 86400),
                    'nominal_capacity_Ah': nominal}})
                previous_end = last
            assert len(observations) > 10
            forecast_unit(out, cell.name, observations)
