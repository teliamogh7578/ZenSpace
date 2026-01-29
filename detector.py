# -*- coding: utf-8 -*-
"""
Detector Module - Gesture and Pose Detection
Handles MediaPipe detection and gesture recognition
"""

import mediapipe as mp
import math


class GestureDetector:
    """Handles all gesture and pose detection using MediaPipe"""
    
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            max_num_hands=2
        )
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def process_frame(self, rgb_frame):
        """Process a frame and return hand, pose, and face mesh results"""
        hand_results = self.hands.process(rgb_frame)
        pose_results = self.pose.process(rgb_frame)
        face_results = self.face_mesh.process(rgb_frame)
        return hand_results, pose_results, face_results
    
    def distance_2d(self, point1, point2, frame_shape):
        """Calculate 2D pixel distance"""
        h, w = frame_shape[:2]
        x1, y1 = int(point1.x * w), int(point1.y * h)
        x2, y2 = int(point2.x * w), int(point2.y * h)
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    
    def distance_normalized(self, point1, point2):
        """Calculate normalized distance between two points"""
        dx = point1.x - point2.x
        dy = point1.y - point2.y
        return math.sqrt(dx**2 + dy**2)
    
    def get_hand_center(self, hand_landmarks):
        """Get center point of hand"""
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        return (wrist.x, wrist.y, wrist.z)
    
    def fingers_extended(self, hand_landmarks):
        """Count how many fingers are extended"""
        landmarks = hand_landmarks.landmark
        extended = 0
        
        finger_tips = [
            (self.mp_hands.HandLandmark.INDEX_FINGER_TIP, self.mp_hands.HandLandmark.INDEX_FINGER_PIP),
            (self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP, self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP),
            (self.mp_hands.HandLandmark.RING_FINGER_TIP, self.mp_hands.HandLandmark.RING_FINGER_PIP),
            (self.mp_hands.HandLandmark.PINKY_TIP, self.mp_hands.HandLandmark.PINKY_PIP)
        ]
        
        for tip, pip in finger_tips:
            if landmarks[tip].y < landmarks[pip].y:
                extended += 1
                
        return extended
    
    # ==================== YAWN & FATIGUE DETECTION ====================
    
    def check_yawn(self, face_landmarks):
        """
        🥱 Detect yawn using Mouth Aspect Ratio (MAR)
        
        MAR = vertical_mouth_distance / horizontal_mouth_distance
        If MAR > 0.6, consider it a yawn
        """
        if not face_landmarks:
            return False
        
        try:
            # Mouth landmarks from MediaPipe Face Mesh
            # Upper lip: 13, Lower lip: 14
            # Left mouth corner: 61, Right mouth corner: 291
            
            upper_lip = face_landmarks.landmark[13]
            lower_lip = face_landmarks.landmark[14]
            left_corner = face_landmarks.landmark[61]
            right_corner = face_landmarks.landmark[291]
            
            # Calculate vertical distance (mouth opening)
            vertical_distance = self.distance_normalized(upper_lip, lower_lip)
            
            # Calculate horizontal distance (mouth width)
            horizontal_distance = self.distance_normalized(left_corner, right_corner)
            
            # Avoid division by zero
            if horizontal_distance == 0:
                return False
            
            # Calculate Mouth Aspect Ratio
            mouth_aspect_ratio = vertical_distance / horizontal_distance
            
            # Threshold: if MAR > 0.6, it's a yawn
            return mouth_aspect_ratio > 0.6
        except:
            return False
    
    def get_mouth_landmarks(self, face_landmarks):
        """Get mouth landmark points for visualization"""
        if not face_landmarks:
            return None
        
        try:
            mouth_points = {
                'upper_lip': face_landmarks.landmark[13],
                'lower_lip': face_landmarks.landmark[14],
                'left_corner': face_landmarks.landmark[61],
                'right_corner': face_landmarks.landmark[291],
                # Additional mouth contour points
                'top_upper': face_landmarks.landmark[11],
                'top_lower': face_landmarks.landmark[16],
            }
            return mouth_points
        except:
            return None
    
    # ==================== GESTURE RECOGNITION ====================
    
    def check_open_palm(self, hand_landmarks):
        """✋ Open Palm (Stop sign)"""
        if not hand_landmarks:
            return False
        
        for hand in hand_landmarks:
            extended = self.fingers_extended(hand)
            landmarks = hand.landmark
            
            if extended == 4:
                wrist = landmarks[self.mp_hands.HandLandmark.WRIST]
                middle_tip = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
                
                if middle_tip.z < wrist.z - 0.05:
                    return True
        return False
    
    def check_both_hands_raised(self, hand_landmarks, pose_landmarks):
        """🙌 Both hands raised"""
        if not hand_landmarks or len(hand_landmarks) < 2 or not pose_landmarks:
            return False
        
        nose = pose_landmarks.landmark[self.mp_pose.PoseLandmark.NOSE]
        
        hands_above_head = 0
        for hand in hand_landmarks:
            wrist = hand.landmark[self.mp_hands.HandLandmark.WRIST]
            if wrist.y < nose.y - 0.1:
                hands_above_head += 1
        
        return hands_above_head >= 2
    
    def check_hands_covering_ears(self, hand_landmarks, pose_landmarks):
        """🙉 Hands covering ears"""
        if not hand_landmarks or len(hand_landmarks) < 2 or not pose_landmarks:
            return False
        
        left_ear = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_EAR]
        right_ear = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_EAR]
        
        hands_near_ears = 0
        for hand in hand_landmarks:
            wrist = hand.landmark[self.mp_hands.HandLandmark.WRIST]
            
            dist_left = math.sqrt((wrist.x - left_ear.x)**2 + (wrist.y - left_ear.y)**2)
            dist_right = math.sqrt((wrist.x - right_ear.x)**2 + (wrist.y - right_ear.y)**2)
            
            if dist_left < 0.15 or dist_right < 0.15:
                hands_near_ears += 1
        
        return hands_near_ears >= 2
    
    def check_clenched_fist(self, hand_landmarks):
        """✊ Clenched fist"""
        if not hand_landmarks:
            return False
        
        for hand in hand_landmarks:
            extended = self.fingers_extended(hand)
            if extended == 0:
                return True
        return False
    
    def check_ok_sign(self, hand_landmarks):
        """👌 Thumb + index circle - More reliable detection"""
        if not hand_landmarks:
            return False
        
        for hand in hand_landmarks:
            landmarks = hand.landmark
            thumb_tip = landmarks[self.mp_hands.HandLandmark.THUMB_TIP]
            index_tip = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            middle_tip = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
            
            # Check if thumb and index are touching
            thumb_index_dist = math.sqrt(
                (thumb_tip.x - index_tip.x)**2 + 
                (thumb_tip.y - index_tip.y)**2
            )
            
            # Check that middle finger is extended (up)
            middle_pip = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
            middle_extended = middle_tip.y < middle_pip.y
            
            # OK sign: thumb and index touching, middle finger up
            if thumb_index_dist < 0.08 and middle_extended:
                return True
        return False
    
    def check_peace_sign(self, hand_landmarks):
        """✌️ Two fingers up"""
        if not hand_landmarks:
            return False
        
        for hand in hand_landmarks:
            landmarks = hand.landmark
            
            index_up = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP].y < \
                       landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_PIP].y
            middle_up = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y < \
                        landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y
            ring_down = landmarks[self.mp_hands.HandLandmark.RING_FINGER_TIP].y > \
                        landmarks[self.mp_hands.HandLandmark.RING_FINGER_PIP].y
            
            if index_up and middle_up and ring_down:
                return True
        return False
    
    def check_fingers_near_mouth(self, hand_landmarks, pose_landmarks, frame_shape):
        """🤏 Fingers near mouth"""
        if not hand_landmarks or not pose_landmarks:
            return False
        
        mouth_left = pose_landmarks.landmark[self.mp_pose.PoseLandmark.MOUTH_LEFT]
        mouth_right = pose_landmarks.landmark[self.mp_pose.PoseLandmark.MOUTH_RIGHT]
        
        for hand in hand_landmarks:
            for finger_idx in [
                self.mp_hands.HandLandmark.INDEX_FINGER_TIP,
                self.mp_hands.HandLandmark.THUMB_TIP
            ]:
                finger = hand.landmark[finger_idx]
                dist_left = self.distance_2d(finger, mouth_left, frame_shape)
                dist_right = self.distance_2d(finger, mouth_right, frame_shape)
                
                if dist_left < 50 or dist_right < 50:
                    return True
        return False
    
    def check_palms_together(self, hand_landmarks):
        """🤲 Palms together"""
        if not hand_landmarks or len(hand_landmarks) < 2:
            return False
        
        hand1 = hand_landmarks[0].landmark
        hand2 = hand_landmarks[1].landmark
        
        wrist1 = hand1[self.mp_hands.HandLandmark.WRIST]
        wrist2 = hand2[self.mp_hands.HandLandmark.WRIST]
        
        distance = math.sqrt((wrist1.x - wrist2.x)**2 + (wrist1.y - wrist2.y)**2)
        return distance < 0.15
    
    def check_looking_down_at_phone(self, pose_landmarks):
        """📱 Detect if user is looking down at phone (distraction)"""
        if not pose_landmarks:
            return False
        
        # Get key landmarks
        nose = pose_landmarks.landmark[self.mp_pose.PoseLandmark.NOSE]
        left_shoulder = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
        
        # Calculate average shoulder height
        shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        
        # Only check if nose is below shoulder height
        # When looking down at phone, nose drops below shoulders
        nose_below_shoulders = nose.y > shoulder_y
        
        return nose_below_shoulders

    
    def distance_2d(self, point1, point2, frame_shape):
        """Calculate 2D pixel distance"""
        h, w = frame_shape[:2]
        x1, y1 = int(point1.x * w), int(point1.y * h)
        x2, y2 = int(point2.x * w), int(point2.y * h)
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    
    def get_hand_center(self, hand_landmarks):
        """Get center point of hand"""
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        return (wrist.x, wrist.y, wrist.z)
    
    def fingers_extended(self, hand_landmarks):
        """Count how many fingers are extended"""
        landmarks = hand_landmarks.landmark
        extended = 0
        
        finger_tips = [
            (self.mp_hands.HandLandmark.INDEX_FINGER_TIP, self.mp_hands.HandLandmark.INDEX_FINGER_PIP),
            (self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP, self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP),
            (self.mp_hands.HandLandmark.RING_FINGER_TIP, self.mp_hands.HandLandmark.RING_FINGER_PIP),
            (self.mp_hands.HandLandmark.PINKY_TIP, self.mp_hands.HandLandmark.PINKY_PIP)
        ]
        
        for tip, pip in finger_tips:
            if landmarks[tip].y < landmarks[pip].y:
                extended += 1
                
        return extended
    
    # ==================== GESTURE RECOGNITION ====================
    
    def check_open_palm(self, hand_landmarks):
        """✋ Open Palm (Stop sign)"""
        if not hand_landmarks:
            return False
        
        for hand in hand_landmarks:
            extended = self.fingers_extended(hand)
            landmarks = hand.landmark
            
            if extended == 4:
                wrist = landmarks[self.mp_hands.HandLandmark.WRIST]
                middle_tip = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
                
                if middle_tip.z < wrist.z - 0.05:
                    return True
        return False
    
    def check_both_hands_raised(self, hand_landmarks, pose_landmarks):
        """🙌 Both hands raised"""
        if not hand_landmarks or len(hand_landmarks) < 2 or not pose_landmarks:
            return False
        
        nose = pose_landmarks.landmark[self.mp_pose.PoseLandmark.NOSE]
        
        hands_above_head = 0
        for hand in hand_landmarks:
            wrist = hand.landmark[self.mp_hands.HandLandmark.WRIST]
            if wrist.y < nose.y - 0.1:
                hands_above_head += 1
        
        return hands_above_head >= 2
    
    def check_hands_covering_ears(self, hand_landmarks, pose_landmarks):
        """🙉 Hands covering ears"""
        if not hand_landmarks or len(hand_landmarks) < 2 or not pose_landmarks:
            return False
        
        left_ear = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_EAR]
        right_ear = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_EAR]
        
        hands_near_ears = 0
        for hand in hand_landmarks:
            wrist = hand.landmark[self.mp_hands.HandLandmark.WRIST]
            
            dist_left = math.sqrt((wrist.x - left_ear.x)**2 + (wrist.y - left_ear.y)**2)
            dist_right = math.sqrt((wrist.x - right_ear.x)**2 + (wrist.y - right_ear.y)**2)
            
            if dist_left < 0.15 or dist_right < 0.15:
                hands_near_ears += 1
        
        return hands_near_ears >= 2
    
    def check_clenched_fist(self, hand_landmarks):
        """✊ Clenched fist"""
        if not hand_landmarks:
            return False
        
        for hand in hand_landmarks:
            extended = self.fingers_extended(hand)
            if extended == 0:
                return True
        return False
    
    def check_ok_sign(self, hand_landmarks):
        """👌 Thumb + index circle - More reliable detection"""
        if not hand_landmarks:
            return False
        
        for hand in hand_landmarks:
            landmarks = hand.landmark
            thumb_tip = landmarks[self.mp_hands.HandLandmark.THUMB_TIP]
            index_tip = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            middle_tip = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
            
            # Check if thumb and index are touching
            thumb_index_dist = math.sqrt(
                (thumb_tip.x - index_tip.x)**2 + 
                (thumb_tip.y - index_tip.y)**2
            )
            
            # Check that middle finger is extended (up)
            middle_pip = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
            middle_extended = middle_tip.y < middle_pip.y
            
            # OK sign: thumb and index touching, middle finger up
            if thumb_index_dist < 0.08 and middle_extended:
                return True
        return False
    
    def check_peace_sign(self, hand_landmarks):
        """✌️ Two fingers up"""
        if not hand_landmarks:
            return False
        
        for hand in hand_landmarks:
            landmarks = hand.landmark
            
            index_up = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP].y < \
                       landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_PIP].y
            middle_up = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y < \
                        landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y
            ring_down = landmarks[self.mp_hands.HandLandmark.RING_FINGER_TIP].y > \
                        landmarks[self.mp_hands.HandLandmark.RING_FINGER_PIP].y
            
            if index_up and middle_up and ring_down:
                return True
        return False
    
    def check_fingers_near_mouth(self, hand_landmarks, pose_landmarks, frame_shape):
        """🤏 Fingers near mouth"""
        if not hand_landmarks or not pose_landmarks:
            return False
        
        mouth_left = pose_landmarks.landmark[self.mp_pose.PoseLandmark.MOUTH_LEFT]
        mouth_right = pose_landmarks.landmark[self.mp_pose.PoseLandmark.MOUTH_RIGHT]
        
        for hand in hand_landmarks:
            for finger_idx in [
                self.mp_hands.HandLandmark.INDEX_FINGER_TIP,
                self.mp_hands.HandLandmark.THUMB_TIP
            ]:
                finger = hand.landmark[finger_idx]
                dist_left = self.distance_2d(finger, mouth_left, frame_shape)
                dist_right = self.distance_2d(finger, mouth_right, frame_shape)
                
                if dist_left < 50 or dist_right < 50:
                    return True
        return False
    
    def check_palms_together(self, hand_landmarks):
        """🤲 Palms together"""
        if not hand_landmarks or len(hand_landmarks) < 2:
            return False
        
        hand1 = hand_landmarks[0].landmark
        hand2 = hand_landmarks[1].landmark
        
        wrist1 = hand1[self.mp_hands.HandLandmark.WRIST]
        wrist2 = hand2[self.mp_hands.HandLandmark.WRIST]
        
        distance = math.sqrt((wrist1.x - wrist2.x)**2 + (wrist1.y - wrist2.y)**2)
        return distance < 0.15
    
    def check_looking_down_at_phone(self, pose_landmarks):
        """📱 Detect if user is looking down at phone (distraction)"""
        if not pose_landmarks:
            return False
        
        # Get key landmarks
        nose = pose_landmarks.landmark[self.mp_pose.PoseLandmark.NOSE]
        left_shoulder = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
        
        # Calculate average shoulder height
        shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        
        # Only check if nose is below shoulder height
        # When looking down at phone, nose drops below shoulders
        nose_below_shoulders = nose.y > shoulder_y
        
        return nose_below_shoulders
    
    def check_bad_posture(self, pose_landmarks):
        """
        🧍 Comprehensive bad posture detection
        Returns: (is_bad_posture, posture_issues_dict)
        
        Checks for:
        - Forward head posture (tech neck)
        - Rounded shoulders
        - Slouched back
        - Uneven shoulders
        """
        if not pose_landmarks:
            return False, {}
        
        issues = {
            'forward_head': False,
            'rounded_shoulders': False,
            'slouched': False,
            'uneven_shoulders': False
        }
        
        # Get key landmarks
        nose = pose_landmarks.landmark[self.mp_pose.PoseLandmark.NOSE]
        left_shoulder = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_ear = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_EAR]
        right_ear = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_EAR]
        left_hip = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_HIP]
        
        # Calculate reference points
        shoulder_mid_x = (left_shoulder.x + right_shoulder.x) / 2
        shoulder_mid_y = (left_shoulder.y + right_shoulder.y) / 2
        ear_mid_x = (left_ear.x + right_ear.x) / 2
        hip_mid_x = (left_hip.x + right_hip.x) / 2
        hip_mid_y = (left_hip.y + right_hip.y) / 2
        
        # 1. FORWARD HEAD POSTURE (Tech Neck)
        head_forward_distance = abs(ear_mid_x - shoulder_mid_x)
        if head_forward_distance > 0.08:
            issues['forward_head'] = True
        
        # 2. SLOUCHED/HUNCHED
        if nose.y > shoulder_mid_y + 0.12:
            issues['slouched'] = True
        
        # 3. ROUNDED SHOULDERS
        shoulder_hip_distance = abs(shoulder_mid_x - hip_mid_x)
        if shoulder_hip_distance > 0.06:
            issues['rounded_shoulders'] = True
        
        # 4. UNEVEN SHOULDERS
        shoulder_height_diff = abs(left_shoulder.y - right_shoulder.y)
        if shoulder_height_diff > 0.05:
            issues['uneven_shoulders'] = True
        
        has_bad_posture = any(issues.values())
        
        return has_bad_posture, issues
    
    def get_posture_visualization_points(self, pose_landmarks):
        """Get key points for posture visualization"""
        if not pose_landmarks:
            return None
        
        return {
            'nose': pose_landmarks.landmark[self.mp_pose.PoseLandmark.NOSE],
            'left_ear': pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_EAR],
            'right_ear': pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_EAR],
            'left_shoulder': pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER],
            'right_shoulder': pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER],
            'left_hip': pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_HIP],
            'right_hip': pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_HIP],
        }
