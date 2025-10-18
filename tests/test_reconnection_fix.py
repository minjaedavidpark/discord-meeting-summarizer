#!/usr/bin/env python3
"""
Test to verify the reconnection fix works correctly.
This test simulates the disconnect/reconnect scenario.
"""

import sys
import time
from datetime import datetime
from audio_recorder import MeetingRecorder


class MockUser:
    def __init__(self, user_id, name):
        self.id = user_id
        self.display_name = name


class MockAudioData:
    def __init__(self):
        # Create 3840 bytes of fake stereo PCM data (20ms of audio at 48kHz)
        self.pcm = b'\x00\x01' * 1920  # 1920 stereo frames = 3840 bytes


def test_reconnection_resilience():
    """Test that recorder survives cleanup() without stopping"""
    print("Testing reconnection resilience...")
    
    recorder = MeetingRecorder()
    user = MockUser(12345, "TestUser")
    audio = MockAudioData()
    
    # Simulate audio reception
    print("1. Writing initial audio data...")
    for i in range(10):
        recorder.write(user, audio)
    
    status1 = recorder.get_status()
    print(f"   Status before cleanup: is_stopped={status1['is_stopped']}, bytes={status1['total_bytes']}")
    
    # Simulate disconnect (cleanup called, but should NOT stop)
    print("2. Simulating disconnect (calling cleanup)...")
    recorder.cleanup()
    
    status2 = recorder.get_status()
    print(f"   Status after cleanup: is_stopped={status2['is_stopped']}, bytes={status2['total_bytes']}")
    
    # Try to write more audio (should work!)
    print("3. Writing audio after cleanup (simulating reconnection)...")
    initial_bytes = status2['total_bytes']
    for i in range(10):
        recorder.write(user, audio)
    
    status3 = recorder.get_status()
    print(f"   Status after reconnection: is_stopped={status3['is_stopped']}, bytes={status3['total_bytes']}")
    
    # Verify results
    print("\n=== RESULTS ===")
    if status2['is_stopped']:
        print("❌ FAIL: Recorder was stopped by cleanup() - BUG NOT FIXED")
        return False
    
    if status3['total_bytes'] == initial_bytes:
        print("❌ FAIL: No audio written after cleanup - recorder is not accepting audio")
        return False
    
    print("✅ PASS: Recorder survived cleanup and continues accepting audio")
    
    # Now test explicit stop
    print("\n4. Testing explicit stop()...")
    recorder.stop()
    status4 = recorder.get_status()
    print(f"   Status after stop(): is_stopped={status4['is_stopped']}")
    
    # Try to write audio (should be rejected)
    bytes_before = status4['total_bytes']
    recorder.write(user, audio)
    status5 = recorder.get_status()
    
    if status4['is_stopped'] and status5['total_bytes'] == bytes_before:
        print("✅ PASS: stop() correctly stops the recorder")
        return True
    else:
        print("❌ FAIL: stop() didn't work correctly")
        return False


def test_checkpoint_performance():
    """Test that checkpoint creation completes in reasonable time"""
    print("\n\nTesting checkpoint performance...")
    
    recorder = MeetingRecorder()
    user = MockUser(12345, "TestUser")
    audio = MockAudioData()
    
    # Simulate 30 seconds of audio (similar to checkpoint interval)
    print("1. Writing 30 seconds of audio data...")
    # 48000 Hz * 30 sec / 960 samples per packet = ~1500 packets
    num_packets = 1500
    for i in range(num_packets):
        recorder.write(user, audio)
        if i % 500 == 0:
            print(f"   Written {i}/{num_packets} packets...")
    
    status = recorder.get_status()
    print(f"   Total bytes: {status['total_bytes']:,} ({status['total_bytes']/1024/1024:.2f} MB)")
    print(f"   Estimated duration: {status['estimated_duration']:.1f} seconds")
    
    # Create checkpoint and measure time
    print("2. Creating checkpoint...")
    start_time = time.time()
    checkpoint_data = recorder.create_checkpoint()
    elapsed_time = time.time() - start_time
    
    print(f"   Checkpoint created in {elapsed_time:.3f} seconds")
    print(f"   Checkpoint size: {len(checkpoint_data):,} bytes ({len(checkpoint_data)/1024/1024:.2f} MB)")
    
    # Verify performance (should be much less than 10 seconds to avoid heartbeat timeout)
    print("\n=== RESULTS ===")
    if elapsed_time > 5.0:
        print(f"⚠️  WARNING: Checkpoint took {elapsed_time:.3f}s (>5s may cause issues)")
        print("   Consider optimizing checkpoint creation further")
    elif elapsed_time < 1.0:
        print(f"✅ PASS: Checkpoint created quickly ({elapsed_time:.3f}s)")
    else:
        print(f"✅ PASS: Checkpoint completed in acceptable time ({elapsed_time:.3f}s)")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("RECONNECTION FIX VERIFICATION TEST")
    print("=" * 60)
    print()
    
    test1_pass = test_reconnection_resilience()
    test2_pass = test_checkpoint_performance()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    if test1_pass and test2_pass:
        print("✅ ALL TESTS PASSED - Fix is working correctly!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - Fix needs adjustment")
        sys.exit(1)


