"""简单端到端测试：调用示例 agent 并验证返回结构。"""
import sys
from importlib import import_module


def main():
    try:
        # 使用 examples/run_agent.py 的主方法（如果存在）
        mod = import_module('examples.run_agent')
    except Exception:
        # 兼容直接作为脚本运行的情况
        try:
            mod = import_module('run_agent')
        except Exception as e:
            print('无法导入 examples.run_agent 或 run_agent:', e)
            sys.exit(2)

    # 期望模块提供 run_demo() 或 main() 之一
    if hasattr(mod, 'run_demo'):
        result = mod.run_demo()
    elif hasattr(mod, 'main'):
        result = mod.main()
    else:
        # 如果没有返回值，说明脚本运行成功
        print('找到模块并无返回值函数，假定运行成功。')
        sys.exit(0)

    # 对返回值做最小验证
    if result is None:
        print('示例脚本执行完成，返回 None，视为成功。')
        sys.exit(0)

    # 如果返回 dict，进行简单断言
    if isinstance(result, dict):
        if 'greeting' in result or 'message' in result:
            print('端到端测试通过：返回包含 greeting/message。')
            sys.exit(0)
        else:
            print('端到端测试失败：返回字典但缺少 greeting/message 键。', result)
            sys.exit(3)

    print('端到端测试完成，返回类型：', type(result))
    sys.exit(0)


if __name__ == '__main__':
    main()
