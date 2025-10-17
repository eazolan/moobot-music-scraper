#!/usr/bin/env python3
"""
Moobot Scraper Installation Script
Cross-platform installer for Windows and Linux
"""

import sys
import subprocess
import os
from pathlib import Path


def run_command(cmd, shell=False):
    """Run a command and return success status and output"""
    try:
        result = subprocess.run(
            cmd, 
            shell=shell, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0] if isinstance(cmd, list) else cmd}"


def check_python():
    """Check if Python is installed and get version"""
    print("Checking Python installation...")
    
    # Try different Python commands
    python_commands = ['python', 'python3']
    
    for cmd in python_commands:
        success, output = run_command([cmd, '--version'])
        if success:
            print(f"✓ Found Python: {output}")
            return True, cmd
    
    return False, None


def install_requirements(python_cmd):
    """Install packages from requirements.txt"""
    requirements_file = Path(__file__).parent / 'requirements.txt'
    
    if not requirements_file.exists():
        print("ERROR: requirements.txt not found")
        return False
    
    print("\nInstalling required packages...")
    print("=" * 40)
    
    # Use pip module to ensure we're using the right pip for the Python version
    cmd = [python_cmd, '-m', 'pip', 'install', '-r', str(requirements_file)]
    
    try:
        result = subprocess.run(cmd, check=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install packages (exit code: {e.returncode})")
        print("Try one of the following:")
        print("  - Run with administrator/sudo privileges")
        print("  - Check your internet connection")
        print("  - Update pip: python -m pip install --upgrade pip")
        return False


def main():
    """Main installation function"""
    print("Installing Moobot Scraper Dependencies...")
    print("=" * 42)
    print()
    
    # Check Python installation
    python_available, python_cmd = check_python()
    
    if not python_available:
        print("ERROR: Python is not installed or not in PATH")
        print("Please install Python 3.7+ from https://python.org")
        return 1
    
    # Install requirements
    if not install_requirements(python_cmd):
        return 1
    
    # Success message
    print()
    print("=" * 47)
    print("Installation complete!")
    print("=" * 47)
    print()
    print("To test the scraper, run:")
    print(f"  {python_cmd} test_scraper.py")
    print()
    print("To start continuous monitoring, run:")
    print(f"  {python_cmd} moobot_scraper.py")
    print()
    
    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        
        # On Windows, pause before closing (like the original batch file)
        if os.name == 'nt':
            input("Press Enter to continue...")
        
        sys.exit(exit_code)
    
    except KeyboardInterrupt:
        print("\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)