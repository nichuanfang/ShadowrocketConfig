# 处理小火箭配置文件的入口文件

import os
from datetime import datetime

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def write_file(file_path, content):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w+', encoding='utf-8') as file:
        file.write(content)

def process_strategy(general_content, base_content, strategy_content, custom_direct, custom_proxy, custom_reject):
    combined_content = general_content + base_content
    combined_content = combined_content.replace('{custom-direct}', custom_direct)
    combined_content = combined_content.replace('{custom-proxy}', custom_proxy)
    combined_content = combined_content.replace('{custom-reject}', custom_reject)
    combined_content += strategy_content
    return combined_content

def main():
    # 读取自定义规则
    custom_direct = read_file('src/rules/direct.conf')
    custom_proxy = read_file('src/rules/proxy.conf')
    custom_reject = read_file('src/rules/reject.conf')

    # 读取base.conf和general.conf
    base_content = read_file('base.conf')
    general_content = read_file('src/general/general.conf')

    # 处理每种策略
    strategy_files = [
        'src/strategy/black.conf',
        'src/strategy/black_ad.conf',
        'src/strategy/black_ accelerate.conf',
        'src/strategy/black_ accelerate_ad.conf',
        'src/strategy/white.conf',
        'src/strategy/white_ad.conf',
        'src/strategy/white_ accelerate.conf',
        'src/strategy/white_ accelerate_ad.conf'
    ]

    for strategy_file in strategy_files:
        strategy_name = os.path.basename(strategy_file)
        strategy_content = read_file(strategy_file)
        current_date = datetime.now().strftime("# Shadowrocket: %Y-%m-%d %H:%M:%S\n")
        output_content = current_date + process_strategy(general_content, base_content, strategy_content, custom_direct, custom_proxy, custom_reject)
        write_file(f'dist/{strategy_name}', output_content)

if __name__ == '__main__':
    main()
