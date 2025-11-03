"""
Quick installation check for Discord LLM Bot.
Run this before starting the bot to verify all dependencies are installed.
"""
import sys

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("\n" + "="*60)
    print("Discord LLM Bot - Dependency Check")
    print("="*60 + "\n")
    
    required = {
        'discord': 'discord.py',
        'openai': 'openai',
        'anthropic': 'anthropic',
        'google.generativeai': 'google-generativeai',
        'ollama': 'ollama',
        'flask': 'flask',
        'customtkinter': 'customtkinter',
        'yaml': 'pyyaml',
        'dotenv': 'python-dotenv',
        'aiohttp': 'aiohttp',
        'requests': 'requests',
    }
    
    missing = []
    installed = []
    
    for module, package in required.items():
        try:
            __import__(module)
            installed.append(f"✅ {package:30} INSTALLED")
        except ImportError:
            missing.append(f"❌ {package:30} MISSING")
    
    # Print results
    for item in installed:
        print(item)
    
    if missing:
        print("\n" + "="*60)
        print("MISSING DEPENDENCIES:")
        print("="*60)
        for item in missing:
            print(item)
        
        print("\n" + "="*60)
        print("To install missing dependencies:")
        print("="*60)
        print("pip install -r requirements.txt")
        print("="*60 + "\n")
        return False
    else:
        print("\n" + "="*60)
        print("✅ All dependencies installed!")
        print("="*60)
        print("\nYou can now run:")
        print("  python main.py --reset    # Reset and setup")
        print("  python main.py --setup    # Run setup")
        print("  python main.py            # Start bot")
        print("="*60 + "\n")
        return True

if __name__ == "__main__":
    success = check_dependencies()
    sys.exit(0 if success else 1)
