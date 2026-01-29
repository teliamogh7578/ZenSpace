# -*- coding: utf-8 -*-
"""
Intervention Module - Visual and Audio Interventions
Handles all overlays, breathing exercises, and audio feedback
"""

import cv2
import time
import tkinter as tk
from tkinter import Canvas
import threading
import pygame
import os
import sys
import platform


class BrownNoisePlayer:
    """Brown noise player for quiet mode"""
    def __init__(self):
        self.playing = False
        self.thread = None
        self.sound = None
        pygame.mixer.init()
        
    def start(self):
        """Start brown noise from assets"""
        if not self.playing:
            print("[AUDIO] Starting brown noise...")
            try:
                brown_noise_path = os.path.join(os.path.dirname(__file__), "assets", "brown_noise.mp3")
                if os.path.exists(brown_noise_path):
                    self.sound = pygame.mixer.Sound(brown_noise_path)
                    self.sound.play(-1)  # -1 means loop indefinitely
                    self.playing = True
                else:
                    print(f"[AUDIO] Brown noise file not found at {brown_noise_path}")
            except Exception as e:
                print(f"[AUDIO] Could not start brown noise: {e}")
    
    def stop(self):
        """Stop brown noise"""
        if self.playing:
            print("[AUDIO] Stopping brown noise...")
            self.playing = False
            if self.sound:
                self.sound.stop()
                self.sound = None


class WhiteNoiseBeeper:
    """Beeping white noise for distraction alerts"""
    def __init__(self):
        self.playing = False
        self.thread = None
        
    def start(self):
        """Start beeping white noise"""
        if not self.playing:
            print("[AUDIO] Starting distraction alert beeping...")
            self.playing = True
            self.thread = threading.Thread(target=self._play_beeps, daemon=True)
            self.thread.start()
    
    def _play_beeps(self):
        """Play beeping pattern on Windows"""
        if platform.system() == "Windows":
            import winsound
            while self.playing:
                try:
                    # Beep pattern: medium frequency tone
                    winsound.Beep(300, 80)
                    time.sleep(0.1)
                except:
                    break
    
    def stop(self):
        """Stop beeping"""
        if self.playing:
            print("[AUDIO] Stopping distraction alert...")
            self.playing = False


class ZenMeditationPlayer:
    """Zen meditation audio player for breathing and zen modes"""
    def __init__(self):
        self.playing = False
        self.sound = None
        pygame.mixer.init()
        
    def start(self):
        """Start zen meditation audio"""
        if not self.playing:
            print("[AUDIO] Starting zen meditation...")
            try:
                meditation_path = os.path.join(os.path.dirname(__file__), "assets", "zen-meditation-180194.mp3")
                if os.path.exists(meditation_path):
                    self.sound = pygame.mixer.Sound(meditation_path)
                    self.sound.play(-1)  # -1 means loop indefinitely
                    self.playing = True
                else:
                    print(f"[AUDIO] Zen meditation file not found at {meditation_path}")
            except Exception as e:
                print(f"[AUDIO] Could not start zen meditation: {e}")
    
    def stop(self):
        """Stop zen meditation"""
        if self.playing:
            print("[AUDIO] Stopping zen meditation...")
            self.playing = False
            if self.sound:
                self.sound.stop()
                self.sound = None


class EnergyBreakOverlay:
    """High-energy overlay for fatigue/yawn detection"""
    def __init__(self):
        self.root = None
        self.canvas = None
        self.active = False
        self.running = False
        self.sound = None
        self.exercise_index = 0
        self.exercise_start_time = None
        self.exit_callback = None
        pygame.mixer.init()
        
    def start(self):
        if not self.running:
            self.running = True
            thread = threading.Thread(target=self._run_overlay, daemon=True)
            thread.start()
    
    def set_exit_callback(self, callback):
        """Set callback function for when overlay is exited"""
        self.exit_callback = callback
    
    def _run_overlay(self):
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.9)
        self.root.attributes('-topmost', True)
        
        if sys.platform == 'win32':
            self.root.wm_attributes('-transparentcolor', 'black')
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        self.canvas = Canvas(
            self.root, 
            width=screen_width, 
            height=screen_height,
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack()
        
        # ESC key to deactivate
        self.root.bind('<Escape>', self._on_escape)
        self.root.focus_set()
        self._animate()
        self.root.mainloop()
    
    def _on_escape(self, event):
        """Handle ESC key press"""
        print("[ESC] Escape key pressed - exiting energy break")
        self.deactivate()
    
    def _animate(self):
        if not self.active or not self.canvas:
            if self.root:
                self.root.after(100, self._animate)
            return
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        self.canvas.delete("all")
        
        # Bright orange/yellow background
        self.canvas.create_rectangle(
            0, 0, screen_width, screen_height,
            fill='#ff9500', outline=""
        )
        
        # Main title
        self.canvas.create_text(
            center_x, center_y - 200,
            text="⚡ FATIGUE DETECTED! ⚡",
            font=("Arial", 72, "bold"),
            fill="white"
        )
        
        self.canvas.create_text(
            center_x, center_y - 100,
            text="LET'S ENERGIZE!",
            font=("Arial", 56, "bold"),
            fill="white"
        )
        
        # Exercise prompts - cycle through them
        exercises = [
            "🏃 Do 5 Jumping Jacks NOW!",
            "💪 Stretch your arms upward!",
            "🚶 Walk around for 30 seconds!",
            "🤸 Do 3 quick squats!",
            "😤 Take 3 deep breaths!"
        ]
        
        current_exercise = exercises[self.exercise_index % len(exercises)]
        
        self.canvas.create_text(
            center_x, center_y + 50,
            text=current_exercise,
            font=("Arial", 48, "bold"),
            fill="#ffffff"
        )
        
        # Countdown or message
        self.canvas.create_text(
            center_x, center_y + 150,
            text="You'll return to work after this break",
            font=("Arial", 28),
            fill="white"
        )
        
        # Exit instructions - UPDATED
        self.canvas.create_text(
            center_x, screen_height - 100,
            text="Press ESC or show 👌 OK sign to exit",
            font=("Arial", 24, "bold"),
            fill="white"
        )
        
        self.root.after(33, self._animate)
    
    def activate(self):
        """Activate energy break"""
        self.active = True
        self.exercise_index = 0
        self.exercise_start_time = time.time()
        print("[ENERGY] Activating energy break - Fatigue detected!")
        
        # Play upbeat energy audio
        self._play_energy_audio()
    
    def _play_energy_audio(self):
        """Play upbeat energy audio"""
        try:
            energy_path = os.path.join(os.path.dirname(__file__), "assets", "energy.mp3")
            if os.path.exists(energy_path):
                self.sound = pygame.mixer.Sound(energy_path)
                self.sound.play()
                print("[AUDIO] Playing energy audio...")
            else:
                print(f"[AUDIO] Energy audio file not found at {energy_path}")
        except Exception as e:
            print(f"[AUDIO] Could not play energy audio: {e}")
    
    def deactivate(self):
        """Deactivate energy break - FIXED: Now properly exits"""
        self.active = False
        if self.sound:
            self.sound.stop()
        if self.root:
            try:
                self.root.quit()
            except:
                pass
        print("[ENERGY] Energy break ended")
        
        # Call exit callback if set
        if self.exit_callback:
            self.exit_callback()


class BreathingOverlay:
    """Full-screen breathing exercise overlay"""
    def __init__(self):
        self.root = None
        self.canvas = None
        self.active = False
        self.phase = "inhale"
        self.phase_start = time.time()
        self.running = False
        self.mode = "box"
        
    def start(self):
        if not self.running:
            self.running = True
            thread = threading.Thread(target=self._run_overlay, daemon=True)
            thread.start()
    
    def _run_overlay(self):
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.85)
        self.root.attributes('-topmost', True)
        
        if sys.platform == 'win32':
            self.root.wm_attributes('-transparentcolor', 'black')
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        self.canvas = Canvas(
            self.root, 
            width=screen_width, 
            height=screen_height,
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack()
        
        # ESC key to deactivate
        self.root.bind('<Escape>', lambda e: self.deactivate())
        self._animate()
        self.root.mainloop()
    
    def _animate(self):
        if not self.active or not self.canvas:
            if self.root:
                self.root.after(100, self._animate)
            return
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        self.canvas.delete("all")
        
        current_time = time.time()
        elapsed = current_time - self.phase_start
        duration = 4.0
        
        if self.phase == "inhale":
            if elapsed >= duration:
                self.phase = "hold1"
                self.phase_start = current_time
                progress = 1.0
            else:
                progress = elapsed / duration
            color = "#4a90e2"
            instruction = "BREATHE IN"
            
        elif self.phase == "hold1":
            if elapsed >= duration:
                self.phase = "exhale"
                self.phase_start = current_time
                progress = 1.0
            else:
                progress = 1.0
            color = "#50c878"
            instruction = "HOLD"
            
        elif self.phase == "exhale":
            if elapsed >= duration:
                self.phase = "hold2"
                self.phase_start = current_time
                progress = 0.0
            else:
                progress = 1.0 - (elapsed / duration)
            color = "#9b59b6"
            instruction = "BREATHE OUT"
            
        else:  # hold2
            if elapsed >= duration:
                self.phase = "inhale"
                self.phase_start = current_time
                progress = 0.0
            else:
                progress = 0.0
            color = "#50c878"
            instruction = "HOLD"
        
        min_radius = 80
        max_radius = 250
        radius = min_radius + (max_radius - min_radius) * progress
        
        self.canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill=color, outline="white", width=5
        )
        
        self.canvas.create_text(
            center_x, center_y - 350,
            text=instruction,
            font=("Arial", 48, "bold"),
            fill="white"
        )
        
        bar_width = 600
        bar_height = 30
        bar_x = center_x - bar_width // 2
        bar_y = center_y + 300
        
        self.canvas.create_rectangle(
            bar_x, bar_y,
            bar_x + bar_width, bar_y + bar_height,
            fill="#c8c8c8", outline="white", width=2
        )
        
        phase_progress = elapsed / duration
        self.canvas.create_rectangle(
            bar_x, bar_y,
            bar_x + int(bar_width * phase_progress), bar_y + bar_height,
            fill=color, outline=""
        )
        
        remaining = duration - elapsed
        self.canvas.create_text(
            center_x, bar_y + bar_height + 40,
            text=f"{remaining:.1f}s",
            font=("Arial", 24),
            fill="white"
        )
        
        # Exit instructions
        self.canvas.create_text(
            center_x, screen_height - 80,
            text="Press ESC or show 👌 OK sign to exit",
            font=("Arial", 20, "bold"),
            fill="white"
        )
        
        self.root.after(33, self._animate)
    
    def activate(self, mode="box"):
        self.active = True
        self.mode = mode
        self.phase = "inhale"
        self.phase_start = time.time()
        print(f"[BREATHING] {mode.capitalize()} breathing started")
    
    def deactivate(self):
        self.active = False
        if self.canvas:
            self.canvas.delete("all")
        print("[BREATHING] Breathing exercise stopped")


class ScreenWarmer:
    """Full-screen warm color overlay"""
    def __init__(self):
        self.root = None
        self.canvas = None
        self.warmth = 0
        self.running = False
        
    def start(self):
        if not self.running:
            self.running = True
            thread = threading.Thread(target=self._run_overlay, daemon=True)
            thread.start()
    
    def _run_overlay(self):
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        
        if sys.platform == 'win32':
            self.root.wm_attributes('-transparentcolor', 'black')
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        self.canvas = Canvas(
            self.root, 
            width=screen_width, 
            height=screen_height,
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack()
        
        self._update()
        self.root.mainloop()
    
    def _update(self):
        if not self.canvas:
            return
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        self.canvas.delete("all")
        
        if self.warmth > 0:
            alpha_value = (self.warmth / 100.0) * 0.4
            self.root.attributes('-alpha', alpha_value)
            
            self.canvas.create_rectangle(
                0, 0, screen_width, screen_height,
                fill='#ff8800', outline=""
            )
        else:
            self.root.attributes('-alpha', 0.0)
        
        self.root.after(100, self._update)
    
    def set_warmth(self, value):
        self.warmth = max(0, min(100, value))


class ZenModeDim:
    """Full-screen dim overlay for Zen Mode"""
    def __init__(self):
        self.root = None
        self.canvas = None
        self.active = False
        self.running = False
        self.message = "ZEN MODE"
        self.mode_type = "default"  # default, quiet, focus
        
    def start(self):
        if not self.running:
            self.running = True
            thread = threading.Thread(target=self._run_overlay, daemon=True)
            thread.start()
    
    def _run_overlay(self):
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        
        if sys.platform == 'win32':
            self.root.wm_attributes('-transparentcolor', 'black')
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        self.canvas = Canvas(
            self.root, 
            width=screen_width, 
            height=screen_height,
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack()
        
        # ESC key to deactivate
        self.root.bind('<Escape>', lambda e: self.deactivate())
        self._update()
        self.root.mainloop()
    
    def _update(self):
        if not self.canvas:
            return
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        self.canvas.delete("all")
        
        if self.active:
            # Different modes have different visuals
            if self.mode_type == "focus":
                # FOCUS MODE: Heavy blur effect + calming instructions
                self.root.attributes('-alpha', 0.85)
                
                self.canvas.create_rectangle(
                    0, 0, screen_width, screen_height,
                    fill='#1a1a2e', outline=""
                )
                
                # Main title
                self.canvas.create_text(
                    screen_width // 2, 150,
                    text="5 MINUTE FOCUS PAUSE",
                    font=("Arial", 56, "bold"),
                    fill="#4a90e2"
                )
                
                # Calming instructions
                instructions = [
                    "Pause. Nothing else matters right now.",
                    "Place your feet flat on the ground.",
                    "Slowly breathe in through your nose.",
                    "Let the breath out longer than you breathed in.",
                    "Drop your shoulders away from your ears.",
                    "Soften your jaw and your hands.",
                    "Stay here for a few moments."
                ]

                
                y_pos = 300
                for i, instruction in enumerate(instructions):
                    self.canvas.create_text(
                        screen_width // 2, y_pos + (i * 80),
                        text=f"• {instruction}",
                        font=("Arial", 32),
                        fill="white"
                    )
                
                # Exit instructions
                self.canvas.create_text(
                    screen_width // 2, screen_height - 100,
                    text="Press ESC or show 👌 OK sign to exit",
                    font=("Arial", 24, "bold"),
                    fill="#50c878"
                )
                
            elif self.mode_type == "quiet":
                # QUIET MODE: Darker with noise indicator
                self.root.attributes('-alpha', 0.7)
                
                self.canvas.create_rectangle(
                    0, 0, screen_width, screen_height,
                    fill='#0a0a0a', outline=""
                )
                
                self.canvas.create_text(
                    screen_width // 2, screen_height // 2 - 100,
                    text="🙉 QUIET MODE",
                    font=("Arial", 72, "bold"),
                    fill="white"
                )
                
                self.canvas.create_text(
                    screen_width // 2, screen_height // 2 + 50,
                    text="Brown noise playing...",
                    font=("Arial", 36),
                    fill="#95a5a6"
                )
                
                self.canvas.create_text(
                    screen_width // 2, screen_height // 2 + 150,
                    text="Notifications muted",
                    font=("Arial", 28),
                    fill="#95a5a6"
                )
                
                # Exit instructions
                self.canvas.create_text(
                    screen_width // 2, screen_height - 100,
                    text="Press ESC or show 👌 OK sign to exit",
                    font=("Arial", 24, "bold"),
                    fill="#50c878"
                )
                
            else:
                # DEFAULT ZEN MODE
                self.root.attributes('-alpha', 0.5)
                
                self.canvas.create_rectangle(
                    0, 0, screen_width, screen_height,
                    fill='#000000', outline=""
                )
                
                self.canvas.create_text(
                    screen_width // 2, screen_height // 2,
                    text=self.message,
                    font=("Arial", 72, "bold"),
                    fill="white"
                )
                
                # Exit instructions
                self.canvas.create_text(
                    screen_width // 2, screen_height - 100,
                    text="Press ESC or show 👌 OK sign to exit",
                    font=("Arial", 24, "bold"),
                    fill="#95a5a6"
                )
        else:
            self.root.attributes('-alpha', 0.0)
        
        self.root.after(100, self._update)
    
    def activate(self, message="ZEN MODE", mode_type="default"):
        self.active = True
        self.message = message
        self.mode_type = mode_type
        print(f"[ZEN] {message} ({mode_type})")
    
    def deactivate(self):
        self.active = False
        self.mode_type = "default"
        print("[ZEN] Zen Mode deactivated")


class PostureWarningBeeper:
    """Beeping alert for bad posture warnings"""
    def __init__(self):
        self.playing = False
        self.thread = None
        
    def start(self):
        """Start posture warning beeps"""
        if not self.playing:
            print("[AUDIO] Starting posture warning beeps...")
            self.playing = True
            self.thread = threading.Thread(target=self._play_beeps, daemon=True)
            self.thread.start()
    
    def _play_beeps(self):
        """Play gentle beeping pattern for posture"""
        if platform.system() == "Windows":
            import winsound
            while self.playing:
                try:
                    # Gentle reminder beep: lower frequency, softer
                    winsound.Beep(400, 100)  # 400Hz, 100ms
                    time.sleep(2.0)  # Every 2 seconds
                except:
                    break
    
    def stop(self):
        """Stop beeping"""
        if self.playing:
            print("[AUDIO] Stopping posture warning beeps...")
            self.playing = False


class PostureWarningOverlay:
    """Full-screen posture warning overlay"""
    def __init__(self):
        self.root = None
        self.canvas = None
        self.active = False
        self.running = False
        self.posture_issues = {}
        
    def start(self):
        """Start the overlay in a separate thread"""
        if not self.running:
            self.running = True
            thread = threading.Thread(target=self._run_overlay, daemon=True)
            thread.start()
    
    def _run_overlay(self):
        """Run the tkinter overlay"""
        self.root = tk.Tk()
        
        # Make fullscreen and semi-transparent
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.0)  # Start invisible
        self.root.attributes('-topmost', True)
        
        if sys.platform == 'win32':
            self.root.wm_attributes('-transparentcolor', 'black')
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Create canvas
        self.canvas = Canvas(
            self.root, 
            width=screen_width, 
            height=screen_height,
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack()
        
        # Start update loop
        self._update()
        
        self.root.mainloop()
    
    def _update(self):
        """Update the overlay"""
        if not self.canvas:
            return
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        self.canvas.delete("all")
        
        if self.active:
            # Make visible with warning overlay
            self.root.attributes('-alpha', 0.75)
            
            # Draw semi-transparent orange/yellow background
            self.canvas.create_rectangle(
                0, 0, screen_width, screen_height,
                fill='#ff6b35', outline=""
            )
            
            # Main warning message
            center_x = screen_width // 2
            center_y = screen_height // 2
            
            self.canvas.create_text(
                center_x, center_y - 150,
                text="⚠️ POSTURE ALERT ⚠️",
                font=("Arial", 72, "bold"),
                fill="white"
            )
            
            self.canvas.create_text(
                center_x, center_y - 50,
                text="Fix Your Posture Now!",
                font=("Arial", 48, "bold"),
                fill="white"
            )
            
            # List specific issues
            if self.posture_issues:
                y_offset = center_y + 50
                issue_text = []
                
                if self.posture_issues.get('forward_head'):
                    issue_text.append("• Pull your head back (chin tuck)")
                if self.posture_issues.get('slouched'):
                    issue_text.append("• Sit up straight, open your chest")
                if self.posture_issues.get('rounded_shoulders'):
                    issue_text.append("• Roll shoulders back and down")
                if self.posture_issues.get('uneven_shoulders'):
                    issue_text.append("• Level your shoulders")
                
                for i, text in enumerate(issue_text):
                    self.canvas.create_text(
                        center_x, y_offset + (i * 50),
                        text=text,
                        font=("Arial", 32),
                        fill="white"
                    )
            
            # Instructions
            self.canvas.create_text(
                center_x, screen_height - 100,
                text="Fix your posture to dismiss this warning",
                font=("Arial", 28, "bold"),
                fill="white"
            )
            
        else:
            # Make invisible when not active
            self.root.attributes('-alpha', 0.0)
        
        # Schedule next update
        self.root.after(100, self._update)
    
    def activate(self, posture_issues=None):
        """Show posture warning overlay"""
        self.active = True
        if posture_issues:
            self.posture_issues = posture_issues
        print("[POSTURE OVERLAY] Showing fullscreen warning")
    
    def deactivate(self):
        """Hide posture warning overlay"""
        self.active = False
        self.posture_issues = {}
        print("[POSTURE OVERLAY] Warning dismissed")
