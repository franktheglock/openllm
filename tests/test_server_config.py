"""
Test script to verify per-server LLM configuration functionality.
"""
import os
import sys
import sqlite3
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.manager import ConfigManager


def test_per_server_config():
    """Test that each server can have independent configuration."""
    print("\n" + "="*60)
    print("Testing Per-Server Configuration")
    print("="*60 + "\n")
    
    # Create a test database in a temporary location
    test_db = Path(__file__).parent / "test_bot.db"
    if test_db.exists():
        test_db.unlink()
    
    try:
        # Initialize config manager with test database
        config_manager = ConfigManager()
        config_manager.db_path = test_db
        config_manager._init_database()
        
        # Simulate two different Discord servers with realistic IDs
        TEST_SERVER_1_ID = "123456789"  # Gaming Community server
        TEST_SERVER_2_ID = "987654321"  # Dev Team server
    
        print("1. Testing independent server configurations...")
    
        # Set configuration for Server 1
        server1_config = {
            'llm_provider': 'openai',
            'llm_model': 'gpt-4',
            'temperature': 0.7,
            'max_tokens': 2048,
            'system_prompt': 'You are a helpful assistant for Server 1.',
            'enabled_tools': ['web_search', 'calculator']
        }
        config_manager.set_server_config(TEST_SERVER_1_ID, server1_config)
        print(f"   ✅ Set config for Server 1 (ID: {TEST_SERVER_1_ID})")
    
        # Set configuration for Server 2
        server2_config = {
            'llm_provider': 'anthropic',
            'llm_model': 'claude-3-opus-20240229',
            'temperature': 0.5,
            'max_tokens': 4096,
            'system_prompt': 'You are a professional assistant for Server 2.',
            'enabled_tools': ['web_search']
        }
        config_manager.set_server_config(TEST_SERVER_2_ID, server2_config)
        print(f"   ✅ Set config for Server 2 (ID: {TEST_SERVER_2_ID})")
    
        print("\n2. Verifying configurations are isolated...")
    
        # Retrieve and verify Server 1 configuration
        retrieved_config1 = config_manager.get_server_config(TEST_SERVER_1_ID)
        assert retrieved_config1['llm_provider'] == 'openai', "Server 1 provider mismatch"
        assert retrieved_config1['llm_model'] == 'gpt-4', "Server 1 model mismatch"
        assert retrieved_config1['system_prompt'] == 'You are a helpful assistant for Server 1.', "Server 1 system prompt mismatch"
        assert retrieved_config1['temperature'] == 0.7, "Server 1 temperature mismatch"
        print(f"   ✅ Server 1 config verified:")
        print(f"      Provider: {retrieved_config1['llm_provider']}")
        print(f"      Model: {retrieved_config1['llm_model']}")
        print(f"      System Prompt: {retrieved_config1['system_prompt'][:50]}...")
    
        # Retrieve and verify Server 2 configuration
        retrieved_config2 = config_manager.get_server_config(TEST_SERVER_2_ID)
        assert retrieved_config2['llm_provider'] == 'anthropic', "Server 2 provider mismatch"
        assert retrieved_config2['llm_model'] == 'claude-3-opus-20240229', "Server 2 model mismatch"
        assert retrieved_config2['system_prompt'] == 'You are a professional assistant for Server 2.', "Server 2 system prompt mismatch"
        assert retrieved_config2['temperature'] == 0.5, "Server 2 temperature mismatch"
        print(f"   ✅ Server 2 config verified:")
        print(f"      Provider: {retrieved_config2['llm_provider']}")
        print(f"      Model: {retrieved_config2['llm_model']}")
        print(f"      System Prompt: {retrieved_config2['system_prompt'][:50]}...")
    
        print("\n3. Testing configuration updates...")
    
        # Update Server 1 configuration
        server1_config['system_prompt'] = 'Updated system prompt for Server 1'
        config_manager.set_server_config(TEST_SERVER_1_ID, server1_config)
    
        # Verify Server 1 was updated
        updated_config1 = config_manager.get_server_config(TEST_SERVER_1_ID)
        assert updated_config1['system_prompt'] == 'Updated system prompt for Server 1', "Server 1 update failed"
        print(f"   ✅ Server 1 system prompt updated successfully")
    
        # Verify Server 2 was NOT affected
        unchanged_config2 = config_manager.get_server_config(TEST_SERVER_2_ID)
        assert unchanged_config2['system_prompt'] == 'You are a professional assistant for Server 2.', "Server 2 was incorrectly modified"
        print(f"   ✅ Server 2 remains unchanged (isolation verified)")
    
        print("\n4. Testing database-level verification...")
    
        # Direct database query to ensure isolation
        with sqlite3.connect(test_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT server_id, llm_provider, llm_model, system_prompt FROM server_config")
            rows = cursor.fetchall()
        
            assert len(rows) == 2, f"Expected 2 server configs, found {len(rows)}"
            print(f"   ✅ Database contains exactly 2 server configurations")
        
            for row in rows:
                server_id, provider, model, prompt = row
                if server_id == TEST_SERVER_1_ID:
                    assert provider == 'openai', "DB: Server 1 provider mismatch"
                    assert model == 'gpt-4', "DB: Server 1 model mismatch"
                    print(f"   ✅ Database record for Server 1 is correct")
                elif server_id == TEST_SERVER_2_ID:
                    assert provider == 'anthropic', "DB: Server 2 provider mismatch"
                    assert model == 'claude-3-opus-20240229', "DB: Server 2 model mismatch"
                    print(f"   ✅ Database record for Server 2 is correct")
    
        print("\n" + "="*60)
        print("✅ All Tests Passed!")
        print("="*60)
        print("\nPer-server configuration is working correctly:")
        print("  • Each server can have its own LLM provider")
        print("  • Each server can have its own model")
        print("  • Each server can have its own system prompt")
        print("  • Each server can have its own temperature/max_tokens")
        print("  • Configurations are properly isolated in the database")
        print("  • Updates to one server don't affect others")
        print("="*60 + "\n")
    
    finally:
        # Cleanup test database
        if test_db.exists():
            test_db.unlink()

    
if __name__ == "__main__":
    try:
        test_per_server_config()
    except AssertionError as e:
        print(f"\n❌ Test Failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
