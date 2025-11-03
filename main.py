"""
Discord LLM Bot - Main Entry Point
"""
import asyncio
import sys
import argparse
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.bot import DiscordLLMBot
from src.utils.logger import setup_logger
from src.config.manager import ConfigManager

logger = setup_logger(__name__)


def reset_configuration():
    """Reset all configuration files for testing purposes."""
    import shutil
    
    files_to_remove = [
        '.env',
        'config.yaml',
        'bot_database.db',
        'data'  # Database directory
    ]
    
    for file_path in files_to_remove:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            try:
                if full_path.is_file():
                    full_path.unlink()
                    logger.info(f"Removed: {file_path}")
                elif full_path.is_dir():
                    shutil.rmtree(full_path)
                    logger.info(f"Removed directory: {file_path}")
            except Exception as e:
                logger.warning(f"Could not remove {file_path}: {e}")
    
    # Also clear any cached configuration
    cache_dir = Path(__file__).parent / '__pycache__'
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir)
            logger.info("Cleared Python cache")
        except Exception as e:
            logger.warning(f"Could not clear cache: {e}")
    
    # Clear src cache as well
    src_cache = Path(__file__).parent / 'src' / '__pycache__'
    if src_cache.exists():
        try:
            shutil.rmtree(src_cache)
        except Exception as e:
            pass
    
    logger.info("✅ Configuration files cleared. Ready for fresh setup.")


async def main():
    """Main entry point for the bot."""
    parser = argparse.ArgumentParser(description="Discord LLM Bot")
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run the setup wizard"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset configuration and run setup wizard (for testing)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to config file"
    )
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Disable the web dashboard"
    )
    
    args = parser.parse_args()
    
    # Handle reset flag - clear configuration and re-run setup
    if args.reset:
        logger.info("Resetting configuration...")
        reset_configuration()
        logger.info("Configuration reset complete. Running setup wizard...")
        args.setup = True
    
    # Run setup wizard if requested or if first launch
    config_manager = ConfigManager()
    if args.setup or not config_manager.is_configured():
        logger.info("Starting GUI setup wizard...")
        # Import here to avoid issues if tkinter not available
        from src.setup_wizard_gui import run_gui_setup
        run_gui_setup()
        logger.info("Setup complete! Starting bot...")
    
    # Initialize and start the bot
    try:
        bot = DiscordLLMBot(
            config_path=args.config,
            enable_dashboard=not args.no_dashboard
        )
        
        logger.info("Starting Discord LLM Bot...")
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
