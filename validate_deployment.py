#!/usr/bin/env python3
"""
部署驗證腳本
檢查系統配置和依賴項是否正確
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path
from typing import List, Dict, Any

def check_python_version():
    """檢查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        return False, f"Python版本過低: {version.major}.{version.minor}, 需要3.8+"
    return True, f"Python版本: {version.major}.{version.minor}.{version.micro}"

def check_required_files():
    """檢查必要檔案是否存在"""
    required_files = [
        "main.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "models/__init__.py",
        "services/__init__.py",
        "utils/__init__.py",
        "azure-config/k8s/namespace.yaml",
        "azure-config/k8s/configmap.yaml",
        "azure-config/k8s/secret.yaml",
        "sql/init.sql"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    return len(missing_files) == 0, {
        "existing": existing_files,
        "missing": missing_files
    }

def check_environment_variables():
    """檢查重要的環境變數"""
    important_vars = [
        "POSTGRES_HOST",
        "POSTGRES_USER", 
        "POSTGRES_PASSWORD",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_SEARCH_ENDPOINT"
    ]
    
    set_vars = []
    missing_vars = []
    
    for var in important_vars:
        if os.getenv(var):
            set_vars.append(var)
        else:
            missing_vars.append(var)
    
    return len(missing_vars) == 0, {
        "set": set_vars,
        "missing": missing_vars
    }

def check_import_dependencies():
    """檢查Python依賴項導入"""
    critical_imports = [
        "fastapi",
        "uvicorn", 
        "pydantic",
        "asyncpg",
        "aiohttp"
    ]
    
    available_imports = []
    missing_imports = []
    
    for module in critical_imports:
        try:
            importlib.import_module(module)
            available_imports.append(module)
        except ImportError:
            missing_imports.append(module)
    
    return len(missing_imports) == 0, {
        "available": available_imports,
        "missing": missing_imports
    }

def check_syntax_errors():
    """檢查Python檔案的語法錯誤"""
    python_files = []
    syntax_errors = []
    
    # 找所有Python檔案
    for pattern in ["*.py", "*/*.py", "*/*/*.py"]:
        python_files.extend(Path(".").glob(pattern))
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                compile(f.read(), py_file, 'exec')
        except SyntaxError as e:
            syntax_errors.append({
                "file": str(py_file),
                "line": e.lineno,
                "error": str(e)
            })
        except Exception as e:
            syntax_errors.append({
                "file": str(py_file),
                "error": str(e)
            })
    
    return len(syntax_errors) == 0, {
        "total_files": len(python_files),
        "errors": syntax_errors
    }

def main():
    """主驗證函數"""
    print("🔍 開始部署驗證...")
    print("=" * 50)
    
    checks = [
        ("Python版本", check_python_version),
        ("必要檔案", check_required_files),
        ("環境變數", check_environment_variables),
        ("Python依賴項", check_import_dependencies),
        ("語法檢查", check_syntax_errors)
    ]
    
    all_passed = True
    results = {}
    
    for check_name, check_func in checks:
        print(f"\n📋 檢查: {check_name}")
        try:
            passed, details = check_func()
            results[check_name] = {"passed": passed, "details": details}
            
            if passed:
                print(f"✅ {check_name}: 通過")
                if isinstance(details, str):
                    print(f"   {details}")
            else:
                print(f"❌ {check_name}: 失敗")
                all_passed = False
                
                if isinstance(details, dict):
                    if "missing" in details and details["missing"]:
                        print(f"   缺失: {', '.join(details['missing'])}")
                    if "errors" in details and details["errors"]:
                        for error in details["errors"][:3]:  # 只顯示前3個錯誤
                            print(f"   錯誤: {error}")
                
        except Exception as e:
            print(f"❌ {check_name}: 檢查過程中發生錯誤: {str(e)}")
            all_passed = False
            results[check_name] = {"passed": False, "error": str(e)}
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有檢查都通過！系統已準備好部署。")
        return 0
    else:
        print("⚠️  發現問題，請修復後再進行部署。")
        return 1

if __name__ == "__main__":
    exit(main())