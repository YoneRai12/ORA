# ruff: noqa: E402, F401, B023, B007, B008
import sys
import unittest


# Mock Discord Objects
class MockUser:
    id = 123
    name = "TestUser"
    discriminator = "0000"


class MockGuild:
    id = 999


class MockInteraction:
    user = MockUser()
    guild = MockGuild()
    channel_id = 111


# Import our new components
# We need to add src to path
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.views.music_dashboard import create_music_embed, format_time


class TestMusicDashboard(unittest.TestCase):
    def test_format_time(self):
        self.assertEqual(format_time(65), "1:05")
        self.assertEqual(format_time(3600), "1:00:00")
        self.assertEqual(format_time(0), "0:00")

    def test_embed_creation_playing(self):
        embed = create_music_embed(
            track_info={"title": "Test Song", "url": "http://example.com"},
            status="Playing",
            play_time_sec=30,
            total_duration_sec=120,
            queue_preview=[{"title": "Next Song"}],
        )
        self.assertEqual(embed.title, "Test Song")
        self.assertIn("Test Song", embed.title)
        self.assertIn("Now Playing: Playing", embed.author.name)
        # Check Progress Bar visual
        self.assertIn("▬", embed.description)
        self.assertIn("0:30 / 2:00", embed.description)

    def test_embed_creation_queue_overflow(self):
        queue = [{"title": f"Song {i}"} for i in range(15)]
        embed = create_music_embed(
            track_info={"title": "Current"},
            status="Playing",
            play_time_sec=0,
            total_duration_sec=0,
            queue_preview=queue,
        )
        self.assertIn("Next Up (15)", embed.fields[0].name)
        self.assertIn("Song 0", embed.fields[0].value)
        self.assertIn("Song 9", embed.fields[0].value)
        self.assertNotIn("Song 10", embed.fields[0].value)  # Should be truncated
        self.assertIn("...and **5** more", embed.fields[0].value)


if __name__ == "__main__":
    unittest.main()
