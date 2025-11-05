#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil

def fix_file_encoding(filepath):
    """修复文件编码问题"""
    print(f"修复文件编码: {filepath}")
    
    # 备份原文件
    backup_path = filepath + '.backup'
    shutil.copy2(filepath, backup_path)
    print(f"已备份原文件到: {backup_path}")
    
    # 读取文件内容
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        print("✅ 成功以UTF-8读取文件")
    except Exception as e:
        print(f"❌ UTF-8读取失败: {e}")
        # 尝试其他编码
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
            print("✅ 成功以latin-1读取文件")
        except Exception as e2:
            print(f"❌ 所有编码都失败: {e2}")
            return False
    
    # 重新以UTF-8写入文件
    try:
        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        print("✅ 成功以UTF-8重新写入文件")
        return True
    except Exception as e:
        print(f"❌ UTF-8写入失败: {e}")
        # 恢复备份
        shutil.copy2(backup_path, filepath)
        print("已恢复备份文件")
        return False

if __name__ == "__main__":
    # 修复数据库配置文件
    files_to_fix = [
        'database/config.py',
        'database/postgresql_config.py'
    ]
    
    for config_file in files_to_fix:
        print(f"\n=== 修复 {config_file} ===")
        if os.path.exists(config_file):
            success = fix_file_encoding(config_file)
            if success:
                print(f"✅ {config_file} 编码修复完成")
            else:
                print(f"❌ {config_file} 编码修复失败")
        else:
            print(f"❌ 文件不存在: {config_file}")