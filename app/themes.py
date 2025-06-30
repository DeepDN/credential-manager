"""
Themes and Customization for SecureVault
Provides theme management and UI customization options
"""
import json
import os
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# Themes API Router
themes_router = APIRouter(prefix="/api/themes", tags=["themes"])

class ThemeColors(BaseModel):
    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text_primary: str
    text_secondary: str
    success: str
    warning: str
    error: str
    info: str

class Theme(BaseModel):
    id: str
    name: str
    description: str
    colors: ThemeColors
    is_dark: bool
    custom_css: Optional[str] = None
    created_by: str = "system"
    version: str = "1.0"

class CustomizationSettings(BaseModel):
    theme_id: str
    font_family: str = "Inter, sans-serif"
    font_size: str = "14px"
    border_radius: str = "8px"
    animation_speed: str = "0.3s"
    compact_mode: bool = False
    show_icons: bool = True
    sidebar_collapsed: bool = False
    custom_css: Optional[str] = None

class ThemeManager:
    """Manage themes and customization settings"""
    
    def __init__(self):
        self.themes_dir = "./themes"
        self.settings_file = "./user_settings.json"
        self.ensure_directories()
        self.load_default_themes()
        
    def ensure_directories(self):
        """Ensure theme directories exist"""
        os.makedirs(self.themes_dir, exist_ok=True)
        
    def load_default_themes(self):
        """Load default themes"""
        default_themes = self.get_default_themes()
        
        for theme in default_themes:
            theme_file = os.path.join(self.themes_dir, f"{theme.id}.json")
            if not os.path.exists(theme_file):
                self.save_theme(theme)
                
    def get_default_themes(self) -> List[Theme]:
        """Get default theme definitions"""
        return [
            # Light Theme
            Theme(
                id="light",
                name="Light",
                description="Clean light theme with blue accents",
                colors=ThemeColors(
                    primary="#2563eb",
                    secondary="#64748b",
                    accent="#3b82f6",
                    background="#ffffff",
                    surface="#f8fafc",
                    text_primary="#1e293b",
                    text_secondary="#64748b",
                    success="#10b981",
                    warning="#f59e0b",
                    error="#ef4444",
                    info="#3b82f6"
                ),
                is_dark=False,
                created_by="system"
            ),
            
            # Dark Theme
            Theme(
                id="dark",
                name="Dark",
                description="Modern dark theme with blue accents",
                colors=ThemeColors(
                    primary="#3b82f6",
                    secondary="#6b7280",
                    accent="#60a5fa",
                    background="#0f172a",
                    surface="#1e293b",
                    text_primary="#f1f5f9",
                    text_secondary="#94a3b8",
                    success="#10b981",
                    warning="#f59e0b",
                    error="#ef4444",
                    info="#3b82f6"
                ),
                is_dark=True,
                created_by="system"
            ),
            
            # High Contrast Theme
            Theme(
                id="high-contrast",
                name="High Contrast",
                description="High contrast theme for accessibility",
                colors=ThemeColors(
                    primary="#000000",
                    secondary="#666666",
                    accent="#0066cc",
                    background="#ffffff",
                    surface="#f5f5f5",
                    text_primary="#000000",
                    text_secondary="#333333",
                    success="#008000",
                    warning="#ff8c00",
                    error="#cc0000",
                    info="#0066cc"
                ),
                is_dark=False,
                created_by="system"
            ),
            
            # Cyberpunk Theme
            Theme(
                id="cyberpunk",
                name="Cyberpunk",
                description="Futuristic cyberpunk theme with neon colors",
                colors=ThemeColors(
                    primary="#00ff9f",
                    secondary="#bd93f9",
                    accent="#ff79c6",
                    background="#0d1117",
                    surface="#161b22",
                    text_primary="#f0f6fc",
                    text_secondary="#8b949e",
                    success="#00ff9f",
                    warning="#ffb86c",
                    error="#ff5555",
                    info="#8be9fd"
                ),
                is_dark=True,
                created_by="system"
            ),
            
            # Nature Theme
            Theme(
                id="nature",
                name="Nature",
                description="Calming nature-inspired green theme",
                colors=ThemeColors(
                    primary="#059669",
                    secondary="#6b7280",
                    accent="#10b981",
                    background="#f0fdf4",
                    surface="#dcfce7",
                    text_primary="#14532d",
                    text_secondary="#374151",
                    success="#10b981",
                    warning="#d97706",
                    error="#dc2626",
                    info="#0891b2"
                ),
                is_dark=False,
                created_by="system"
            ),
            
            # Ocean Theme
            Theme(
                id="ocean",
                name="Ocean",
                description="Deep ocean blue theme",
                colors=ThemeColors(
                    primary="#0ea5e9",
                    secondary="#64748b",
                    accent="#38bdf8",
                    background="#0c4a6e",
                    surface="#075985",
                    text_primary="#e0f2fe",
                    text_secondary="#bae6fd",
                    success="#10b981",
                    warning="#f59e0b",
                    error="#ef4444",
                    info="#38bdf8"
                ),
                is_dark=True,
                created_by="system"
            )
        ]
        
    def save_theme(self, theme: Theme) -> bool:
        """Save theme to file"""
        try:
            theme_file = os.path.join(self.themes_dir, f"{theme.id}.json")
            with open(theme_file, 'w') as f:
                json.dump(theme.dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save theme {theme.id}: {e}")
            return False
            
    def load_theme(self, theme_id: str) -> Optional[Theme]:
        """Load theme from file"""
        try:
            theme_file = os.path.join(self.themes_dir, f"{theme_id}.json")
            if os.path.exists(theme_file):
                with open(theme_file, 'r') as f:
                    theme_data = json.load(f)
                return Theme(**theme_data)
            return None
        except Exception as e:
            print(f"Failed to load theme {theme_id}: {e}")
            return None
            
    def get_all_themes(self) -> List[Theme]:
        """Get all available themes"""
        themes = []
        
        if os.path.exists(self.themes_dir):
            for filename in os.listdir(self.themes_dir):
                if filename.endswith('.json'):
                    theme_id = filename[:-5]  # Remove .json extension
                    theme = self.load_theme(theme_id)
                    if theme:
                        themes.append(theme)
                        
        return themes
        
    def delete_theme(self, theme_id: str) -> bool:
        """Delete custom theme"""
        try:
            theme = self.load_theme(theme_id)
            if not theme:
                return False
                
            # Don't allow deletion of system themes
            if theme.created_by == "system":
                return False
                
            theme_file = os.path.join(self.themes_dir, f"{theme_id}.json")
            if os.path.exists(theme_file):
                os.remove(theme_file)
                return True
            return False
        except Exception as e:
            print(f"Failed to delete theme {theme_id}: {e}")
            return False
            
    def save_settings(self, settings: CustomizationSettings) -> bool:
        """Save user customization settings"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings.dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save settings: {e}")
            return False
            
    def load_settings(self) -> CustomizationSettings:
        """Load user customization settings"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings_data = json.load(f)
                return CustomizationSettings(**settings_data)
        except Exception as e:
            print(f"Failed to load settings: {e}")
            
        # Return default settings
        return CustomizationSettings(theme_id="light")
        
    def generate_css(self, theme: Theme, settings: CustomizationSettings) -> str:
        """Generate CSS from theme and settings"""
        
        # Generate compact mode CSS if enabled
        compact_mode_css = ""
        if settings.compact_mode:
            compact_mode_css = """
.compact-mode {
    --font-size: 12px;
    --border-radius: 4px;
}

.compact-mode .card {
    padding: 8px 12px;
}

.compact-mode .btn {
    padding: 4px 8px;
    font-size: 12px;
}
"""
        
        # Generate icon CSS if disabled
        icon_css = ""
        if not settings.show_icons:
            icon_css = """
.icon {
    display: none !important;
}
"""

        # Generate sidebar CSS if collapsed
        sidebar_css = ""
        if settings.sidebar_collapsed:
            sidebar_css = """
.sidebar {
    width: 60px;
}

.sidebar .nav-text {
    display: none;
}
"""
        
        css = f"""
/* SecureVault Theme: {theme.name} */
:root {{
    /* Colors */
    --color-primary: {theme.colors.primary};
    --color-secondary: {theme.colors.secondary};
    --color-accent: {theme.colors.accent};
    --color-background: {theme.colors.background};
    --color-surface: {theme.colors.surface};
    --color-text-primary: {theme.colors.text_primary};
    --color-text-secondary: {theme.colors.text_secondary};
    --color-success: {theme.colors.success};
    --color-warning: {theme.colors.warning};
    --color-error: {theme.colors.error};
    --color-info: {theme.colors.info};
    
    /* Typography */
    --font-family: {settings.font_family};
    --font-size: {settings.font_size};
    
    /* Layout */
    --border-radius: {settings.border_radius};
    --animation-speed: {settings.animation_speed};
}}

/* Base styles */
body {{
    font-family: var(--font-family);
    font-size: var(--font-size);
    background-color: var(--color-background);
    color: var(--color-text-primary);
    transition: all var(--animation-speed) ease;
}}

/* Compact mode */
{compact_mode_css}

/* Hide icons if disabled */
{icon_css}

/* Sidebar collapsed */
{sidebar_css}

/* Button styles */
.btn-primary {{
    background-color: var(--color-primary);
    border-color: var(--color-primary);
    color: white;
    border-radius: var(--border-radius);
    transition: all var(--animation-speed) ease;
}}

.btn-primary:hover {{
    background-color: var(--color-accent);
    border-color: var(--color-accent);
}}

/* Card styles */
.card {{
    background-color: var(--color-surface);
    border: 1px solid var(--color-secondary);
    border-radius: var(--border-radius);
    color: var(--color-text-primary);
}}

/* Input styles */
.form-control {{
    background-color: var(--color-surface);
    border: 1px solid var(--color-secondary);
    color: var(--color-text-primary);
    border-radius: var(--border-radius);
}}

.form-control:focus {{
    border-color: var(--color-primary);
    box-shadow: 0 0 0 0.2rem rgba({self._hex_to_rgb(theme.colors.primary)}, 0.25);
}}

/* Alert styles */
.alert-success {{
    background-color: var(--color-success);
    border-color: var(--color-success);
    color: white;
}}

.alert-warning {{
    background-color: var(--color-warning);
    border-color: var(--color-warning);
    color: white;
}}

.alert-danger {{
    background-color: var(--color-error);
    border-color: var(--color-error);
    color: white;
}}

.alert-info {{
    background-color: var(--color-info);
    border-color: var(--color-info);
    color: white;
}}

/* Custom CSS */
{settings.custom_css or ""}
{theme.custom_css or ""}
"""
        return css
        
    def _hex_to_rgb(self, hex_color: str) -> str:
        """Convert hex color to RGB"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"{r}, {g}, {b}"
        return "0, 0, 0"

# Global theme manager
theme_manager = ThemeManager()

@themes_router.get("/", response_model=List[Theme])
async def get_all_themes():
    """Get all available themes"""
    try:
        themes = theme_manager.get_all_themes()
        return themes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get themes: {str(e)}"
        )

@themes_router.get("/{theme_id}", response_model=Theme)
async def get_theme(theme_id: str):
    """Get specific theme"""
    try:
        theme = theme_manager.load_theme(theme_id)
        if not theme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Theme not found"
            )
        return theme
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get theme: {str(e)}"
        )

@themes_router.post("/", response_model=Theme)
async def create_theme(theme: Theme):
    """Create custom theme"""
    try:
        # Set as custom theme
        theme.created_by = "user"
        
        success = theme_manager.save_theme(theme)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save theme"
            )
        return theme
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create theme: {str(e)}"
        )

@themes_router.put("/{theme_id}", response_model=Theme)
async def update_theme(theme_id: str, theme: Theme):
    """Update custom theme"""
    try:
        existing_theme = theme_manager.load_theme(theme_id)
        if not existing_theme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Theme not found"
            )
            
        # Don't allow updating system themes
        if existing_theme.created_by == "system":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update system theme"
            )
        
        theme.id = theme_id
        theme.created_by = "user"
        
        success = theme_manager.save_theme(theme)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update theme"
            )
        return theme
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update theme: {str(e)}"
        )

@themes_router.delete("/{theme_id}")
async def delete_theme(theme_id: str):
    """Delete custom theme"""
    try:
        success = theme_manager.delete_theme(theme_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Theme not found or cannot be deleted"
            )
        return {"status": "deleted", "theme_id": theme_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete theme: {str(e)}"
        )

@themes_router.get("/settings/current", response_model=CustomizationSettings)
async def get_current_settings():
    """Get current customization settings"""
    try:
        settings = theme_manager.load_settings()
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get settings: {str(e)}"
        )

@themes_router.post("/settings", response_model=CustomizationSettings)
async def save_settings(settings: CustomizationSettings):
    """Save customization settings"""
    try:
        success = theme_manager.save_settings(settings)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save settings"
            )
        return settings
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save settings: {str(e)}"
        )

@themes_router.get("/css/current")
async def get_current_css():
    """Get current theme CSS"""
    try:
        settings = theme_manager.load_settings()
        theme = theme_manager.load_theme(settings.theme_id)
        
        if not theme:
            # Fallback to light theme
            theme = theme_manager.load_theme("light")
            
        if not theme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No theme available"
            )
            
        css = theme_manager.generate_css(theme, settings)
        
        return {
            "css": css,
            "theme_id": theme.id,
            "theme_name": theme.name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate CSS: {str(e)}"
        )
