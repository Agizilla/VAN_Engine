#!/usr/bin/env python3
"""
VoiceAdapter Studio - Installation Test
Verifies that the installation is correct and all components are working.
"""

import sys
from pathlib import Path


def test_file_structure():
    """Test that all required files exist."""
    print("Testing file structure...")
    
    required_files = [
        "main.py",
        "cli.py",
        "gui.py",
        "adapter.py",
        "marketplace.py",
        "requirements.txt",
        "README.md",
        "TASKS.md",
        "LICENSE"
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return False
    
    print("✅ All required files present")
    return True


def test_directories():
    """Test that all required directories exist."""
    print("Testing directory structure...")
    
    required_dirs = [
        "models",
        "adapters",
        "outputs",
        "marketplace_data"
    ]
    
    missing = []
    for directory in required_dirs:
        if not Path(directory).exists():
            missing.append(directory)
    
    if missing:
        print(f"❌ Missing directories: {', '.join(missing)}")
        return False
    
    print("✅ All required directories present")
    return True


def test_imports():
    """Test that all modules can be imported."""
    print("Testing module imports...")
    
    modules = [
        ("adapter", "AdapterConfig, AdapterTrainer, AdapterInference"),
        ("marketplace", "Marketplace"),
        ("cli", "CLI"),
    ]
    
    failed = []
    for module_name, imports in modules:
        try:
            module = __import__(module_name)
            print(f"   ✓ {module_name}")
        except ImportError as e:
            failed.append((module_name, str(e)))
            print(f"   ✗ {module_name}: {e}")
    
    if failed:
        print(f"❌ Failed to import {len(failed)} module(s)")
        return False
    
    print("✅ All modules import successfully")
    return True


def test_dependencies():
    """Test that core dependencies are available."""
    print("Testing dependencies...")
    
    dependencies = [
        "torch",
        "numpy",
        "soundfile",
        "librosa",
        "gradio"
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"   ✓ {dep}")
        except ImportError:
            missing.append(dep)
            print(f"   ✗ {dep} (not installed)")
    
    if missing:
        print(f"⚠️  Missing dependencies: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies available")
    return True


def test_marketplace():
    """Test marketplace functionality."""
    print("Testing marketplace...")
    
    try:
        from marketplace import Marketplace
        
        marketplace = Marketplace()
        adapters = marketplace.get_all_adapters()
        
        if len(adapters) == 0:
            print("⚠️  Marketplace has no adapters")
            return False
        
        print(f"   ✓ Loaded {len(adapters)} marketplace adapters")
        
        # Test categories
        categories = marketplace.get_categories()
        print(f"   ✓ Found {len(categories)} categories")
        
        # Test search
        results = marketplace.search("pop")
        print(f"   ✓ Search working ({len(results)} results for 'pop')")
        
        print("✅ Marketplace functional")
        return True
        
    except Exception as e:
        print(f"❌ Marketplace test failed: {e}")
        return False


def test_adapter_module():
    """Test adapter module basics."""
    print("Testing adapter module...")
    
    try:
        from adapter import VoiceAdapter, AdapterConfig, list_adapters
        
        # Test adapter creation
        adapter = VoiceAdapter(adapter_dim=32)
        size = adapter.get_size_mb()
        print(f"   ✓ Created test adapter ({size:.2f} MB)")
        
        # Test config
        config = AdapterConfig(mode="ordinary")
        print(f"   ✓ Config created (device: {config.device})")
        
        # Test list_adapters
        adapters = list_adapters()
        print(f"   ✓ list_adapters() works ({len(adapters)} found)")
        
        print("✅ Adapter module functional")
        return True
        
    except Exception as e:
        print(f"❌ Adapter test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*60)
    print("VoiceAdapter Studio - Installation Test")
    print("="*60 + "\n")
    
    tests = [
        ("File Structure", test_file_structure),
        ("Directories", test_directories),
        ("Dependencies", test_dependencies),
        ("Module Imports", test_imports),
        ("Marketplace", test_marketplace),
        ("Adapter Module", test_adapter_module),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! VoiceAdapter Studio is ready to use.")
        print("\nTo get started:")
        print("   python main.py          # Launch CLI")
        print("   python main.py --gui    # Launch web GUI")
        print("   python demo.py          # Run demonstration")
        return True
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
        print("\nCommon fixes:")
        print("   pip install -r requirements.txt")
        print("   python main.py  (auto-installs dependencies)")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted.")
        sys.exit(1)
