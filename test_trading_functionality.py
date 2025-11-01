#!/usr/bin/env python3
"""
Quantum Trading System - Functionality Test
Comprehensive test of the dual-repository architecture
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def test_repository_structure():
    """Test if all repositories are properly structured"""
    print("🔍 Testing Repository Structure...")
    
    repos = {
        "public-quantum-trading": "/home/husni/public-quantum-trading",
        "private-quantum-vault": "/home/husni/private-quantum-vault", 
        "api-bridge": "/home/husni/api-bridge"
    }
    
    results = {}
    for name, path in repos.items():
        repo_path = Path(path)
        if repo_path.exists():
            results[name] = {
                "status": "✅ EXISTS",
                "files": len(list(repo_path.rglob("*.py"))),
                "readme": "✅ README.md" if (repo_path / "README.md").exists() else "❌ No README"
            }
        else:
            results[name] = {"status": "❌ MISSING"}
    
    return results

def test_trading_components():
    """Test core trading components"""
    print("\n🧠 Testing Trading Components...")
    
    # Test private vault trading algorithms
    vault_path = Path("/home/husni/private-quantum-vault")
    trading_components = {}
    
    # Alpha strategies
    alpha_dir = vault_path / "alpha-strategies"
    if alpha_dir.exists():
        trading_components["alpha_strategies"] = {
            "quantum_optimizer": (alpha_dir / "quantum_optimizer.py").exists(),
            "classical_optimizer": (alpha_dir / "classical_optimizer.py").exists()
        }
    
    # Brain AI components  
    brain_dir = vault_path / "brain"
    if brain_dir.exists():
        trading_components["ai_brain"] = {
            "predictors": len(list(brain_dir.glob("*predictor*.py"))),
            "models": len(list(brain_dir.glob("models/*.py")))
        }
    
    # Risk management
    risk_dir = vault_path / "risk-brain"
    if risk_dir.exists():
        trading_components["risk_management"] = {
            "risk_models": len(list(risk_dir.glob("*.py")))
        }
    
    return trading_components

def test_bridge_functionality():
    """Test API bridge components"""
    print("\n🌉 Testing Bridge Functionality...")
    
    bridge_path = Path("/home/husni/api-bridge")
    bridge_components = {}
    
    # Security components
    auth_dir = bridge_path / "auth"
    if auth_dir.exists():
        bridge_components["authentication"] = {
            "mfa_system": (auth_dir / "mfa.py").exists()
        }
    
    # Bridge core
    bridge_core = bridge_path / "bridge"
    if bridge_core.exists():
        bridge_components["bridge_core"] = {
            "controller": (bridge_core / "controller.py").exists(),
            "data_sanitizer": (bridge_core / "data_sanitizer.py").exists()
        }
    
    # Configuration
    config_dir = bridge_path / "config"
    if config_dir.exists():
        bridge_components["configuration"] = {
            "config_manager": (config_dir / "manager.py").exists()
        }
    
    # Deployment
    docker_dir = bridge_path / "docker"
    if docker_dir.exists():
        bridge_components["deployment"] = {
            "dockerfile": (docker_dir / "Dockerfile").exists(),
            "requirements": (bridge_path / "requirements.txt").exists()
        }
    
    return bridge_components

def test_dependencies():
    """Test Python dependencies"""
    print("\n📦 Testing Dependencies...")
    
    dependencies = {}
    
    # Core scientific libraries
    try:
        import numpy as np
        dependencies["numpy"] = f"✅ {np.__version__}"
    except ImportError:
        dependencies["numpy"] = "❌ NOT INSTALLED"
    
    try:
        import pandas as pd
        dependencies["pandas"] = f"✅ {pd.__version__}"
    except ImportError:
        dependencies["pandas"] = "❌ NOT INSTALLED"
    
    # Quantum computing
    try:
        import qiskit
        dependencies["qiskit"] = f"✅ {qiskit.__version__}"
    except ImportError:
        dependencies["qiskit"] = "❌ NOT INSTALLED (CRITICAL)"
    
    # Web framework for bridge
    try:
        import fastapi
        dependencies["fastapi"] = f"✅ {fastapi.__version__}"
    except ImportError:
        dependencies["fastapi"] = "❌ NOT INSTALLED"
    
    return dependencies

def test_public_repository():
    """Test public repository components"""
    print("\n🔓 Testing Public Repository...")
    
    public_path = Path("/home/husni/public-quantum-trading")
    public_components = {}
    
    if public_path.exists():
        # Check core structure
        public_components["core_infrastructure"] = (public_path / "core").exists()
        public_components["api_gateway"] = (public_path / "api-gateway").exists()
        public_components["data_ingestion"] = (public_path / "data-ingestion").exists()
        public_components["documentation"] = (public_path / "docs").exists()
        public_components["community_framework"] = (public_path / "community").exists()
    
    return public_components

def generate_functionality_report():
    """Generate comprehensive functionality report"""
    print("🚀 QUANTUM TRADING SYSTEM - FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Test all components
    repo_test = test_repository_structure()
    trading_test = test_trading_components()
    bridge_test = test_bridge_functionality()
    deps_test = test_dependencies()
    public_test = test_public_repository()
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "system_status": "ANALYSIS COMPLETE",
        "repositories": repo_test,
        "trading_components": trading_test,
        "bridge_components": bridge_test,
        "dependencies": deps_test,
        "public_components": public_test
    }
    
    # Print detailed results
    print("\n📊 DETAILED RESULTS:")
    print("-" * 40)
    
    print("\n🔍 Repository Structure:")
    for repo, status in repo_test.items():
        print(f"  {repo}: {status['status']}")
        if 'files' in status:
            print(f"    - Python files: {status['files']}")
            print(f"    - Documentation: {status['readme']}")
    
    print("\n🧠 Trading Components:")
    for component, details in trading_test.items():
        print(f"  {component}:")
        for item, status in details.items():
            print(f"    - {item}: {'✅' if status else '❌'}")
    
    print("\n🌉 Bridge Components:")
    for component, details in bridge_test.items():
        print(f"  {component}:")
        for item, status in details.items():
            print(f"    - {item}: {'✅' if status else '❌'}")
    
    print("\n📦 Dependencies:")
    for dep, status in deps_test.items():
        print(f"  {dep}: {status}")
    
    print("\n🔓 Public Repository:")
    for component, status in public_test.items():
        print(f"  {component}: {'✅' if status else '❌'}")
    
    # Summary
    print("\n📈 FUNCTIONALITY SUMMARY:")
    print("-" * 40)
    
    # Count working components
    working_repos = sum(1 for r in repo_test.values() if "✅" in str(r.get("status", "")))
    working_deps = sum(1 for d in deps_test.values() if "✅" in d)
    
    print(f"📁 Repositories: {working_repos}/3 operational")
    print(f"🔧 Dependencies: {working_deps}/{len(deps_test)} installed")
    
    # Check critical issues
    critical_issues = []
    if "❌ NOT INSTALLED (CRITICAL)" in deps_test.get("qiskit", ""):
        critical_issues.append("Qiskit not installed - quantum features unavailable")
    
    if not bridge_test.get("authentication", {}).get("mfa_system"):
        critical_issues.append("Bridge MFA system missing")
    
    if critical_issues:
        print(f"\n🚨 CRITICAL ISSUES:")
        for issue in critical_issues:
            print(f"  - {issue}")
    else:
        print(f"\n✅ NO CRITICAL ISSUES DETECTED")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if "❌ NOT INSTALLED (CRITICAL)" in deps_test.get("qiskit", ""):
        print("  - Install Qiskit: pip install qiskit qiskit-aer")
    
    print("  - Test bridge authentication system")
    print("  - Validate quantum optimization algorithms")
    print("  - Run end-to-end integration tests")
    
    return report

if __name__ == "__main__":
    report = generate_functionality_report()
    
    # Save report
    report_path = "/home/husni/quantum_trading_system/functionality_test_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to: {report_path}")