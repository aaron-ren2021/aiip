#!/usr/bin/env python3
"""
部署監控腳本
監控Kubernetes部署狀態和應用程式健康狀況
"""

import subprocess
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any
import argparse

class DeploymentMonitor:
    def __init__(self, namespace: str = "patent-rpa-system"):
        self.namespace = namespace
        self.deployments = [
            "patent-rpa-backend",
            "patent-rpa-frontend", 
            "patent-rpa-bots"
        ]
    
    def run_kubectl_command(self, command: List[str]) -> Dict[str, Any]:
        """執行kubectl命令並返回結果"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            return {"success": True, "output": result.stdout, "error": None}
        except subprocess.CalledProcessError as e:
            return {"success": False, "output": None, "error": e.stderr}
    
    def get_pod_status(self) -> Dict[str, Any]:
        """取得Pod狀態"""
        cmd = ["kubectl", "get", "pods", "-n", self.namespace, "-o", "json"]
        result = self.run_kubectl_command(cmd)
        
        if not result["success"]:
            return {"error": result["error"]}
        
        try:
            pods_data = json.loads(result["output"])
            pods_status = {}
            
            for pod in pods_data.get("items", []):
                pod_name = pod["metadata"]["name"]
                status = pod["status"]["phase"]
                ready = False
                
                # 檢查容器就緒狀態
                container_statuses = pod["status"].get("containerStatuses", [])
                if container_statuses:
                    ready = all(cs.get("ready", False) for cs in container_statuses)
                
                pods_status[pod_name] = {
                    "status": status,
                    "ready": ready,
                    "restart_count": sum(cs.get("restartCount", 0) for cs in container_statuses),
                    "created": pod["metadata"]["creationTimestamp"]
                }
            
            return {"pods": pods_status}
            
        except json.JSONDecodeError as e:
            return {"error": f"解析kubectl輸出失敗: {e}"}
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """取得Deployment狀態"""
        deployment_status = {}
        
        for deployment in self.deployments:
            cmd = ["kubectl", "get", "deployment", deployment, "-n", self.namespace, "-o", "json"]
            result = self.run_kubectl_command(cmd)
            
            if not result["success"]:
                deployment_status[deployment] = {"error": result["error"]}
                continue
            
            try:
                dep_data = json.loads(result["output"])
                status = dep_data["status"]
                
                deployment_status[deployment] = {
                    "replicas": status.get("replicas", 0),
                    "ready_replicas": status.get("readyReplicas", 0),
                    "available_replicas": status.get("availableReplicas", 0),
                    "updated_replicas": status.get("updatedReplicas", 0),
                    "conditions": status.get("conditions", [])
                }
                
            except (json.JSONDecodeError, KeyError) as e:
                deployment_status[deployment] = {"error": f"解析失敗: {e}"}
        
        return deployment_status
    
    def get_service_status(self) -> Dict[str, Any]:
        """取得Service狀態"""
        cmd = ["kubectl", "get", "services", "-n", self.namespace, "-o", "json"]
        result = self.run_kubectl_command(cmd)
        
        if not result["success"]:
            return {"error": result["error"]}
        
        try:
            services_data = json.loads(result["output"])
            services_status = {}
            
            for service in services_data.get("items", []):
                service_name = service["metadata"]["name"]
                service_type = service["spec"]["type"]
                ports = service["spec"].get("ports", [])
                
                services_status[service_name] = {
                    "type": service_type,
                    "ports": [{"port": p["port"], "target_port": p.get("targetPort")} for p in ports],
                    "cluster_ip": service["spec"].get("clusterIP"),
                    "external_ip": service["status"].get("loadBalancer", {}).get("ingress", [])
                }
            
            return {"services": services_status}
            
        except json.JSONDecodeError as e:
            return {"error": f"解析Service狀態失敗: {e}"}
    
    def check_api_health(self) -> Dict[str, Any]:
        """檢查API健康狀況"""
        # 嘗試端口轉發連接到API
        try:
            # 找到backend pod
            cmd = ["kubectl", "get", "pods", "-n", self.namespace, 
                   "-l", "app=patent-rpa-backend", "-o", "jsonpath={.items[0].metadata.name}"]
            result = self.run_kubectl_command(cmd)
            
            if not result["success"] or not result["output"].strip():
                return {"error": "找不到backend pod"}
            
            pod_name = result["output"].strip()
            
            # 執行健康檢查
            cmd = ["kubectl", "exec", pod_name, "-n", self.namespace, "--", 
                   "curl", "-f", "-s", "http://localhost:8000/health"]
            result = self.run_kubectl_command(cmd)
            
            if result["success"]:
                try:
                    health_data = json.loads(result["output"])
                    return {"status": "healthy", "data": health_data}
                except json.JSONDecodeError:
                    return {"status": "healthy", "data": result["output"]}
            else:
                return {"status": "unhealthy", "error": result["error"]}
                
        except Exception as e:
            return {"error": f"健康檢查失敗: {e}"}
    
    def get_logs(self, deployment: str, lines: int = 50) -> Dict[str, Any]:
        """取得應用程式日誌"""
        cmd = ["kubectl", "logs", f"deployment/{deployment}", 
               "-n", self.namespace, "--tail", str(lines)]
        result = self.run_kubectl_command(cmd)
        
        if result["success"]:
            return {"logs": result["output"]}
        else:
            return {"error": result["error"]}
    
    def print_status_report(self):
        """印出完整狀態報告"""
        print(f"\n{'='*60}")
        print(f"RPA專利系統部署狀態報告")
        print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"命名空間: {self.namespace}")
        print(f"{'='*60}")
        
        # Pod狀態
        print(f"\n📦 Pod 狀態:")
        print("-" * 40)
        pod_status = self.get_pod_status()
        if "error" in pod_status:
            print(f"❌ 錯誤: {pod_status['error']}")
        else:
            for pod_name, status in pod_status["pods"].items():
                ready_icon = "✅" if status["ready"] else "❌"
                print(f"{ready_icon} {pod_name}")
                print(f"   狀態: {status['status']}")
                print(f"   就緒: {status['ready']}")
                print(f"   重啟次數: {status['restart_count']}")
        
        # Deployment狀態
        print(f"\n🚀 Deployment 狀態:")
        print("-" * 40)
        dep_status = self.get_deployment_status()
        for dep_name, status in dep_status.items():
            if "error" in status:
                print(f"❌ {dep_name}: {status['error']}")
            else:
                ready = status["ready_replicas"]
                total = status["replicas"]
                icon = "✅" if ready == total and total > 0 else "❌"
                print(f"{icon} {dep_name}: {ready}/{total} 就緒")
        
        # Service狀態
        print(f"\n🌐 Service 狀態:")
        print("-" * 40)
        svc_status = self.get_service_status()
        if "error" in svc_status:
            print(f"❌ 錯誤: {svc_status['error']}")
        else:
            for svc_name, status in svc_status["services"].items():
                print(f"🔗 {svc_name} ({status['type']})")
                for port in status["ports"]:
                    print(f"   端口: {port['port']} -> {port['target_port']}")
        
        # API健康檢查
        print(f"\n🏥 API 健康檢查:")
        print("-" * 40)
        health = self.check_api_health()
        if "error" in health:
            print(f"❌ 錯誤: {health['error']}")
        elif health["status"] == "healthy":
            print("✅ API 健康狀況良好")
        else:
            print(f"❌ API 不健康: {health.get('error', '未知錯誤')}")
    
    def monitor_continuously(self, interval: int = 30):
        """持續監控模式"""
        print(f"開始持續監控模式 (每{interval}秒更新)")
        print("按 Ctrl+C 停止監控")
        
        try:
            while True:
                self.print_status_report()
                print(f"\n下次更新: {interval}秒後...")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n監控已停止")

def main():
    parser = argparse.ArgumentParser(description="RPA專利系統部署監控")
    parser.add_argument("--namespace", "-n", default="patent-rpa-system", 
                       help="Kubernetes命名空間")
    parser.add_argument("--continuous", "-c", action="store_true", 
                       help="持續監控模式")
    parser.add_argument("--interval", "-i", type=int, default=30, 
                       help="持續監控間隔(秒)")
    parser.add_argument("--logs", "-l", metavar="DEPLOYMENT", 
                       help="顯示指定deployment的日誌")
    parser.add_argument("--lines", type=int, default=50, 
                       help="顯示日誌行數")
    
    args = parser.parse_args()
    
    monitor = DeploymentMonitor(args.namespace)
    
    if args.logs:
        print(f"📋 {args.logs} 日誌 (最後 {args.lines} 行):")
        print("="*60)
        logs = monitor.get_logs(args.logs, args.lines)
        if "error" in logs:
            print(f"❌ 錯誤: {logs['error']}")
        else:
            print(logs["logs"])
    elif args.continuous:
        monitor.monitor_continuously(args.interval)
    else:
        monitor.print_status_report()

if __name__ == "__main__":
    main()