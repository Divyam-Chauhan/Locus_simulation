import pygame
import math
import time
import sys

# --- Constants ---
SPEED_OF_SOUND = 343.0  # m/s
PIXELS_PER_METER = 800.0
PIXELS_PER_SEC = SPEED_OF_SOUND * PIXELS_PER_METER  # 274400 px/s
BASELINE_M = 0.15
MIC_DIST_M = BASELINE_M / 2.0
MIC_DIST_PX = MIC_DIST_M * PIXELS_PER_METER  # 60.0 px
FRIENDLY_FIRE_RADIUS = 100.0 # pixels
MAX_HISTORY_ENTRIES = 8
HISTORY_LIFESPAN_SEC = 300.0 # 5 minutes

# --- Window ---
WIDTH, HEIGHT = 1000, 600
GRID_SIZE = 600
HUD_WIDTH = 400
CENTER_X, CENTER_Y = 300, 300

# --- Colors ---
COLOR_BG = (30, 30, 30)  # Slate grey
COLOR_GRID = (60, 60, 60)
COLOR_WHITE = (255, 255, 255)
COLOR_CYAN = (0, 255, 255)
COLOR_NEON_GREEN = (57, 255, 20)
COLOR_RED = (255, 50, 50)
COLOR_DARK_RED = (80, 20, 20)
COLOR_GRAY = (100, 100, 100)
COLOR_LOCKOUT = (255, 165, 0) # Orange

class Mic:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y
        self.hit_time_us = 0.0
        self.rel_time_us = 0.0
        self.locked = False

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("LOCUS Digital Twin")
        self.font_large = pygame.font.SysFont("consolas", 24, bold=True)
        self.font_medium = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 14)
        
        self.mics = {
            'N': Mic('N', CENTER_X, CENTER_Y - MIC_DIST_PX),
            'E': Mic('E', CENTER_X + MIC_DIST_PX, CENTER_Y),
            'S': Mic('S', CENTER_X, CENTER_Y + MIC_DIST_PX),
            'W': Mic('W', CENTER_X - MIC_DIST_PX, CENTER_Y)
        }
        
        self.mode = "1x" # Modes: "1x", "5x Slower"
        self.click_pos = None
        self.animating = False
        self.friendly_fire = False
        
        # State
        self.wave_radius = 0.0
        self.sim_time_us = 0.0
        self.first_hit_time_us = None
        self.all_hit = False
        self.tdoa_resolved = False
        self.bearing = 0.0
        self.dt_x = 0.0
        self.dt_y = 0.0
        
        self.history = [] # List of dicts: {'angle': float, 'time': float}

    def reset_state(self):
        for m in self.mics.values():
            m.locked = False
            m.hit_time_us = 0.0
            m.rel_time_us = 0.0
        self.first_hit_time_us = None
        self.all_hit = False
        self.tdoa_resolved = False
        self.wave_radius = 0.0
        self.sim_time_us = 0.0
        self.click_pos = None
        self.animating = False
        self.friendly_fire = False

    def angle_diff(self, a1, a2):
        diff = (a1 - a2) % 360.0
        if diff > 180.0:
            diff -= 360.0
        return abs(diff)

    def add_to_history(self, bearing):
        now = time.time()
        matched_idx = -1
        for i, entry in enumerate(self.history):
            if self.angle_diff(entry['angle'], bearing) <= 5.0:
                matched_idx = i
                break
                
        if matched_idx != -1:
            # Pop and update
            entry = self.history.pop(matched_idx)
            entry['angle'] = bearing
            entry['time'] = now
            self.history.insert(0, entry)
        else:
            # Insert new
            self.history.insert(0, {'angle': bearing, 'time': now})
            
        # Enforce max entries
        if len(self.history) > MAX_HISTORY_ENTRIES:
            self.history = self.history[:MAX_HISTORY_ENTRIES]

    def format_time_ago(self, seconds):
        if seconds < 10:
            return "Just now"
        elif seconds < 60:
            return f"{int(seconds)}s ago"
        else:
            mins = int(seconds / 60)
            return f"{mins}m ago"

    def get_fade_color(self, seconds_old):
        # Fades from NEON_GREEN to GRAY over 60 seconds
        max_fade_time = 60.0
        ratio = min(seconds_old / max_fade_time, 1.0)
        
        r = int(57 + (100 - 57) * ratio)
        g = int(255 + (100 - 255) * ratio)
        b = int(20 + (100 - 20) * ratio)
        return (r, g, b)

    def handle_click(self, pos):
        if pos[0] > GRID_SIZE:
            # Mode toggle button rect: (620, 60, 250, 40)
            if 620 <= pos[0] <= 870 and 60 <= pos[1] <= 100:
                self.mode = "5x Slower" if self.mode == "1x" else "1x"
            return
            
        # Ignore clicks if animation is currently running in slow-mo
        if self.animating:
            return
            
        self.reset_state()
        self.click_pos = pos
        
        # Check friendly fire zone
        dist_from_center = math.hypot(pos[0] - CENTER_X, pos[1] - CENTER_Y)
        if dist_from_center < FRIENDLY_FIRE_RADIUS:
            self.friendly_fire = True
            return
        
        # 1. Calculate Absolute TOF
        for name, m in self.mics.items():
            dist_px = math.sqrt((pos[0] - m.x)**2 + (pos[1] - m.y)**2)
            dist_m = dist_px / PIXELS_PER_METER
            time_s = dist_m / SPEED_OF_SOUND
            m.hit_time_us = time_s * 1_000_000.0
            
        self.first_hit_time_us = min(m.hit_time_us for m in self.mics.values())
        
        # 2. Relative Timestamps
        for name, m in self.mics.items():
            m.rel_time_us = m.hit_time_us - self.first_hit_time_us

        # 3. TDOA Math Engine
        self.dt_x = self.mics['E'].hit_time_us - self.mics['W'].hit_time_us
        self.dt_y = self.mics['N'].hit_time_us - self.mics['S'].hit_time_us
        
        # Angle using standard polar coordinates: East=0, North=90, West=180, South=270
        angle_rad = math.atan2(-self.dt_y, -self.dt_x)
        self.bearing = math.degrees(angle_rad) % 360.0
        
        if self.mode == "1x":
            # Instant calculation
            max_hit_time_us = max(m.hit_time_us for m in self.mics.values())
            self.sim_time_us = self.first_hit_time_us + 51000.0 # fast forward past 50ms lockout
            for m in self.mics.values():
                m.locked = True
            self.all_hit = True
            self.tdoa_resolved = True
            self.add_to_history(self.bearing)
        else:
            self.animating = True

    def update(self, dt_real):
        current_time = time.time()
        # Memory overhead cleanup for ESP32 constraints (delete entries older than 5 mins)
        self.history = [h for h in self.history if current_time - h['time'] < HISTORY_LIFESPAN_SEC]

        if self.animating and self.mode == "5x Slower" and not self.friendly_fire:
            visual_speed_px = 300.0 
            self.wave_radius += visual_speed_px * dt_real
            self.sim_time_us = (self.wave_radius / PIXELS_PER_SEC) * 1_000_000.0
            
            all_locked = True
            for m in self.mics.values():
                if not m.locked:
                    if self.sim_time_us >= m.hit_time_us:
                        m.locked = True
                    else:
                        all_locked = False
            
            if all_locked:
                self.all_hit = True
                
                if not self.tdoa_resolved:
                    self.tdoa_resolved = True
                    self.add_to_history(self.bearing)
                
                max_radius = (max(m.hit_time_us for m in self.mics.values()) / 1_000_000.0) * PIXELS_PER_SEC
                # Stop animating once the wave expands just past the furthest mic
                if self.wave_radius > max_radius + 50.0:
                    self.animating = False
                    # Fast forward the physics time past the 50ms lockout so the UI clears it
                    self.sim_time_us = self.first_hit_time_us + 51000.0

    def draw(self):
        self.screen.fill(COLOR_BG)
        
        # --- Tactical Grid ---
        pygame.draw.line(self.screen, COLOR_WHITE, (GRID_SIZE, 0), (GRID_SIZE, HEIGHT), 2)
        for i in range(0, GRID_SIZE, 50):
            pygame.draw.line(self.screen, COLOR_GRID, (i, 0), (i, HEIGHT))
            pygame.draw.line(self.screen, COLOR_GRID, (0, i), (GRID_SIZE, i))
            
        # --- Ghost Trajectory Lines (History) ---
        current_time = time.time()
        for entry in self.history:
            seconds_old = current_time - entry['time']
            color = self.get_fade_color(seconds_old)
            rad = math.radians(entry['angle'])
            dir_x = math.cos(rad)
            dir_y = -math.sin(rad) # Pygame Y grows downwards
            end_x = CENTER_X + dir_x * 800
            end_y = CENTER_Y + dir_y * 800
            pygame.draw.line(self.screen, color, (CENTER_X, CENTER_Y), (end_x, end_y), 1)

        # --- Friendly Fire Zone ---
        pygame.draw.circle(self.screen, COLOR_DARK_RED, (CENTER_X, CENTER_Y), int(FRIENDLY_FIRE_RADIUS), 0)
        pygame.draw.circle(self.screen, COLOR_RED, (CENTER_X, CENTER_Y), int(FRIENDLY_FIRE_RADIUS), 1)
            
        # --- Array ---
        pygame.draw.line(self.screen, COLOR_GRAY, (CENTER_X, CENTER_Y - 80), (CENTER_X, CENTER_Y + 80), 2)
        pygame.draw.line(self.screen, COLOR_GRAY, (CENTER_X - 80, CENTER_Y), (CENTER_X + 80, CENTER_Y), 2)
        
        for name, m in self.mics.items():
            color = COLOR_NEON_GREEN if m.locked else COLOR_WHITE
            pygame.draw.circle(self.screen, color, (int(m.x), int(m.y)), 6)
            txt = self.font_small.render(name, True, COLOR_WHITE)
            self.screen.blit(txt, (m.x + 10, m.y - 10))
            
        # --- Active Shockwave & Trajectory ---
        if self.click_pos:
            click_color = COLOR_RED if self.friendly_fire else COLOR_CYAN
            pygame.draw.circle(self.screen, click_color, (int(self.click_pos[0]), int(self.click_pos[1])), 4)
            
            if not self.friendly_fire:
                # Draw expanding shockwave ONLY in 5x Slower Mode
                if self.mode == "5x Slower" and self.wave_radius > 0:
                    pygame.draw.circle(self.screen, COLOR_CYAN, (int(self.click_pos[0]), int(self.click_pos[1])), int(self.wave_radius), 2)
                    
                # Draw Active Trajectory
                if self.all_hit:
                    # Calculate trajectory line based strictly on polar angle
                    rad = math.radians(self.bearing)
                    dir_x = math.cos(rad)
                    dir_y = -math.sin(rad) # Pygame Y grows downwards
                    end_x = CENTER_X + dir_x * 400
                    end_y = CENTER_Y + dir_y * 400
                    pygame.draw.line(self.screen, COLOR_RED, (CENTER_X, CENTER_Y), (end_x, end_y), 3)

        # --- HUD ---
        hud_x = GRID_SIZE + 20
        title = self.font_large.render("LOCUS TACTICAL HUD", True, COLOR_CYAN)
        self.screen.blit(title, (hud_x, 20))
        
        # Mode Toggle Button
        btn_rect = pygame.Rect(hud_x, 60, 250, 40)
        pygame.draw.rect(self.screen, COLOR_GRAY, btn_rect)
        pygame.draw.rect(self.screen, COLOR_WHITE, btn_rect, 2)
        btn_txt = self.font_medium.render(f"Mode: {self.mode}", True, COLOR_WHITE)
        self.screen.blit(btn_txt, (hud_x + 10, 70))
        
        # Microphones Status
        y_offset = 120
        for name in ['N', 'E', 'S', 'W']:
            m = self.mics[name]
            label = self.font_medium.render(f"Mic {name}:", True, COLOR_WHITE)
            self.screen.blit(label, (hud_x, y_offset))
            
            if not self.click_pos or self.friendly_fire:
                status = self.font_medium.render("IDLE", True, COLOR_GRAY)
            elif not m.locked:
                status = self.font_medium.render("WAITING...", True, COLOR_CYAN)
            else:
                status = self.font_medium.render(f"+{m.rel_time_us:.1f} µs", True, COLOR_NEON_GREEN)
                
            self.screen.blit(status, (hud_x + 80, y_offset))
            y_offset += 30
            
        y_offset += 10
        
        # Refractory Lockout / Friendly fire indicator
        if self.friendly_fire:
            lock_txt = self.font_medium.render("IGNORED: FRIENDLY FIRE ZONE", True, COLOR_RED)
            self.screen.blit(lock_txt, (hud_x, y_offset))
        elif self.first_hit_time_us is not None:
            time_since_first_hit = self.sim_time_us - self.first_hit_time_us
            if 0 <= time_since_first_hit <= 50000.0:
                lock_txt = self.font_medium.render("50ms HARDWARE LOCKOUT", True, COLOR_LOCKOUT)
                self.screen.blit(lock_txt, (hud_x, y_offset))
        
        y_offset += 30
        
        # TDOA Results
        if self.all_hit and not self.friendly_fire:
            res_title = self.font_large.render("LATEST RESULT", True, COLOR_CYAN)
            self.screen.blit(res_title, (hud_x, y_offset))
            y_offset += 30
            
            dx_txt = self.font_medium.render(f"ΔX: {self.dt_x:.1f}  ΔY: {self.dt_y:.1f}", True, COLOR_WHITE)
            self.screen.blit(dx_txt, (hud_x, y_offset))
            y_offset += 30
            
            bear_txt = self.font_large.render(f"BEARING: {self.bearing:.1f}°", True, COLOR_NEON_GREEN)
            self.screen.blit(bear_txt, (hud_x, y_offset))
            
        y_offset += 40
        
        # Threat History Log
        hist_title = self.font_large.render("THREAT HISTORY", True, COLOR_CYAN)
        self.screen.blit(hist_title, (hud_x, y_offset))
        y_offset += 30
        
        if not self.history:
            txt = self.font_medium.render("No contacts.", True, COLOR_GRAY)
            self.screen.blit(txt, (hud_x, y_offset))
        else:
            for entry in self.history:
                seconds_old = current_time - entry['time']
                color = self.get_fade_color(seconds_old)
                
                angle_str = f"{entry['angle']:.1f}°"
                time_str = self.format_time_ago(seconds_old)
                
                txt = self.font_medium.render(f"{angle_str:<8} | {time_str}", True, color)
                self.screen.blit(txt, (hud_x, y_offset))
                y_offset += 25
        
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            dt = clock.tick(60) / 1000.0 # seconds
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_click(event.pos)
                        
            self.update(dt)
            self.draw()
            
        pygame.quit()

if __name__ == '__main__':
    sim = Simulation()
    sim.run()