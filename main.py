# -*- coding: utf-8 -*-
"""
ZenSpace - Enhanced Full Screen Intervention System
Main connector module between gesture detection and interventions
"""

import cv2
import numpy as np
import time
import sys
import os
from collections import deque

# Import detector and intervention modules
from detector import GestureDetector
from intervention import (
    BrownNoisePlayer,
    WhiteNoiseBeeper,
    ZenMeditationPlayer,
    EnergyBreakOverlay,
    BreathingOverlay,
    ScreenWarmer,
    ZenModeDim,
    PostureWarningBeeper,
    PostureWarningOverlay
)

# Force UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


class ZenSpaceEnhanced:
    """Main ZenSpace controller - connects detection with interventions"""
    
    def __init__(self):
        # Initialize detector
        self.detector = GestureDetector()
        
        # Gesture state tracking
        self.gesture_timers = {
            'open_palm': None,
            'both_hands_raised': None,
            'hands_covering_ears': None,
            'clenched_fist': None,
            'fingers_near_mouth': None,
            'hand_near_face_scratch': None,
            'repetitive_face_touch': None,
            'finger_tapping': None,
            'palms_together': None,
            'ok_sign': None,
            'peace_sign': None,
            'palm_down_slow': None,
            'slouched': None,
            'low_movement': None,
            'head_on_hand': None
        }

        
        # State tracking
        self.zen_mode_active = False
        self.breathing_active = False
        self.warmth_active = False
        self.quiet_mode_active = False
        self.focus_mode_active = False
        
        # Yawn and fatigue tracking
        self.energy_break_active = False
        self.yawn_counter = 0
        self.yawn_window = deque(maxlen=750)  # 750 frames at ~30fps = ~25 seconds observation window
        self.yawn_threshold = 5  # 5 yawns in window triggers energy break
        self.last_yawn_detected = False
        
        # Phone distraction tracking
        self.looking_down = False
        self.looking_down_start = None
        self.distraction_warning_active = False
        
        
        # Bad posture tracking
        self.bad_posture_active = False
        self.bad_posture_start = None
        self.posture_issues = {}
        self.posture_warning_threshold = 30  # seconds
        
        # Nail biting tracking
        self.nail_biting_count = 0  # Count of nail biting episodes
        self.nail_biting_active = False
        self.last_nail_biting_detected = False
        self.nail_biting_threshold = 6  # Anxiety threshold
        self.nail_biting_warmth_levels = [10, 20, 30, 40, 50]  # Progressive warmth for episodes 1-5
        
        # Initialize intervention components
        self.brown_noise = BrownNoisePlayer()
        self.distraction_beeper = WhiteNoiseBeeper()
        self.zen_meditation = ZenMeditationPlayer()
        self.energy_break = EnergyBreakOverlay()
        self.energy_break.set_exit_callback(self._on_energy_break_exit)
        
        # Movement tracking
        self.hand_positions_history = deque(maxlen=90)
        self.face_touch_count = 0
        self.face_touch_window = deque(maxlen=300)
        self.last_hand_movement_time = time.time()
        
        self.current_min_distance = 999.0
        
        # Initialize video capture
        self.cap = cv2.VideoCapture(0)
        
        # Initialize overlays
        self.breathing_overlay = BreathingOverlay()
        self.screen_warmer = ScreenWarmer()
        self.zen_dim = ZenModeDim()
        self.posture_warning_overlay = PostureWarningOverlay()
        self.posture_beeper = PostureWarningBeeper()
        
        print("[INIT] Starting overlay systems...")
        self.breathing_overlay.start()
        time.sleep(0.5)
        self.screen_warmer.start()
        time.sleep(0.5)
        self.zen_dim.start()
        time.sleep(0.5)
        self.energy_break.start()
        time.sleep(0.5)
        self.posture_warning_overlay.start()
        time.sleep(1)
        print("[INIT] All systems ready!")
    
    # ==================== EXIT ALL MODES ====================
    
    def exit_all_modes(self):
        """Properly exit all active modes"""
        print("[EXIT] Exiting all active modes...")
        
        if self.zen_mode_active:
            self.zen_mode_active = False
            self.zen_dim.deactivate()
            self.zen_meditation.stop()
        
        if self.breathing_active:
            self.breathing_active = False
            self.breathing_overlay.deactivate()
            self.zen_meditation.stop()
        
        if self.quiet_mode_active:
            self.quiet_mode_active = False
            self.brown_noise.stop()
            self.zen_dim.deactivate()
        
        if self.focus_mode_active:
            self.focus_mode_active = False
            self.zen_dim.deactivate()
        
        if self.energy_break_active:
            self.energy_break_active = False
            self.energy_break.deactivate()
        
        if self.distraction_warning_active:
            self.distraction_warning_active = False
            self.looking_down_start = None
        
        if self.bad_posture_active:
            self.bad_posture_active = False
            self.bad_posture_start = None
            self.posture_warning_overlay.deactivate()
            self.posture_beeper.stop()
        
        # Reset nail biting tracking
        if self.nail_biting_active:
            print(f"[RESET] Nail biting counter reset (was at {self.nail_biting_count} episodes)")
            self.nail_biting_active = False
            self.nail_biting_count = 0
            self.last_nail_biting_detected = False
        
        self.screen_warmer.set_warmth(0)
        print("[EXIT] All modes deactivated ✓")
    
    def _on_energy_break_exit(self):
        """Callback when energy break is exited"""
        print("[ENERGY] Energy break exit callback triggered")
        self.energy_break_active = False
        self.yawn_counter = 0
        self.yawn_window.clear()
    
    # ==================== GESTURE PROCESSING ====================
    
    def process_gestures(self, hand_results, pose_results, face_results, frame_shape):
        """Process all gesture recognitions and trigger interventions"""
        current_time = time.time()
        hand_landmarks = hand_results.multi_hand_landmarks
        pose_landmarks = pose_results.pose_landmarks
        face_landmarks = face_results.multi_face_landmarks
        
        if hand_landmarks:
            self.last_hand_movement_time = current_time
        
        # ===== YAWN & FATIGUE DETECTION =====
        # 🥱 Check for yawns using face mesh
        yawn_detected = False
        if face_landmarks:
            for face_landmark in face_landmarks:
                if self.detector.check_yawn(face_landmark):
                    yawn_detected = True
                    break
        
        # Track yawns in a sliding window
        self.yawn_window.append(1 if yawn_detected else 0)
        
        # Detect transitions from no-yawn to yawn (count only once per yawn)
        if yawn_detected and not self.last_yawn_detected:
            self.yawn_counter += 1
            print(f"[YAWN] Yawn detected! Count: {self.yawn_counter} in window")
        
        self.last_yawn_detected = yawn_detected
        
        # Check if threshold met for energy break
        # Use yawn_counter (distinct yawns) instead of window sum (frame count)
        if self.yawn_counter >= self.yawn_threshold and not self.energy_break_active:
            print(f"[!!!] FATIGUE ALERT - {self.yawn_counter} yawns detected!")
            self.energy_break_active = True
            self.energy_break.activate()
            self.yawn_counter = 0  # Reset counter
        
        # Don't process other gestures if energy break is active
        if self.energy_break_active:
            # FIXED: Allow OK sign to exit energy break
            if hand_landmarks and self.detector.check_ok_sign(hand_landmarks):
                if self.gesture_timers['ok_sign'] is None:
                    self.gesture_timers['ok_sign'] = current_time
                    print("[OK SIGN] Detected - hold for 1.5s to exit energy break")
                elif current_time - self.gesture_timers['ok_sign'] > 1.5:
                    print("[!!!] OK SIGN - Exiting energy break")
                    self.energy_break_active = False
                    self.energy_break.deactivate()
                    self.gesture_timers['ok_sign'] = None
                    self.yawn_window.clear()  # Clear yawn window on exit
            else:
                self.gesture_timers['ok_sign'] = None
            return
        
        # ===== PRIORITY: OK SIGN TO EXIT =====
        # Check OK sign first to allow immediate exit
        if self.detector.check_ok_sign(hand_landmarks):
            if self.gesture_timers['ok_sign'] is None:
                self.gesture_timers['ok_sign'] = current_time
            elif current_time - self.gesture_timers['ok_sign'] > 1.5:
                self.exit_all_modes()
                self.gesture_timers['ok_sign'] = None
        else:
            self.gesture_timers['ok_sign'] = None
        
        # ===== NAIL BITING DETECTION (Priority - check first!) =====
        # 🤏 Fingers Near Mouth - Progressive Nail Biting Detection
        # Episodes 1-5: Habit-induced (warmth only, progressive)
        # Episode 6+: Anxiety-induced (breathing exercise)
        # CHECK THIS BEFORE OTHER GESTURES TO AVOID FALSE POSITIVES
        nail_biting_detected = self.detector.check_fingers_near_mouth(hand_landmarks, pose_landmarks, frame_shape)
        
        if nail_biting_detected:
            if self.gesture_timers['fingers_near_mouth'] is None:
                self.gesture_timers['fingers_near_mouth'] = current_time
            elif current_time - self.gesture_timers['fingers_near_mouth'] > 2:
                # Count this as a nail biting episode (only once per session)
                if not self.last_nail_biting_detected:
                    self.nail_biting_count += 1
                    self.last_nail_biting_detected = True
                    
                    if self.nail_biting_count < self.nail_biting_threshold:
                        # Episodes 1-5: Habit-induced - Progressive warmth only
                        # EXPLICITLY ensure breathing is NOT activated
                        warmth_level = self.nail_biting_warmth_levels[min(self.nail_biting_count - 1, 4)]
                        self.screen_warmer.set_warmth(warmth_level)
                        print(f"[HABIT] Nail biting detected (Episode {self.nail_biting_count}/{self.nail_biting_threshold - 1})")
                        print(f"   Screen warmth: {warmth_level}% - Building awareness")
                        print(f"   NO breathing exercise (habit phase)")
                        
                    else:
                        # Episode 6+: Anxiety-induced - Trigger breathing exercise
                        if self.nail_biting_count == self.nail_biting_threshold:
                            print(f"[!!!] ANXIETY ALERT - {self.nail_biting_count} nail biting episodes!")
                            print("   This suggests anxiety, not just habit")
                            print("   Activating breathing exercise...")
                        else:
                            print(f"[ANXIETY] Nail biting episode {self.nail_biting_count} - Breathing active")
                        
                        # Activate breathing overlay ONLY in anxiety phase
                        if not self.breathing_active:
                            self.breathing_active = True
                            self.breathing_overlay.activate()
                            self.zen_meditation.start()
                        
                        # Also increase warmth
                        self.screen_warmer.set_warmth(70)
                        self.nail_biting_active = True
        else:
            # Hand moved away from mouth
            if self.last_nail_biting_detected:
                self.last_nail_biting_detected = False
                print(f"[OK] Hands away from mouth (Total episodes: {self.nail_biting_count})")
                
            # Reset timer
            self.gesture_timers['fingers_near_mouth'] = None
            
            # Gradually reduce warmth if not in anxiety mode
            if not self.nail_biting_active:
                if self.screen_warmer.warmth > 0 and self.screen_warmer.warmth <= 50:
                    self.screen_warmer.set_warmth(0)
        
        # Don't process other gestures if already in a mode (except exit and nail biting)
        # Also skip if nail biting is detected to avoid false positives from other gesture detectors
        if self.zen_mode_active or self.breathing_active or self.quiet_mode_active or self.focus_mode_active:
            return
        
        # If fingers are near mouth, skip other gesture detection to prevent false positives
        if nail_biting_detected:
            return
        
        # ===== EMERGENCY GESTURES =====
        
        # ✋ Open Palm - Zen Mode
        if self.detector.check_open_palm(hand_landmarks):
            if self.gesture_timers['open_palm'] is None:
                self.gesture_timers['open_palm'] = current_time
            elif current_time - self.gesture_timers['open_palm'] > 2:
                print("[!!!] OPEN PALM DETECTED - Activating Zen Mode")
                self.zen_mode_active = True
                self.zen_dim.activate("ZEN MODE\nTake a moment to breathe", "default")
                self.zen_meditation.start()
        else:
            self.gesture_timers['open_palm'] = None
        
        # 🙌 Both Hands Raised - Pause + Breathing
        if self.detector.check_both_hands_raised(hand_landmarks, pose_landmarks):
            if self.gesture_timers['both_hands_raised'] is None:
                self.gesture_timers['both_hands_raised'] = current_time
            elif current_time - self.gesture_timers['both_hands_raised'] > 2:
                print("[!!!] BOTH HANDS RAISED - Starting guided breathing")
                self.breathing_active = True
                self.breathing_overlay.activate("box")
                self.zen_meditation.start()
        else:
            self.gesture_timers['both_hands_raised'] = None
        
        # 🙉 Hands Covering Ears - QUIET MODE WITH BROWN NOISE
        if self.detector.check_hands_covering_ears(hand_landmarks, pose_landmarks):
            if self.gesture_timers['hands_covering_ears'] is None:
                self.gesture_timers['hands_covering_ears'] = current_time
            elif current_time - self.gesture_timers['hands_covering_ears'] > 1:
                if not self.quiet_mode_active:
                    print("[!!!] HANDS ON EARS - QUIET MODE + BROWN NOISE")
                    self.quiet_mode_active = True
                    self.brown_noise.start()
                    self.zen_dim.activate("QUIET MODE", "quiet")
        else:
            self.gesture_timers['hands_covering_ears'] = None
        
        # ✊ Clenched Fist - Box Breathing + Warmth
        if self.detector.check_clenched_fist(hand_landmarks):
            if self.gesture_timers['clenched_fist'] is None:
                self.gesture_timers['clenched_fist'] = current_time
            elif current_time - self.gesture_timers['clenched_fist'] > 3:
                print("[!!!] CLENCHED FIST - Box breathing + warmth")
                self.breathing_active = True
                self.breathing_overlay.activate("box")
                self.screen_warmer.set_warmth(60)
                self.zen_meditation.start()
        else:
            self.gesture_timers['clenched_fist'] = None
        
        # ✌️ Peace Sign - FOCUS MODE WITH BLUR
        if self.detector.check_peace_sign(hand_landmarks):
            if self.gesture_timers['peace_sign'] is None:
                self.gesture_timers['peace_sign'] = current_time
            elif current_time - self.gesture_timers['peace_sign'] > 2:
                if not self.focus_mode_active:
                    print("[!!!] PEACE SIGN - 5 MINUTE FOCUS MODE")
                    self.focus_mode_active = True
                    self.zen_dim.activate("5 MINUTE FOCUS PAUSE", "focus")
        else:
            self.gesture_timers['peace_sign'] = None
        
        # 🤲 Palms Together - Mindfulness
        if self.detector.check_palms_together(hand_landmarks):
            if self.gesture_timers['palms_together'] is None:
                self.gesture_timers['palms_together'] = current_time
            elif current_time - self.gesture_timers['palms_together'] > 2:
                print("[CALM] Namaste - Starting mindfulness")
                self.zen_mode_active = True
                self.zen_dim.activate("MINDFULNESS\n5 minutes of calm", "default")
                self.zen_meditation.start()
        else:
            self.gesture_timers['palms_together'] = None
        
        # ===== PHONE DISTRACTION DETECTION =====
        # 📱 Looking Down at Phone - Distraction Warning
        looking_down = self.detector.check_looking_down_at_phone(pose_landmarks)
        
        if looking_down:
            if self.looking_down_start is None:
                self.looking_down_start = current_time
                print("[DISTRACTION] Looking down detected...")
            
            # After 3 seconds of looking down, activate warning
            elapsed = current_time - self.looking_down_start
            if elapsed > 3 and not self.distraction_warning_active:
                print("[!!!] PHONE DISTRACTION - You're looking at your phone!")
                self.distraction_warning_active = True
                # Subtle orange warmth to remind user
                self.screen_warmer.set_warmth(40)
                # Start beeping alert
                self.distraction_beeper.start()
        else:
            # Looking back up - clear warning
            if self.distraction_warning_active:
                print("[OK] Welcome back! Distraction cleared")
                self.distraction_warning_active = False
                self.screen_warmer.set_warmth(0)
                # Stop beeping
                self.distraction_beeper.stop()
            self.looking_down_start = None

        # ===== BAD POSTURE DETECTION =====
        # 🧍 Check for bad posture (tech neck, slouching, etc.)
        has_bad_posture, posture_issues = self.detector.check_bad_posture(pose_landmarks)
        self.posture_issues = posture_issues
        
        if has_bad_posture:
            if self.bad_posture_start is None:
                self.bad_posture_start = current_time
                print("[POSTURE] Bad posture detected - monitoring...")
                if posture_issues.get('forward_head'):
                    print("  - Forward head posture (tech neck)")
                if posture_issues.get('slouched'):
                    print("  - Slouched/hunched")
                if posture_issues.get('rounded_shoulders'):
                    print("  - Rounded shoulders")
                if posture_issues.get('uneven_shoulders'):
                    print("  - Uneven shoulders")
            
            # After threshold seconds of bad posture, activate warning
            elapsed = current_time - self.bad_posture_start
            if elapsed > self.posture_warning_threshold and not self.bad_posture_active:
                print(f"[!!!] BAD POSTURE ALERT - {elapsed:.0f}s of poor posture!")
                self.bad_posture_active = True
                # Activate fullscreen warning overlay
                self.posture_warning_overlay.activate(posture_issues)
                # Start beeping
                self.posture_beeper.start()
                # Add warmth to screen
                self.screen_warmer.set_warmth(50)
        else:
            # Good posture restored
            if self.bad_posture_active or self.bad_posture_start is not None:
                if self.bad_posture_active:
                    print("[OK] Great! Posture corrected!")
                    # Deactivate warning overlay
                    self.posture_warning_overlay.deactivate()
                    # Stop beeping
                    self.posture_beeper.stop()
                    # Remove warmth
                    self.screen_warmer.set_warmth(0)
                self.bad_posture_active = False
                self.bad_posture_start = None
    
    def run(self):
        """Main video processing loop"""
        print("=" * 70)
        print("  ZenSpace Enhanced: Comprehensive Gesture Recognition System")
        print("=" * 70)
        print("\n*** EMERGENCY GESTURES:")
        print("  ✋ Open Palm (2s) → Zen Mode")
        print("  🙌 Both Hands Raised (2s) → Pause + Guided Breathing")
        print("  🙉 Hands on Ears (2s) → Quiet Mode + BROWN NOISE")
        print("  ✊ Clenched Fist (3s) → Box Breathing + Warmth")
        print("\n*** FOCUS & CALM:")
        print("  🤲 Palms Together (2s) → Mindfulness")
        print("  ✌️ Peace Sign (2s) → 5 Min FOCUS MODE (blur + calming)")
        print("\n*** PASSIVE MONITORING:")
        print("  📱 Looking down (3s) → Phone distraction warning")
        print("  🤏 Nail biting detection:")
        print("       Episodes 1-5: Progressive warmth (habit awareness)")
        print("       Episode 6+: Breathing exercise (anxiety intervention)")
        print("  🥱 Yawns (5x in 25s window) → ENERGY BREAK (fatigue detection)")
        print("  🧍 Bad posture (30s) → POSTURE ALERT (lines turn RED, warmth)")
        print("       - Fix posture to turn lines GREEN/WHITE again!")
        print("\n*** EXIT ANY MODE:")
        print("  👌 OK Sign (1.5s) → EXIT ALL MODES")
        print("  ESC key → EXIT ALL MODES")
        print("\nPress 'q' in camera window to quit")
        print("Green dots on mouth = yawn detection debug landmarks\n")
        
        while self.cap.isOpened():
            success, frame = self.cap.read()
            if not success:
                break
            
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame through detector
            hand_results, pose_results, face_results = self.detector.process_frame(rgb_frame)
            
            # Process all gestures and trigger interventions
            self.process_gestures(hand_results, pose_results, face_results, frame.shape)
            
            # Draw landmarks
            if hand_results.multi_hand_landmarks:
                for hand_landmarks in hand_results.multi_hand_landmarks:
                    self.detector.mp_drawing.draw_landmarks(
                        frame, hand_landmarks, self.detector.mp_hands.HAND_CONNECTIONS
                    )
            
            if pose_results.pose_landmarks:
                # Draw pose landmarks with custom coloring for posture feedback
                posture_points = self.detector.get_posture_visualization_points(pose_results.pose_landmarks)
                
                if posture_points and (self.bad_posture_active or any(self.posture_issues.values())):
                    # BAD POSTURE - Draw in RED with thicker lines
                    h, w = frame.shape[:2]
                    
                    # Define connections for posture spine
                    connections = [
                        ('left_ear', 'left_shoulder'),
                        ('right_ear', 'right_shoulder'),
                        ('left_shoulder', 'right_shoulder'),
                        ('left_shoulder', 'left_hip'),
                        ('right_shoulder', 'right_hip'),
                        ('left_hip', 'right_hip'),
                    ]
                    
                    # Draw lines in RED
                    for start_name, end_name in connections:
                        start = posture_points[start_name]
                        end = posture_points[end_name]
                        start_x, start_y = int(start.x * w), int(start.y * h)
                        end_x, end_y = int(end.x * w), int(end.y * h)
                        cv2.line(frame, (start_x, start_y), (end_x, end_y), (0, 0, 255), 5)  # RED, thick
                    
                    # Draw points in RED
                    for point_name, point in posture_points.items():
                        x, y = int(point.x * w), int(point.y * h)
                        cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)  # RED circles
                else:
                    # GOOD POSTURE - Draw in GREEN
                    self.detector.mp_drawing.draw_landmarks(
                        frame, pose_results.pose_landmarks, self.detector.mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=self.detector.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                        connection_drawing_spec=self.detector.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
                    )
            
            # Draw mouth landmarks for yawn detection debugging (green)
            if face_results.multi_face_landmarks:
                for face_landmark in face_results.multi_face_landmarks:
                    mouth_points = self.detector.get_mouth_landmarks(face_landmark)
                    if mouth_points:
                        h, w = frame.shape[:2]
                        for point_name, point in mouth_points.items():
                            x = int(point.x * w)
                            y = int(point.y * h)
                            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)  # Green circles
            
            # Show status
            y_pos = 30
            statuses = [
                ("Zen", self.zen_mode_active),
                ("Breathing", self.breathing_active),
                ("Quiet", self.quiet_mode_active),
                ("Focus", self.focus_mode_active),
                ("Energy", self.energy_break_active)
            ]
            
            for label, active in statuses:
                color = (0, 0, 255) if active else (0, 255, 0)
                cv2.putText(frame, f"{label}: {'ACTIVE' if active else 'Ready'}", 
                           (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                y_pos += 30
            
            # Phone distraction warning (separate, prominent)
            if self.distraction_warning_active:
                cv2.putText(frame, "DISTRACTED - Look up!", 
                           (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 3)
                y_pos += 40
            
            # Posture warning (RED when bad, show issues)
            if self.bad_posture_active or any(self.posture_issues.values()):
                posture_color = (0, 0, 255) if self.bad_posture_active else (0, 165, 255)
                status_text = "BAD POSTURE!" if self.bad_posture_active else "Posture issue detected"
                cv2.putText(frame, status_text, 
                           (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.9, posture_color, 3)
                y_pos += 35
                
                # Show specific issues
                if self.posture_issues.get('forward_head'):
                    cv2.putText(frame, "- Forward head (tech neck)", 
                               (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    y_pos += 25
                if self.posture_issues.get('slouched'):
                    cv2.putText(frame, "- Slouched/hunched", 
                               (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    y_pos += 25
                if self.posture_issues.get('rounded_shoulders'):
                    cv2.putText(frame, "- Rounded shoulders", 
                               (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    y_pos += 25
                if self.posture_issues.get('uneven_shoulders'):
                    cv2.putText(frame, "- Uneven shoulders", 
                               (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    y_pos += 25
                
                # Posture correction hint
                if self.bad_posture_start:
                    elapsed = time.time() - self.bad_posture_start
                    cv2.putText(frame, f"Fix posture to turn green! ({elapsed:.0f}s)", 
                               (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    y_pos += 30
            
            # Yawn counter display
            if self.yawn_counter > 0:
                cv2.putText(frame, f"Yawns: {self.yawn_counter}/5", 
                           (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                y_pos += 30
            
            # Nail biting counter display
            if self.nail_biting_count > 0:
                # Color changes based on severity
                if self.nail_biting_count < 3:
                    counter_color = (0, 255, 255)  # Yellow - mild habit
                elif self.nail_biting_count < 6:
                    counter_color = (0, 165, 255)  # Orange - moderate habit
                else:
                    counter_color = (0, 0, 255)  # Red - anxiety level
                
                status_text = f"Nail biting: {self.nail_biting_count}"
                if self.nail_biting_count < 6:
                    status_text += f"/5 (habit)"
                else:
                    status_text += " (ANXIETY!)"
                
                cv2.putText(frame, status_text, 
                           (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.8, counter_color, 2)
                y_pos += 30
            
            # Show exit hint if any mode is active
            if any(active for _, active in statuses):
                cv2.putText(frame, "Show OK sign to exit", 
                           (10, y_pos + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            
            cv2.imshow('ZenSpace Enhanced Camera', frame)
            
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
        
        self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        self.brown_noise.stop()
        self.distraction_beeper.stop()
        self.posture_beeper.stop()
        self.zen_meditation.stop()
        self.energy_break.deactivate()
        self.posture_warning_overlay.deactivate()
        self.cap.release()
        cv2.destroyAllWindows()
        print("\n[DONE] ZenSpace Enhanced stopped")


if __name__ == "__main__":
    zenspace = ZenSpaceEnhanced()
    zenspace.run()
