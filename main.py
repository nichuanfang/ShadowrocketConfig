# 处理小火箭配置文件的入口文件

import os
from datetime import datetime

# 通用模块
general_module_line = '[General]\n'
#路由模块
rule_module_line = '[Rule]\n'

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def write_file(file_path, content):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w+', encoding='utf-8') as file:
        file.write(content)

def process_strategy(general_content, base_content, strategy_content, custom_direct, custom_proxy, custom_reject):
    # 通用配置
    combined_content = general_module_line + general_content + '\n'
    #路由规则
    combined_content = combined_content + rule_module_line
    strategy_content = strategy_content.replace('{custom-direct}', custom_direct)
    strategy_content = strategy_content.replace('{custom-proxy}', custom_proxy)
    strategy_content = strategy_content.replace('{custom-reject}', custom_reject)
    strategy_content = replace_direct(strategy_content)
    strategy_content = replace_reject(strategy_content)
    strategy_content = replace_proxy(strategy_content)
    strategy_content = replace_direct_accelerate(strategy_content)
    strategy_content = replace_proxy_accelerate(strategy_content)
    
    combined_content = combined_content + strategy_content + '\n'
    #基础配置
    combined_content = combined_content + base_content
    
    
    return combined_content

def main():
    # 读取自定义规则
    custom_direct = read_file('config/rules/direct.conf')
    custom_proxy = read_file('config/rules/proxy.conf')
    custom_reject = read_file('config/rules/reject.conf')

    # 读取base.conf和general.conf
    base_content = read_file('base.conf')
    general_content = read_file('config/general/general.conf')

    # 处理每种策略
    strategy_files = [
        'config/strategy/black.conf',
        'config/strategy/black_ad.conf',
        'config/strategy/black_ accelerate.conf',
        'config/strategy/black_ accelerate_ad.conf',
        'config/strategy/white.conf',
        'config/strategy/white_ad.conf',
        'config/strategy/white_ accelerate.conf',
        'config/strategy/white_ accelerate_ad.conf'
    ]

    for strategy_file in strategy_files:
        strategy_name = f'shadowrocket_{os.path.basename(strategy_file)}'
        strategy_content = read_file(strategy_file)
        current_date = datetime.now().strftime("# Shadowrocket: %Y-%m-%d %H:%M:%S\n")
        output_content = current_date + process_strategy(general_content, base_content, strategy_content, custom_direct, custom_proxy, custom_reject)
        write_file(f'dist/{strategy_name}', output_content)

if __name__ == '__main__':
    main()
