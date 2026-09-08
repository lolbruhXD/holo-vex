"""
Theme System - Visual themes for holographic effects.
"""


class ThemeManager:
    """Manages visual themes for holographic objects."""

    def __init__(self):
        self.themes = {
            'cyan': {
                'name': 'Cyan',
                'primary': (255, 180, 50),      # BGR: Cyan
                'secondary': (180, 140, 30),
                'glow': (255, 200, 80),
                'particle': (255, 180, 50),
                'hud': (255, 180, 50),
            },
            'purple': {
                'name': 'Purple',
                'primary': (220, 100, 180),     # BGR: Purple
                'secondary': (160, 70, 130),
                'glow': (240, 120, 200),
                'particle': (220, 100, 180),
                'hud': (220, 100, 180),
            },
            'green': {
                'name': 'Green',
                'primary': (100, 255, 100),     # BGR: Green
                'secondary': (70, 180, 70),
                'glow': (120, 255, 120),
                'particle': (100, 255, 100),
                'hud': (100, 255, 100),
            },
            'amber': {
                'name': 'Amber',
                'primary': (80, 180, 255),      # BGR: Amber
                'secondary': (50, 130, 200),
                'glow': (100, 200, 255),
                'particle': (80, 180, 255),
                'hud': (80, 180, 255),
            },
        }

        self.theme_order = ['cyan', 'purple', 'green', 'amber']
        self.current_theme_name = 'cyan'

    def get_current_theme(self):
        """Get current theme dictionary."""
        return self.themes[self.current_theme_name]

    def get_theme_name(self):
        """Get current theme name."""
        return self.themes[self.current_theme_name]['name']

    def set_theme(self, theme_name):
        """Set theme by name."""
        if theme_name in self.themes:
            self.current_theme_name = theme_name
            return True
        return False

    def cycle_theme(self):
        """Cycle to next theme."""
        current_index = self.theme_order.index(self.current_theme_name)
        next_index = (current_index + 1) % len(self.theme_order)
        self.current_theme_name = self.theme_order[next_index]
        return self.current_theme_name

    def get_all_themes(self):
        """Get list of all theme names."""
        return self.theme_order.copy()

    def get_theme_color(self, color_key='primary'):
        """Get specific color from current theme."""
        return self.themes[self.current_theme_name].get(color_key, (255, 255, 255))
