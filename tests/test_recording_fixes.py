#!/usr/bin/env python3
"""
Test script for recording fixes
Tests the new watchdog, checkpoint, and status functionality
"""

import asyncio
import sys
from datetime import datetime
from audio_recorder import MeetingRecorder

# Mock user class for testing
class MockUser:
    def __init__(self, user_id, display_name):
        self.id = user_id
        self.display_name = display_name

# Mock PCM data class
class MockPCMData:
    def __init__(self, size_bytes=3840):
        # Create fake PCM data (stereo, 16-bit)
        self.pcm = b'\x00' * size_bytes

def test_recorder_basics():
    """Test basic recorder functionality"""
    print("Test 1: Basic Recorder Functionality")
    print("-" * 50)
    
    recorder = MeetingRecorder()
    
    # Check initial status
    status = recorder.get_status()
    print(f"Initial status: {status}")
    assert status['is_stopped'] == False
    assert status['users_recording'] == 0
    assert status['total_bytes'] == 0
    assert status['has_data'] == False
    
    # Write some data
    user1 = MockUser(1, "TestUser1")
    user2 = MockUser(2, "TestUser2")
    
    for i in range(10):
        recorder.write(user1, MockPCMData())
        recorder.write(user2, MockPCMData())
    
    # Check status after writing
    status = recorder.get_status()
    print(f"After writing: {status}")
    assert status['users_recording'] == 2
    assert status['total_bytes'] > 0
    assert status['has_data'] == True
    
    print("✅ Test 1 PASSED\n")

def test_checkpoint():
    """Test checkpoint creation"""
    print("Test 2: Checkpoint Creation")
    print("-" * 50)
    
    recorder = MeetingRecorder()
    
    # Write some data
    user1 = MockUser(1, "TestUser1")
    for i in range(100):  # Write enough data to create a meaningful checkpoint
        recorder.write(user1, MockPCMData())
    
    # Create checkpoint
    checkpoint_data = recorder.create_checkpoint()
    print(f"Checkpoint size: {len(checkpoint_data)} bytes")
    assert len(checkpoint_data) > 0
    
    # Verify it's a valid WAV file
    assert checkpoint_data[:4] == b'RIFF'
    assert checkpoint_data[8:12] == b'WAVE'
    
    print("✅ Test 2 PASSED\n")

def test_status_tracking():
    """Test status tracking over time"""
    print("Test 3: Status Tracking")
    print("-" * 50)
    
    recorder = MeetingRecorder()
    user1 = MockUser(1, "TestUser1")
    
    # Write data
    recorder.write(user1, MockPCMData())
    
    # Check immediately
    status1 = recorder.get_status()
    print(f"Immediately after write: last_audio_seconds_ago = {status1['last_audio_seconds_ago']:.2f}")
    assert status1['last_audio_seconds_ago'] < 1.0
    
    # Wait a bit
    import time
    time.sleep(2)
    
    # Check again
    status2 = recorder.get_status()
    print(f"After 2 seconds: last_audio_seconds_ago = {status2['last_audio_seconds_ago']:.2f}")
    assert status2['last_audio_seconds_ago'] >= 2.0
    
    print("✅ Test 3 PASSED\n")

def test_cleanup():
    """Test cleanup behavior"""
    print("Test 4: Cleanup Behavior")
    print("-" * 50)
    
    recorder = MeetingRecorder()
    user1 = MockUser(1, "TestUser1")
    
    # Write data
    recorder.write(user1, MockPCMData())
    
    # Check data exists
    assert len(recorder.audio_data) > 0
    
    # Cleanup
    recorder.cleanup()
    
    # Check stopped flag
    assert recorder.is_stopped == True
    
    # Data should still exist (for saving)
    assert len(recorder.audio_data) > 0
    
    # Try to write after cleanup (should be ignored)
    recorder.write(user1, MockPCMData())
    
    print("✅ Test 4 PASSED\n")

def test_error_handling():
    """Test error handling in write method"""
    print("Test 5: Error Handling")
    print("-" * 50)
    
    recorder = MeetingRecorder()
    
    # Create callback to track errors
    errors = []
    async def error_callback(e):
        errors.append(e)
    
    recorder.set_error_callback(error_callback)
    
    # Test with None data (should not crash)
    user1 = MockUser(1, "TestUser1")
    recorder.write(user1, None)
    
    # Test with object without pcm attribute
    class BadData:
        pass
    recorder.write(user1, BadData())
    
    print(f"Recorded {len(errors)} errors (callbacks)")
    print("✅ Test 5 PASSED (no crashes)\n")

async def test_watchdog_concept():
    """Test watchdog concept (simplified)"""
    print("Test 6: Watchdog Concept")
    print("-" * 50)
    
    recorder = MeetingRecorder()
    user1 = MockUser(1, "TestUser1")
    
    # Write initial data
    recorder.write(user1, MockPCMData())
    
    # Simulate watchdog check
    async def watchdog_check():
        for i in range(3):
            await asyncio.sleep(1)
            status = recorder.get_status()
            print(f"Watchdog check {i+1}: {status['last_audio_seconds_ago']:.1f}s since audio")
    
    await watchdog_check()
    
    print("✅ Test 6 PASSED\n")

def main():
    """Run all tests"""
    print("=" * 50)
    print("Recording Fixes Test Suite")
    print("=" * 50)
    print()
    
    try:
        test_recorder_basics()
        test_checkpoint()
        test_status_tracking()
        test_cleanup()
        test_error_handling()
        asyncio.run(test_watchdog_concept())
        
        print("=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 50)
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())


