"""Fixed raw inputs of the random-forest reference: one reader per dataset.

``iter_samples(dataset, inputs, unit, raw=None, selected=None)`` yields, in file order, one dict per requested record:
``record_id``, ``sequence`` (channels x length, float32), ``tabular`` (1-D float32) and, for MATWI, ``image``. Only
observations available at the request enter a sample; labels are never opened. A waveform becomes three unchanged
256-point pieces (beginning, middle, end; short signals right-padded with zeros); slow observations keep the latest
32 rows (left-padded with zeros). No spectra, statistics or learned features. These are the arrays of the paper's
fixed baseline, reproduced bit for bit.

``unit`` is the unit ID (operating conditions of CWRU, SEU, PRONOSTIA and IMS come from ``task.json``); MATWI reads its
row of the condition table in ``info.md``; AHU21 its channel list from ``info.md``. PUBD16 needs ``raw``, the raw root
of ``python -m nextunit.data`` (``<raw>/PUBD16/data/<bearing>/*.mat``): the time axes of its channels are measured
and are stored only in the original files. ``selected`` (THREEW only) skips records outside a set of IDs.
"""
from __future__ import annotations

import csv
import json
import re
from collections import deque
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from ... import definition
from .care_columns import CARE_COLUMNS

SEGMENT, HISTORY = 256, 32


# ---------------------------------------------------------------------------
# Shared pieces

def _waveform(array):
    """[channels, 768] from a 1-D or [n, channels] signal, and the number of points per piece."""
    x = np.asarray(array, dtype=np.float32)
    if x.ndim == 1:
        x = x[:, None]
    n, channels = x.shape
    out = np.zeros((channels, 3 * SEGMENT), dtype=np.float32)
    for i, start in enumerate((0, max(0, (n - SEGMENT) // 2), max(0, n - SEGMENT))):
        part = x[start:start + SEGMENT]
        out[:, i * SEGMENT:i * SEGMENT + len(part)] = part.T
    return out, min(n, SEGMENT)


def raw_segments(values):
    """Beginning, middle, end of a 1-D signal: three consecutive 256-point pieces."""
    values = np.asarray(values, dtype=np.float32).reshape(-1)
    out = np.zeros(3 * SEGMENT, dtype=np.float32)
    for slot, start in enumerate((0, max(0, (len(values) - SEGMENT) // 2), max(0, len(values) - SEGMENT))):
        part = values[start:start + SEGMENT]
        out[slot * SEGMENT:slot * SEGMENT + len(part)] = part
    return out


def aligned_segments(channels, times, reference=0):
    """All channels at the selected timestamps of one reference axis: equal axes by direct indexing, others by linear
    interpolation (the nearest observed endpoint outside their span)."""
    axes = [np.asarray(axis, dtype=np.float64).reshape(-1) for axis in times]
    ref = axes[reference]
    n = len(ref)
    out = np.zeros((len(channels), 3 * SEGMENT), dtype=np.float32)
    for slot, start in enumerate((0, max(0, (n - SEGMENT) // 2), max(0, n - SEGMENT))):
        stop = min(start + SEGMENT, n)
        selected = ref[start:stop]
        for index, (channel, axis) in enumerate(zip(channels, axes)):
            values = np.asarray(channel, dtype=np.float32).reshape(-1)
            assert len(values) == len(axis)
            part = values[start:stop] if np.array_equal(axis, ref) else np.interp(selected, axis, values)
            out[index, slot * SEGMENT:slot * SEGMENT + len(selected)] = part
    return out


def _recent(array):
    """Latest 32 rows of [n, channels] as [channels, 32], and how many were available."""
    x = np.asarray(array[-HISTORY:], dtype=np.float32)
    out = np.zeros((x.shape[1], HISTORY), dtype=np.float32)
    if len(x):
        out[:, -len(x):] = x.T
    return out, len(x)


def recent_rows(values, width=HISTORY):
    values = np.asarray(values, dtype=np.float32)
    out = np.zeros((values.shape[1], width), dtype=np.float32)
    take = min(len(values), width)
    if take:
        out[:, -take:] = values[-take:].T
    return out


def text_bytes(value, width=32):
    """Vocabulary-free encoding of a text field: its UTF-8 bytes, truncated or zero-padded to 32."""
    raw = str(value).encode('utf-8') if pd.notna(value) else b''
    out = np.zeros(width, dtype=np.float32)
    out[:min(len(raw), width)] = np.frombuffer(raw[:width], dtype=np.uint8)
    return out


def sample(record_id, sequence, tabular=(), image=None):
    out = {'record_id': str(record_id), 'sequence': np.asarray(sequence, dtype=np.float32),
           'tabular': np.asarray(tabular, dtype=np.float32), 'image': None}
    if image is not None:
        out['image'] = np.asarray(image, dtype=np.float32)
    return out


def blocks(root: Path):
    """Chunk directories of a stream unit (stream.json), else the unit itself."""
    manifest = root / 'stream.json'
    if manifest.exists():
        for name in json.loads(manifest.read_text()):
            yield root / name
    else:
        yield root


# ---------------------------------------------------------------------------
# Rotating machines and engines

PHYSICAL = {'CWRU': ('负载_马力', '名义转速_rpm', '采样率_Hz'), 'SEU': ('转速_Hz', '负载控制_V'),
            'PRONOSTIA': ('转速_rpm', '径向载荷_N', '采样率_Hz'), 'IMS': ('转速_rpm', '径向载荷_lb', '采样率_Hz')}
PUBD_CHANNELS = ('force', 'phase_current_1', 'phase_current_2', 'speed', 'temp_2_bearing_module', 'torque', 'vibration_1')
PUBD_INVALID = {'N15_M01_F10_KA08_2.mat'}       # corrupt in the source; also skipped by the converter


def _physical(dataset, unit):
    keys = PHYSICAL.get(dataset, ())
    if not keys:
        return []
    values = next(e['physical'] for e in definition.task(dataset)['entities'] if e['id'] == unit)
    return [float(values[k]) for k in keys]


def pubd16(root, unit, raw):
    from scipy.io import loadmat
    if raw is None:
        raise ValueError('PUBD16 needs the raw root (--raw): channel time axes exist only in the original MAT files')
    records = json.loads((root / 'records.json').read_text())
    sources = sorted(p for p in (Path(raw) / 'PUBD16/data' / unit).glob('*.mat') if p.name not in PUBD_INVALID)
    assert len(records) == len(sources), (unit, len(records), len(sources))
    for record, source in zip(records, sources):
        mat = loadmat(source, simplify_cells=True)[source.stem]
        metadata = {channel['Name']: channel for channel in mat['Y']}
        channels, times, lengths = [], [], []
        with np.load(root / record['signal_file']) as data:
            for key in PUBD_CHANNELS:
                channel = np.asarray(data[key]).reshape(-1)
                assert np.array_equal(channel, np.asarray(metadata[key]['Data']).reshape(-1)), (unit, source.name, key)
                channels.append(channel)
                times.append(mat['X'][int(metadata[key]['XIndex']) - 1]['Data'])
                lengths.append(min(len(channel), SEGMENT))
        yield sample(record['record_id'], aligned_segments(channels, times, PUBD_CHANNELS.index('vibration_1')), lengths)


def xjtu_sy(root):
    chunks = blocks(root) if (root / 'stream.json').exists() or (root / 'records.json').exists() else sorted(root.glob('chunk_*'))
    for block in chunks:
        for record in json.loads((block / 'records.json').read_text()):
            data = pd.read_csv(block / record['signal_file'], dtype=np.float32).to_numpy()
            sequence, length = _waveform(data)
            yield sample(record['record_id'], sequence, [record['elapsed_minutes'], length])


def cmapss(root):
    observations = pd.read_csv(root / 'observations.csv')
    cycles = observations['cycle'].to_numpy()
    values = observations.drop(columns='cycle').to_numpy(dtype=np.float32)
    for request in pd.read_csv(root / 'requests.csv').itertuples(index=False):
        stop = int(np.searchsorted(cycles, request.cycle, side='right'))
        sequence, length = _recent(values[max(0, stop - HISTORY):stop])
        yield sample(request.record_id, sequence, [request.cycle, length])


def ncmapss(root):
    for block in blocks(root):
        data = np.load(block / 'observations.npy', mmap_mode='r')
        sequence, length = _recent(data)
        for record in pd.read_csv(block / 'records.csv').itertuples(index=False):
            yield sample(record.record_id, sequence, [record.cycle, record.flight_class, len(data), length])


def cwru_seu(root, physical):
    data = np.load(root / 'signals.npy', mmap_mode='r')
    for i, record in enumerate(pd.read_csv(root / 'records.csv').itertuples(index=False)):
        sequence, length = _waveform(data[i])
        yield sample(record.record_id, sequence, [record.start_sample, length, *physical])


def pronostia(root, physical):
    data = np.load(root / 'signals.npy', mmap_mode='r')
    observations = pd.read_csv(root / 'observations.csv').set_index('sample_index')
    for request in pd.read_csv(root / 'requests.csv').itertuples(index=False):
        index = int(request.sample_index)
        sequence, length = _waveform(data[index])
        yield sample(request.record_id, sequence, [observations.loc[index, 'elapsed_seconds'], length, *physical])


def ims(root, physical):
    for block in blocks(root):
        data = np.load(block / 'signals.npy', mmap_mode='r')
        sequence, length = _waveform(data)
        for record in pd.read_csv(block / 'records.csv').itertuples(index=False):
            yield sample(record.record_id, sequence, [record.elapsed_hours, length, *physical])


# ---------------------------------------------------------------------------
# Batteries, tools and systems

def matwi(root, public_id):
    line = next(line for line in definition.info_md('MATWI').read_text(encoding='utf-8').splitlines()
                if line.startswith(f'| {public_id} |'))
    fields = [field.strip() for field in line.strip('|').split('|')]
    numeric = []
    for value in fields[2:8]:
        parts = value.split('/')
        numeric.extend([float(parts[0]) if parts[0] != '?' else np.nan, float(parts[1]) if len(parts) == 2 else np.nan])
    numeric += [float(fields[9])]
    conditions = np.concatenate([numeric, text_bytes(fields[1]), text_bytes(fields[8])])
    from PIL import Image
    for row in pd.read_csv(root / 'records.csv', dtype={'record_id': str}).itertuples(index=False):
        data = pd.read_csv(root / row.sensor_path, header=None)
        values = data.iloc[:, :5].to_numpy(dtype=np.float32)
        times = pd.to_datetime(data.iloc[:, 5], format='mixed')
        seconds = (times - times.iloc[0]).dt.total_seconds().to_numpy()
        sequence = np.stack([raw_segments(values[:, i]) for i in range(5)] + [raw_segments(seconds)])
        with Image.open(root / row.image_path) as picture:
            image = np.asarray(picture.convert('RGB').resize((128, 128), Image.Resampling.BILINEAR),
                               dtype=np.float32).transpose(2, 0, 1)
        yield sample(row.record_id, sequence, np.r_[len(values), conditions], image)


def phm10(root):
    for block in blocks(root):
        query = pd.read_csv(block / 'query.csv').iloc[0]
        values = pd.read_csv(block / 'signals.csv', header=None, dtype=np.float32).to_numpy()
        yield sample(query.record_id, np.stack([raw_segments(x) for x in values.T]),
                     [query.cut_index, len(values), 50000, 10400, 1555, .125, .2, 3])


def matr(root):
    summary = pd.read_csv(root / 'summary.csv').reindex(
        columns=['IR', 'QCharge', 'QDischarge', 'Tavg', 'Tmax', 'Tmin', 'chargetime', 'cycle'])
    conditions = json.loads((root / 'conditions.json').read_text())
    query = pd.read_csv(root / 'query.csv').iloc[0]
    sequences, lengths, separate_axes = [], [], []
    with np.load(root / 'cycles.npz') as arrays:
        for channel in ['I', 'Qc', 'Qd', 'Qdlin', 'T', 'Tdlin', 'V', 'discharge_dQdV', 't']:
            values = np.concatenate([arrays[f'cycle_{i:03d}_{channel}'] for i in range(1, 101)])
            # Curves on their own axis (not cycle time) go to the tabular part.
            (separate_axes if channel in {'Qdlin', 'Tdlin', 'discharge_dQdV'} else sequences).append(raw_segments(values))
            lengths.append(len(values))
    table = np.r_[summary.to_numpy(dtype=np.float32).ravel(), lengths, query.observed_cycles,
                  conditions['nominal_capacity_Ah'], conditions['chamber_temperature_C'], conditions['discharge_rate_C'],
                  text_bytes(conditions['charge_policy']), np.asarray(separate_axes).ravel()]
    yield sample(query.record_id, sequences, table)


def capacity(dataset, root):
    if dataset == 'NB1':
        channels = ['time_s', 'voltage_V', 'current_A', 'temperature_C', 'load_current_A', 'load_voltage_V']
        observed = ['observed_cycle', 'measured_capacity_Ah', 'ambient_temperature_C']
    else:
        channels = ['time_s', 'voltage_V', 'current_A', 'step_index', 'charge_capacity_Ah', 'discharge_capacity_Ah',
                    'internal_resistance_ohm']
        observed = ['observed_cycle', 'measured_capacity_Ah', 'elapsed_days', 'nominal_capacity_Ah']
    history = deque(maxlen=HISTORY)
    for block in blocks(root):
        query = pd.read_csv(block / 'query.csv').iloc[0]
        history.append(pd.read_csv(block / 'observation.csv').iloc[0][observed].to_numpy(dtype=np.float32))
        with np.load(block / 'signals.npz') as arrays:
            sequences = [raw_segments(arrays[channel]) for channel in channels]
            length = len(arrays[channels[0]])
        yield sample(query.record_id, sequences,
                     np.r_[query.observed_cycle, query.forecast_horizon, length, recent_rows(np.asarray(history)).ravel()])


def nb14(root):
    channels = ['time', 'relative_time', 'current', 'voltage', 'temperature']
    for block in blocks(root):
        requests = pd.read_csv(block / 'requests.csv', dtype={'record_id': str})
        with np.load(block / 'daily.npz') as arrays:
            for row in requests.itertuples(index=False):
                stop = int(row.history_stop)
                sequences = [raw_segments(arrays[channel][:stop]) for channel in channels]
                offsets = arrays['step_offsets']
                discharge = np.repeat(arrays['step_discharging'], np.diff(offsets))[:stop]
                sequences.append(raw_segments(discharge))
                yield sample(row.record_id, sequences, [row.age_seconds, stop])


@lru_cache(maxsize=None)
def _ahu_columns():
    return sorted(set(re.findall(r'^- `([^`]+)`', definition.info_md('AHU21').read_text(encoding='utf-8'), re.M)))


def ahu21(root):
    history, first_time, columns = deque(maxlen=HISTORY), None, _ahu_columns()
    for frame in pd.read_csv(root / 'signals.csv', dtype={'record_id': str}, chunksize=4096):
        timestamps = pd.to_datetime(frame.Time, format='mixed')
        if first_time is None:
            first_time = timestamps.iloc[0]
        elapsed = (timestamps - first_time).dt.total_seconds().to_numpy()
        values = frame.reindex(columns=columns).to_numpy(dtype=np.float32)
        for record_id, seconds, row in zip(frame.record_id, elapsed, values):
            history.append(np.r_[seconds, row])
            yield sample(record_id, recent_rows(np.asarray(history)), [seconds, len(history)])


HSF_CHANNELS = ['CE', 'CP', 'EPS1', 'FS1', 'FS2', 'PS1', 'PS2', 'PS3', 'PS4', 'PS5', 'PS6', 'SE', 'TS1', 'TS2', 'TS3',
                'TS4', 'VS1']
HSF_RATES = [1, 1, 100, 10, 10, 100, 100, 100, 100, 100, 100, 1, 1, 1, 1, 1, 1]


def hsf15(root):
    for row in json.loads((root / 'records.json').read_text()):
        with np.load(root / row['signal_file']) as arrays:
            values = [arrays[key] for key in HSF_CHANNELS]
            times = [np.arange(len(value), dtype=np.float64) / rate for value, rate in zip(values, HSF_RATES)]
            sequence = aligned_segments(values, times, reference=HSF_CHANNELS.index('PS1'))
            lengths = [len(arrays[key]) for key in HSF_CHANNELS]
        yield sample(row['record_id'], sequence, lengths)


def phme20(root):
    history = deque(maxlen=HISTORY)
    for block in blocks(root):
        frame = pd.read_csv(block / 'measurement.csv')
        history.extend(frame[['elapsed_seconds', 'flow_ml_min', 'upstream_psi', 'downstream_psi']].to_numpy(dtype=np.float32))
        for row in json.loads((block / 'records.json').read_text()):
            yield sample(row['record_id'], recent_rows(np.asarray(history)),
                         [row['elapsed_seconds'], row['particle_size_micron'], row['solid_ratio_percent'], len(history)])


def tep(root):
    with np.load(root / 'measurements.npz') as arrays:
        values, elapsed = arrays['values'], arrays['elapsed_minutes']
        for row in json.loads((root / 'records.json').read_text()):
            stop = int(row['row']) + 1
            yield sample(row['record_id'], recent_rows(values[max(0, stop - HISTORY):stop]), [elapsed[stop - 1], min(stop, HISTORY)])


def backblaze(root):
    categories = ['model', 'datacenter', 'cluster_id', 'vault_id', 'pod_id']
    histories, numeric_columns = {}, None
    for block in blocks(root):
        frame = pd.read_csv(block / 'measurements.csv', dtype={'record_id': str, 'disk_id': str})
        if numeric_columns is None:
            numeric_columns = sorted(set(frame.columns) - {'record_id', 'disk_id', *categories})
        numeric = frame.reindex(columns=numeric_columns).to_numpy(dtype=np.float32)
        # The disk ID only indexes history; it is never a model input.
        for (record_id, disk_id, *values), row in zip(frame[['record_id', 'disk_id', *categories]].itertuples(index=False, name=None), numeric):
            history = histories.setdefault(disk_id, deque(maxlen=HISTORY))
            history.append(row)
            yield sample(record_id, recent_rows(np.asarray(history)),
                         np.r_[len(history), np.concatenate([text_bytes(value) for value in values])])


# ---------------------------------------------------------------------------
# Wind turbines, composites, vehicles, oil wells

CARE_CHANNELS = tuple((site, name) for site in sorted(CARE_COLUMNS) for name in CARE_COLUMNS[site])
CARE_INDEX = {key: i for i, key in enumerate(CARE_CHANNELS)}


def care(root):
    """16 uniformly spaced history rows and 16 observation rows, with their time coordinates; channels of other
    sites stay NaN."""
    for row in pd.read_csv(root / 'records.csv', dtype={'record_id': str}).itertuples(index=False):
        with np.load(root / row.file, allow_pickle=False) as data:
            site = str(data['site_id'].item())
            names = data['feature_names'].tolist()
            assert names == CARE_COLUMNS[site]
            sequence = np.full((len(CARE_CHANNELS) + 3, 32), np.nan, dtype=np.float32)
            indices = [CARE_INDEX[(site, name)] for name in names]
            lengths = []
            for phase, prefix in enumerate(('history', 'observation')):
                values = data[prefix + '_values']
                lengths.append(len(values))
                take = np.linspace(0, len(values) - 1, 16, dtype=int)
                columns = np.arange(16 * phase, 16 * (phase + 1))
                sequence[np.ix_(indices, columns)] = values[take].T
                sequence[-3, columns] = data[prefix + '_time_seconds'][take]
                sequence[-2, columns] = data[prefix + '_day_of_year'][take]
                sequence[-1, columns] = phase
            yield sample(row.record_id, sequence, lengths + [float(site == f'site_{i}') for i in (1, 2, 3)])


CFRP_PATHS = [(f, a, s) for f in (150, 200, 250, 300, 350, 400, 450) for a in range(1, 7) for s in range(7, 13)]
CFRP_INDEX = {key: i for i, key in enumerate(CFRP_PATHS)}


def cfrp(root):
    """Per request: three measurements of the requested cycle (first, middle, last), each with every documented
    actuator-sensor path as three 256-point pieces (NaN where absent), path settings and load."""
    for folder in blocks(root):
        request = pd.read_csv(folder / 'requests.csv', dtype={'record_id': str}).iloc[0]
        table = pd.read_csv(folder / 'measurements.csv')
        table = table[table.cycles == request.cycles].reset_index(drop=True)
        signals, tabular = [], [float(request.cycles), *[float(request.layup == i) for i in (1, 2, 3)]]
        for position in np.linspace(0, len(table) - 1, 3, dtype=int):
            row = table.iloc[position]
            with np.load(folder / row.file, allow_pickle=False) as data:
                signal = np.full((504, 768), np.nan, dtype=np.float32)
                meta = np.full((252, 4), np.nan, dtype=np.float32)
                waveforms = {field: data[field] for field in ('signal_actuator', 'signal_sensor')}
                for j, (a, s, amp, f, gain, rate) in enumerate(data['path_metadata']):
                    key = (int(f), int(a), int(s))
                    if key not in CFRP_INDEX:
                        raise ValueError(f'Undocumented physical path: {key}')
                    k = CFRP_INDEX[key]
                    meta[k] = [amp, f, gain, rate]
                    for offset, field in ((0, 'signal_actuator'), (252, 'signal_sensor')):
                        values = waveforms[field][j]
                        n, parts = len(values), []
                        for start in (0, max(0, (n - 256) // 2), max(0, n - 256)):
                            segment = np.full(256, np.nan, dtype=np.float32)
                            v = values[start:start + 256]
                            segment[:len(v)] = v
                            parts.append(segment)
                        signal[offset + k] = np.concatenate(parts)
                signals.append(signal)
                tabular.extend(meta.ravel().tolist())
            tabular.append(float(row.load_kips))
            encoded = str(row.condition).encode('utf8')[:32]
            tabular.extend(list(encoded) + [0] * (32 - len(encoded)))
        yield sample(request.record_id, np.concatenate(signals, axis=0), tabular)


def scania_rows(values):
    out = np.zeros((105, 32), dtype=np.float32)
    take = min(32, len(values))
    if take:
        out[:, -take:] = np.asarray(values[-take:], dtype=np.float32).T
    return out


def scania_tabular(spec, time):
    """Time of the readout and the eight vehicle specification fields (32 UTF-8 bytes each)."""
    def encode(value):
        raw = str(value).encode('utf-8') if pd.notna(value) else b''
        assert len(raw) <= 32
        out = np.zeros(32, dtype=np.float32)
        out[:len(raw)] = np.frombuffer(raw, dtype=np.uint8)
        return out
    return np.concatenate([[float(time)], *[encode(x) for x in spec]]).astype(np.float32)


def scania(root):
    z = np.load(root / 'history.npz')
    specs = pd.read_csv(root / 'specifications.csv').set_index('vehicle_id')
    requests = pd.read_csv(root / 'requests.csv', dtype={'record_id': str, 'vehicle_id': str})
    lookup = {str(v): i for i, v in enumerate(z['vehicle_id'])}
    values, times, offsets = z['values'], z['time_step'], z['offsets']
    for r in requests.itertuples(index=False):
        i = lookup[r.vehicle_id]
        start, stop = offsets[i:i + 2]
        end = start + np.searchsorted(times[start:stop], r.time_step, side='right')
        assert end > start and np.isclose(times[end - 1], r.time_step, rtol=0, atol=1e-9)
        yield sample(r.record_id, scania_rows(values[max(start, end - 32):end]), scania_tabular(specs.loc[r.vehicle_id].to_numpy(), r.time_step))


def threew(root, selected=None):
    """27 channels, the last 32 observations of the current sequence."""
    current = values = elapsed = None
    with (root / 'records.csv').open() as stream:
        for row in csv.DictReader(stream):
            if selected is not None and row['record_id'] not in selected:
                continue
            if row['sequence_id'] != current:
                with np.load(root / f"{row['sequence_id']}.npz") as arrays, np.errstate(over='ignore'):
                    values = arrays['values'].astype(np.float32)        # out-of-range values become inf
                    elapsed = arrays['elapsed_seconds']
                current = row['sequence_id']
            stop = int(row['row_index']) + 1
            start = max(0, stop - 32)
            sequence = np.zeros((27, 32), dtype=np.float32)
            sequence[:, -(stop - start):] = values[start:stop].T
            yield sample(row['record_id'], sequence, [elapsed[stop - 1], stop - start])


# ---------------------------------------------------------------------------

def iter_samples(dataset: str, inputs: Path | str, unit: str, raw: Path | str | None = None, selected=None):
    """The requests of one unit (its whole ``inputs`` directory, all chunks), in order."""
    root = Path(inputs)
    if dataset == 'PUBD16':
        yield from pubd16(root, unit, raw)
    elif dataset in ('CWRU', 'SEU'):
        yield from cwru_seu(root, _physical(dataset, unit))
    elif dataset == 'PRONOSTIA':
        yield from pronostia(root, _physical(dataset, unit))
    elif dataset == 'IMS':
        yield from ims(root, _physical(dataset, unit))
    elif dataset == 'MATWI':
        yield from matwi(root, definition.public_ids(dataset)[unit])
    elif dataset in ('NB1', 'CALCE'):
        yield from capacity(dataset, root)
    elif dataset == 'THREEW':
        yield from threew(root, selected)
    else:
        yield from {'XJTU-SY': xjtu_sy, 'CMAPSS': cmapss, 'NCMAPSS': ncmapss, 'PHM10': phm10, 'MATR': matr, 'NB14': nb14,
                    'AHU21': ahu21, 'HSF15': hsf15, 'PHME20': phme20, 'TEP': tep, 'BACKBLAZE': backblaze, 'CARE': care,
                    'CFRP': cfrp, 'SCANIA': scania}[dataset](root)
