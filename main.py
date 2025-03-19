# 处理小火箭配置文件的入口文件

import os
from datetime import datetime
import requests

# 通用模块
general_module_line = '[General]\n'
#路由模块
rule_module_line = '[Rule]\n'
# 直连地址
direct_url = 'https://cdn.jsdelivr.net/gh/GMOogway/shadowrocket-rules@master/sr_direct_list.module'
# 代理地址
proxy_url = 'https://cdn.jsdelivr.net/gh/GMOogway/shadowrocket-rules@master/sr_proxy_list.module'
# 拦截地址
reject_url = 'https://cdn.jsdelivr.net/gh/GMOogway/shadowrocket-rules@master/sr_reject_list.module'


def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def write_file(file_path, content):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w+', encoding='utf-8') as file:
        file.write(content)
        
def extract_rules_from(source: str) -> str or None:
    """
    从源文本中提取 [Rule] 部分的内容。

    Args:
        source (str): 包含规则的源文本。

    Returns:
        str or None: 如果找到 [Rule] 部分，则返回提取的规则字符串；否则返回 None。
    """
    raw = requests.get(direct_url)
    text = raw.text
    # 使用正则表达式查找 [Rule] 部分及其后面的所有内容，直到文本结束
    start_index = text.find("[Rule]")
    if start_index != -1:
        rules = text[start_index + len("[Rule]"):]
        return rules.strip()
    else:
        return None

def replace_direct(strategy_content):
    """
    替换策略内容中的 {direct} 
    """
    # direct_content = read_file('config/rules/direct.conf')
    direct_content = extract_rules_from(direct_url)
    return strategy_content.replace('{direct}', direct_content)

def replace_reject(strategy_content):
    """
    替换策略内容中的 {reject} 
    """
    # reject_content = read_file('config/rules/reject.conf')
    reject_content = extract_rules_from(reject_url)
    return strategy_content.replace('{reject}', reject_content)

def replace_proxy(strategy_content):
    """
    替换策略内容中的 {proxy}
    """
    # proxy_content = read_file('config/rules/proxy.conf')
    proxy_content = extract_rules_from(proxy_url)
    return strategy_content.replace('{reject}', proxy_content)

def replace_direct_accelerate(strategy_content):
    """
    替换策略内容中的 {direct-accelerate} 占位符为 direct.conf 文件中的内容。
    假设 direct-accelerate 内容与直连规则一致。
    """
    direct_accelerate_content = read_file('config/rules/direct_accelerate.conf')
    return strategy_content.replace('{direct-accelerate}', direct_accelerate_content)

def replace_proxy_accelerate(strategy_content):
    """
    替换策略内容中的 {proxy-accelerate} 占位符为远程 URL 中获取的加速代理规则内容。
    """
    proxy_accelerate_content = read_file('config/rules/proxy_accelerate.conf')
    return strategy_content.replace('{proxy-accelerate}', proxy_accelerate_content)

def process_strategy(general_content, base_content, strategy_content, custom_direct, custom_proxy, custom_reject):
    # 通用配置
    combined_content = general_module_line + general_content + '\n'
    #路由规则
    combined_content = combined_content + rule_module_line + '\n'
    strategy_content = strategy_content.replace('{custom-direct}', custom_direct) + '\n'
    strategy_content = strategy_content.replace('{custom-proxy}', custom_proxy) + '\n'
    strategy_content = strategy_content.replace('{custom-reject}', custom_reject) + '\n'
    strategy_content = replace_direct(strategy_content) + '\n'
    strategy_content = replace_reject(strategy_content) + '\n'
    strategy_content = replace_proxy(strategy_content) + '\n'
    strategy_content = replace_direct_accelerate(strategy_content) + '\n'
    strategy_content = replace_proxy_accelerate(strategy_content) + '\n'
    
    combined_content = combined_content + strategy_content
    #基础配置
    combined_content = combined_content + base_content
    return combined_content

def main():
    # 读取自定义规则
    custom_direct = read_file('config/rules/custom_direct.conf')
    custom_proxy = read_file('config/rules/custom_proxy.conf')
    custom_reject = read_file('config/rules/custom_reject.conf')

    # 读取base.conf和general.conf
    base_content = read_file('base.conf')
    general_content = read_file('config/general/general.conf')

    # 处理每种策略
    strategy_files = [
        'config/strategy/black.conf',
        'config/strategy/black_ad.conf',
        'config/strategy/black_accelerate.conf',
        'config/strategy/black_accelerate_ad.conf',
        'config/strategy/white.conf',
        'config/strategy/white_ad.conf',
        'config/strategy/white_accelerate.conf',
        'config/strategy/white_accelerate_ad.conf'
    ]

    for strategy_file in strategy_files:
        strategy_name = f'shadowrocket_{os.path.basename(strategy_file)}'
        strategy_content = read_file(strategy_file)
        current_date = datetime.now().strftime("# Shadowrocket: %Y-%m-%d %H:%M:%S\n")
        output_content = current_date + process_strategy(general_content, base_content, strategy_content, custom_direct, custom_proxy, custom_reject)
        write_file(f'dist/{strategy_name}', output_content)

if __name__ == '__main__':
    main()
