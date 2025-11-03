"""
Test script to verify reset functionality.
Run this to test if --reset properly clears configuration.
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_files():
    """Check which configuration files exist."""
    root = Path(__file__).parent.parent
    
    files_to_check = {
        '.env': root / '.env',
        'config.yaml': root / 'config.yaml',
        'data/': root / 'data',
        'bot_database.db': root / 'bot_database.db'
    }
    
    print("\n" + "="*50)
    print("Configuration Files Status")
    print("="*50)
    
    for name, path in files_to_check.items():
        exists = path.exists()
        status = "✅ EXISTS" if exists else "❌ NOT FOUND"
        print(f"{name:20} {status}")
        
        if exists and path.is_file():
            size = path.stat().st_size
            print(f"{'':20} Size: {size} bytes")
        elif exists and path.is_dir():
            files = list(path.iterdir())
            print(f"{'':20} Contains: {len(files)} items")
    
    print("="*50 + "\n")
    
    # Check if configured
    from src.config.manager import ConfigManager
    config = ConfigManager()
    is_configured = config.is_configured()
    
    print(f"Bot configured: {'✅ YES' if is_configured else '❌ NO'}")
    
    if is_configured:
        print("\nCurrent Configuration:")
        print(f"  Discord Token: {'***' + os.getenv('DISCORD_TOKEN', 'NOT SET')[-10:] if os.getenv('DISCORD_TOKEN') else 'NOT SET'}")
        print(f"  LLM Provider: {config.get('llm.default_provider', 'NOT SET')}")
        print(f"  LLM Model: {config.get('llm.default_model', 'NOT SET')}")
    
    print("\n" + "="*50)
    print("Test Commands:")
    print("="*50)
    print("python main.py --reset    # Reset and run setup")
    print("python main.py --setup    # Just run setup")
    print("python main.py            # Normal start")
    print("="*50 + "\n")

if __name__ == "__main__":
    check_files()
