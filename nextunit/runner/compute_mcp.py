"""Stdio MCP server inside the agent sandbox: forwards run_command and run_light_command to the host broker.

Runs with the runtime's Python and the standard library only. Tool descriptions are shown to the agent under test
and are kept exactly as in the paper's runs."""
import json
import socket
import sys
import threading


COMMAND = {'type': 'string', 'minLength': 1}
OUTPUT = {'type': 'integer', 'minimum': 1, 'maximum': 100000, 'default': 16000}
PERSISTENCE = ('命令在 /workspace 中执行。/workspace 和 /tmp 在当前轨迹的命令之间持久保存，'
               '不同轨迹互相隔离；每条命令结束后清理全部后台子进程。'
               'stdout/stderr 按 max_output_chars 截断。只有当前轨迹有命令排队且没有任何命令运行时，'
               '排队等待才不计入开发预算。')


def tools_for_mode(mode='A'):
    gpu_default = mode == 'B'
    heavy_gpu = ('GPU 默认可见且可直接使用，无需额外申请；gpu=false 可关闭当前命令的 GPU。'
                 if gpu_default else '需要 CUDA 时设置 gpu=true。')
    return [{
        'name': 'run_command',
        'description': (
            '申请资源并执行数据计算、特征处理、训练、验证、预测及批量处理命令。'
            '不确定资源需求时使用本工具。默认申请 1 个逻辑 CPU、2 GiB 内存；'
            'cpus 可设为 1–4，memory_gb 可设为 1–8，' + heavy_gpu +
            '资源按申请量实施硬限制；全局计算资源池为 8 个逻辑 CPU、16 GiB 内存和 1 个 GPU，'
            '当前轨迹的计算命令合计最多占用 4 个逻辑 CPU、8 GiB 内存和 1 个 GPU。'
            '同一受试者的工具命令按提交顺序逐条执行；不同受试者按可用资源并行，GPU 命令每次执行一条；timeout_seconds 从取得资源时开始计时。' + PERSISTENCE
        ),
        'inputSchema': {
            'type': 'object',
            'properties': {
                'command': COMMAND,
                'cpus': {'type': 'integer', 'minimum': 1, 'maximum': 4, 'default': 1},
                'memory_gb': {'type': 'integer', 'minimum': 1, 'maximum': 8, 'default': 2},
                'gpu': {'type': 'boolean', 'default': gpu_default},
                'timeout_seconds': {'type': 'number', 'exclusiveMinimum': 0, 'maximum': 7200, 'default': 7200},
                'max_output_chars': OUTPUT,
            },
            'required': ['command'],
            'additionalProperties': False,
        },
    }, {
        'name': 'run_light_command',
        'description': ('以独立的轻量配额执行目录、文件查看或编辑、CPU 环境及轻量导包检查。'
            '数据计算、特征处理、训练、验证、预测及批量处理使用 run_command。'
            '固定硬限制为 1 个逻辑 CPU、512 MiB 内存、10 秒执行墙钟，无 GPU，也不等待其他轨迹的 GPU。'
            'CUDA/GPU 可用性检查使用 run_command；本工具看不到 GPU 不代表计算环境没有 GPU。'
            '这些限制不能调整。同一受试者的工具命令按提交顺序逐条执行；不同受试者的轻量命令按独立配额并行。'
            '超时会终止命令并返回错误，不会自动重跑。' + PERSISTENCE),
        'inputSchema': {'type': 'object', 'properties': {'command': COMMAND, 'max_output_chars': OUTPUT},
                        'required': ['command'], 'additionalProperties': False},
    }]


class Bridge:
    def __init__(self, path, mode='A'):
        self.path = path
        self.tools = tools_for_mode(mode)
        self.output_lock = threading.Lock()
        self.calls_lock = threading.Lock()
        self.calls = {}

    def reply(self, request_id, *, result=None, error=None):
        message = {'jsonrpc': '2.0', 'id': request_id}
        message['error' if error is not None else 'result'] = error if error is not None else result
        with self.output_lock:
            print(json.dumps(message, ensure_ascii=False), flush=True)

    def cancel(self, request_id):
        with self.calls_lock:
            connection = self.calls.get(request_id)
            if connection is not None:
                try:
                    connection.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                connection.close()

    def run(self, request_id, arguments, connection):
        try:
            connection.connect(self.path)
            connection.sendall(json.dumps(arguments).encode() + b'\n')
            with connection.makefile('rb') as stream:
                result = json.loads(stream.readline())
            response = {'content': [{'type': 'text', 'text': json.dumps(result, ensure_ascii=False)}],
                        'isError': bool(result.get('error')) or result.get('status') != 'completed'
                                   or result.get('returncode') != 0}
        except (OSError, ValueError) as error:
            response = {'content': [{'type': 'text', 'text': str(error)}], 'isError': True}
        finally:
            connection.close()
            with self.calls_lock:
                self.calls.pop(request_id, None)
        self.reply(request_id, result=response)

    def dispatch(self, request):
        method, request_id = request['method'], request.get('id')
        params = request.get('params', {})
        if method == 'notifications/cancelled':
            self.cancel(params['requestId'])
            return
        if request_id is None:
            return
        if method == 'initialize':
            self.reply(request_id, result={
                'protocolVersion': params.get('protocolVersion', '2025-03-26'),
                'capabilities': {'tools': {}},
                'serverInfo': {'name': 'experiment-compute', 'version': '2.1'},
            })
        elif method == 'ping':
            self.reply(request_id, result={})
        elif method == 'tools/list':
            self.reply(request_id, result={'tools': self.tools})
        elif method == 'tools/call' and params.get('name') in ('run_command', 'run_light_command'):
            arguments = {'tool': params['name'], 'arguments': params.get('arguments', {})}
            connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            with self.calls_lock:
                self.calls[request_id] = connection
            threading.Thread(target=self.run, args=(request_id, arguments, connection), daemon=True).start()
        else:
            self.reply(request_id, error={'code': -32601, 'message': 'Unknown method or tool'})

    def serve(self):
        try:
            for line in sys.stdin:
                self.dispatch(json.loads(line))
        finally:
            with self.calls_lock:
                calls = list(self.calls)
            for request_id in calls:
                self.cancel(request_id)


if __name__ == '__main__':
    Bridge(sys.argv[1] if len(sys.argv) > 1 else '/broker.sock',
           sys.argv[2] if len(sys.argv) > 2 else 'A').serve()
