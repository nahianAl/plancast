#!/usr/bin/env python3
"""
Local Testing Launcher
This script provides an easy way to run different types of local tests.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Print a nice banner"""
    print("=" * 60)
    print("🏠 PLANCAST 3D MODEL GENERATION - LOCAL TESTING")
    print("=" * 60)
    print()

def print_menu():
    """Print the main menu"""
    print("Choose a test to run:")
    print()
    print("1. 🧪 Basic 3D Generation Test")
    print("   - Tests room and wall generation with mock data")
    print("   - Creates 3D models and exports them")
    print("   - Generates HTML viewer for results")
    print()
    print("2. 🎨 3D Visualization Test")
    print("   - Creates interactive 3D plots using matplotlib")
    print("   - Shows both 3D and 2D floor plan views")
    print("   - Saves high-quality PNG images")
    print()
    print("3. 🚀 Real Pipeline Test")
    print("   - Tests actual CubiCasa integration with real images")
    print("   - Tests coordinate scaling and 3D generation")
    print("   - Creates detailed test reports")
    print()
    print("4. 🎯 Custom Image Test")
    print("   - Test with your own floor plan image")
    print("   - Interactive room selection and dimension input")
    print("   - Creates personalized 3D models and viewers")
    print()
    print("5. 🔍 View Previous Results")
    print("   - Opens the output directory to see previous results")
    print()
    print("5. 🔍 View Previous Results")
    print("   - Opens the output directory to see previous results")
    print()
    print("6. 🧹 Clean Output Directories")
    print("   - Removes all previous test outputs")
    print()
    print("0. 🚪 Exit")
    print()

def run_basic_test():
    """Run the basic 3D generation test"""
    print("🚀 Running Basic 3D Generation Test...")
    print()
    
    try:
        result = subprocess.run([sys.executable, "test_3d_generation_local.py"], 
                              capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ Basic test completed successfully!")
        else:
            print(f"\n❌ Basic test failed with return code: {result.returncode}")
            
    except Exception as e:
        print(f"\n💥 Error running basic test: {str(e)}")

def run_visualization_test():
    """Run the 3D visualization test"""
    print("🎨 Running 3D Visualization Test...")
    print()
    
    try:
        result = subprocess.run([sys.executable, "test_3d_visualization.py"], 
                              capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ Visualization test completed successfully!")
        else:
            print(f"\n❌ Visualization test failed with return code: {result.returncode}")
            
    except Exception as e:
        print(f"\n💥 Error running visualization test: {str(e)}")

def run_real_pipeline_test():
    """Run the real pipeline test"""
    print("🚀 Running Real Pipeline Test...")
    print()
    
    try:
        result = subprocess.run([sys.executable, "test_real_pipeline_local.py"], 
                              capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ Real pipeline test completed successfully!")
        else:
            print(f"\n❌ Real pipeline test failed with return code: {result.returncode}")
            
    except Exception as e:
        print(f"\n💥 Error running real pipeline test: {str(e)}")

def run_custom_image_test():
    """Run the custom image test"""
    print("🎯 Running Custom Image Test...")
    print()
    
    try:
        result = subprocess.run([sys.executable, "test_custom_image.py"], 
                              capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ Custom image test completed successfully!")
        else:
            print(f"\n❌ Custom image test failed with return code: {result.returncode}")
            
    except Exception as e:
        print(f"\n💥 Error running custom image test: {str(e)}")

def view_results():
    """Open the output directory to view results"""
    print("🔍 Opening output directory...")
    
    output_dir = Path("output")
    if not output_dir.exists():
        print("❌ Output directory not found. Run some tests first!")
        return
    
    try:
        if sys.platform == "darwin":  # macOS
            subprocess.run(["open", str(output_dir)])
        elif sys.platform == "win32":  # Windows
            subprocess.run(["explorer", str(output_dir)])
        else:  # Linux
            subprocess.run(["xdg-open", str(output_dir)])
        
        print("✅ Output directory opened!")
        
        # List contents
        print("\n📁 Output directory contents:")
        for item in output_dir.iterdir():
            if item.is_dir():
                print(f"   📁 {item.name}/")
                # List files in subdirectories
                for subitem in item.iterdir():
                    if subitem.is_file():
                        size = subitem.stat().st_size
                        size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                        print(f"      📄 {subitem.name} ({size_str})")
            else:
                size = item.stat().st_size
                size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                print(f"   📄 {item.name} ({size_str})")
                
    except Exception as e:
        print(f"❌ Error opening output directory: {str(e)}")

def clean_outputs():
    """Clean all output directories"""
    print("🧹 Cleaning output directories...")
    
    output_dir = Path("output")
    if not output_dir.exists():
        print("✅ No output directory to clean!")
        return
    
    try:
        # Remove all contents
        for item in output_dir.iterdir():
            if item.is_file():
                item.unlink()
                print(f"   🗑️  Deleted file: {item.name}")
            elif item.is_dir():
                for subitem in item.iterdir():
                    if subitem.is_file():
                        subitem.unlink()
                        print(f"   🗑️  Deleted file: {item.name}/{subitem.name}")
                item.rmdir()
                print(f"   🗑️  Deleted directory: {item.name}")
        
        print("✅ All outputs cleaned!")
        
    except Exception as e:
        print(f"❌ Error cleaning outputs: {str(e)}")

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    required_modules = [
        'numpy',
        'matplotlib',
        'PIL',
        'pathlib'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} - MISSING")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n⚠️  Missing modules: {', '.join(missing_modules)}")
        print("   Install them with: pip install " + " ".join(missing_modules))
        return False
    else:
        print("\n✅ All dependencies available!")
        return True

def main():
    """Main function"""
    print_banner()
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Please install missing dependencies before running tests.")
        return
    
    print()
    
    while True:
        print_menu()
        
        try:
            choice = input("Enter your choice (0-5): ").strip()
            
            if choice == "0":
                print("\n👋 Goodbye!")
                break
            elif choice == "1":
                run_basic_test()
            elif choice == "2":
                run_visualization_test()
            elif choice == "3":
                run_real_pipeline_test()
            elif choice == "4":
                run_custom_image_test()
            elif choice == "5":
                view_results()
            elif choice == "6":
                clean_outputs()
            else:
                print("\n❌ Invalid choice. Please enter a number between 0 and 6.")
            
            print("\n" + "="*60 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n💥 Unexpected error: {str(e)}")
            print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
