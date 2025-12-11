import math
import random
import os
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QProgressBar, QApplication
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QFont, QCursor, QPainter, QBrush, QPen, QColor, QPainterPath, QPixmap, QLinearGradient, QRadialGradient

class PetUI(QWidget):
    clicked = pyqtSignal()
    double_clicked = pyqtSignal()

    def __init__(self, pet_state):
        super().__init__()
        self.pet_state = pet_state
        
        # Animation State
        self.anim_tick = 0
        self.is_blinking = False
        self.target_x = 0
        self.is_moving = False
        
        # Action State
        self.current_action = "idle" # idle, stretch, jump
        self.equipped_item = None 
        
        # Sprite Images
        self.sprites = self.load_sprites()
        
        self.init_ui()
        
        # Stat update timer (1 second)
        self.stat_timer = QTimer(self)
        self.stat_timer.timeout.connect(self.update_stats)
        self.stat_timer.start(1000)
        
        # Animation timer (50ms ~ 20fps)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate)
        self.anim_timer.start(50)

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(100, 100, 200, 300)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Bubble Label
        self.bubble_label = QLabel("안녕! 나는 너의 펫이야.")
        self.bubble_label.setStyleSheet("""
            background-color: white;
            border: 2px solid #333;
            border-radius: 10px;
            padding: 5px;
            color: black;
            font-weight: bold;
        """)
        self.bubble_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bubble_label.setWordWrap(True)
        self.bubble_label.setFixedHeight(60)
        layout.addWidget(self.bubble_label)
        
        layout.addStretch(1)
        self.setLayout(layout)
        self.old_pos = None

    def update_stats(self):
        self.pet_state.update_time_based_stats()

    def animate(self):
        self.anim_tick += 1
        
        if self.anim_tick % 80 == 0: 
            if random.random() < 0.2:
                self.is_blinking = True
        if self.is_blinking and self.anim_tick % 85 == 0:
            self.is_blinking = False
            
        self.update() 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Enable proper alpha blending for transparency
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        
        # Clear background to transparent
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        char_type = self.pet_state.character_type
        
        # Dispatch to specific drawer
        if char_type == "slime":
            self.draw_slime(painter)
        elif char_type == "rock":
            self.draw_rock(painter)
        elif char_type == "dog":
            self.draw_dog(painter)
        elif char_type == "ghost":
            self.draw_ghost(painter)
        elif char_type == "robot":
            self.draw_robot(painter)
        elif char_type == "cloud":
            self.draw_cloud(painter)
        elif char_type == "egg":
            self.draw_egg(painter)
        else: # default
            self.draw_default(painter)

    # --- Drawing Types ---
    
    def load_sprites(self):
        """Load sprite images from artifacts directory and local assets"""
        # Disabled: Using QPainter rendering for better visual effects
        print("[PetUI] Sprite loading disabled - using QPainter rendering")
        return {}


    def draw_default(self, painter):
        stage = self.pet_state.evolution_stage
        
        # Try to use sprite image first
        sprite_key = f"default_{stage}"
        if sprite_key in self.sprites:
            cx = self.width() / 2
            cy = self.height() - 50
            bob_offset = math.sin(self.anim_tick * 0.1) * 3
            
            pixmap = self.sprites[sprite_key]
            # Scale to appropriate size
            scaled = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            x = int(cx - scaled.width() / 2)
            y = int(cy - scaled.height() / 2 - bob_offset)
            painter.drawPixmap(x, y, scaled)
            
            # Still draw equipped item
            self.draw_equipped_item(painter, cx, cy, 80, 50, bob_offset, floating=True)
            return
        
        # Fallback to QPainter rendering
        cx = self.width() / 2
        cy = self.height() - 50 
        bob_offset = math.sin(self.anim_tick * 0.1) * 3
        
        # Colors
        base_color = "#FFD700" 
        outline_color = "#000000"
        
        if stage == 3: # King Potato
             base_color = "#FFD700" # Golden
        
        body_color, outline_color = self.get_state_colors(base_color, outline_color)
        
        pen = QPen(outline_color, 3)
        painter.setPen(pen)
        painter.setBrush(QBrush(body_color))
        
        # Stage 3 Cape (Draw behind)
        if stage == 3:
            painter.save()
            painter.setBrush(QBrush(QColor("red")))
            painter.drawPolygon([
                QPointF(cx - 15, cy - 30 - bob_offset),
                QPointF(cx + 15, cy - 30 - bob_offset),
                QPointF(cx + 25, cy + 10 - bob_offset),
                QPointF(cx - 25, cy + 10 - bob_offset)
            ])
            painter.restore()

        # Body
        body_w, body_h = 40, 40
        body_rect = QRectF(cx - body_w/2, cy - body_h/2 - bob_offset + 25, body_w, body_h)
        painter.drawRoundedRect(body_rect, 10, 10)
        
        # Head
        head_w, head_h = 70, 60
        head_cx = cx
        head_cy = cy - body_h - bob_offset + 10
        painter.drawEllipse(QPointF(head_cx, head_cy), head_w/2, head_h/2)
        
        # Evolution Accessories (Front)
        if stage == 2: # Warrior Headband
            painter.save()
            painter.setBrush(QBrush(QColor("red")))
            painter.drawRect(int(head_cx - 35), int(head_cy - 20), 70, 10)
            painter.drawEllipse(QPointF(head_cx, head_cy - 15), 5, 5) # Gem
            painter.restore()
        elif stage == 3: # King Crown
            painter.save()
            painter.setBrush(QBrush(QColor("gold")))
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            # Crown Polygon
            crown_base_y = head_cy - 25
            painter.drawPolygon([
                QPointF(head_cx - 20, crown_base_y),
                QPointF(head_cx - 20, crown_base_y - 20),
                QPointF(head_cx - 10, crown_base_y - 10),
                QPointF(head_cx, crown_base_y - 25), # Center peak
                QPointF(head_cx + 10, crown_base_y - 10),
                QPointF(head_cx + 20, crown_base_y - 20),
                QPointF(head_cx + 20, crown_base_y)
            ])
            painter.restore()

        # Face & Limbs
        self.draw_derpy_face(painter, head_cx, head_cy)
        self.draw_limbs(painter, cx, cy, body_w, body_h, bob_offset, body_rect, stick=True)
        self.draw_equipped_item(painter, cx, cy, body_w, body_h, bob_offset)

    def draw_slime(self, painter):
        stage = self.pet_state.evolution_stage
        
        # Try to use sprite image first
        sprite_key = f"slime_{stage}"
        if sprite_key in self.sprites:
            cx = self.width() / 2
            cy = self.height() - 50
            wobble = math.sin(self.anim_tick * 0.2) * 2
            
            sprite = self.sprites[sprite_key]
            x = int(cx - sprite.width() / 2)
            y = int(cy - sprite.height() + wobble)
            painter.drawPixmap(x, y, sprite)
            self.draw_equipped_item(painter, cx, cy, sprite.width(), sprite.height(), 0, floating=True)
            return
        
        # Fallback to QPainter rendering
        cx = self.width() / 2
        cy = self.height() - 50 
        # Slime wobble
        wobble = math.sin(self.anim_tick * 0.2) * 2
        stretch = math.cos(self.anim_tick * 0.2) * 2
        
        size_mult = 1.0
        if stage >= 2: size_mult = 1.4 # Mega - bigger
        if stage == 3: size_mult = 1.7 # King - much bigger!
        
        body_color_hex = "#8A2BE2"
        if stage == 2: body_color_hex = "#9400D3" # Darker Violet
        if stage == 3: body_color_hex = "#6A0DAD" # Royal Purple
        
        body_color, outline_color = self.get_state_colors(body_color_hex, "#4B0082") 
        
        # Stage 3: Glowing aura effect
        if stage == 3:
            painter.save()
            for i in range(3):
                aura_gradient = QRadialGradient(cx, cy - (25*size_mult), 60 + i*10)
                aura_gradient.setColorAt(0, QColor(138, 43, 226, 80 - i*20))
                aura_gradient.setColorAt(1, QColor(138, 43, 226, 0))
                painter.setBrush(QBrush(aura_gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(cx, cy - (25*size_mult)), 60 + i*10, 50 + i*8)
            painter.restore()
        
        # Create radial gradient for 3D slime effect
        gradient = QRadialGradient(cx, cy - (25*size_mult), 40*size_mult)
        gradient.setColorAt(0, QColor(body_color).lighter(170))  # Brighter center
        gradient.setColorAt(0.5, QColor(body_color))
        gradient.setColorAt(1, QColor(body_color).darker(140))   # Darker edges
        
        outline_width = 3 if stage < 3 else 4
        painter.setPen(QPen(outline_color, outline_width))
        painter.setBrush(QBrush(gradient))
        
        # Blob shape
        path = QPainterPath()
        path.moveTo(cx - (30*size_mult) - stretch, cy)
        # Top curve
        path.cubicTo(cx - (30*size_mult), cy - (50*size_mult) + wobble, cx + (30*size_mult), cy - (50*size_mult) - wobble, cx + (30*size_mult) + stretch, cy)
        # Bottom flat-ish
        path.quadTo(cx, cy + 10, cx - (30*size_mult) - stretch, cy)
        
        painter.drawPath(path)
        
        # Evolution: Spikes (Stage 2+) with gradient - MORE SPIKES!
        if stage >= 2:
            painter.save()
            spike_gradient = QLinearGradient(cx - 20, cy - (45*size_mult), cx - 20, cy - (65*size_mult))
            spike_gradient.setColorAt(0, QColor(body_color))
            spike_gradient.setColorAt(1, QColor(body_color).lighter(150))
            painter.setBrush(QBrush(spike_gradient))
            # Draw multiple spikes
            spike_count = 3 if stage == 2 else 5
            spike_spacing = 15
            start_x = cx - (spike_count * spike_spacing / 2)
            for i in range(spike_count):
                sx = start_x + (i * spike_spacing)
                sy = cy - (45*size_mult) + wobble
                spike_height = 15 if stage == 2 else 20
                painter.drawPolygon([QPointF(sx, sy), QPointF(sx+7, sy-spike_height), QPointF(sx+14, sy)])
            painter.restore()

        # Evolution: Crown (Stage 3) with metallic gradient - BIGGER CROWN!
        if stage == 3:
            painter.save()
            crown_gradient = QLinearGradient(cx - 20, cy - (60*size_mult), cx + 20, cy - (60*size_mult))
            crown_gradient.setColorAt(0, QColor("#FFD700"))      # Gold
            crown_gradient.setColorAt(0.5, QColor("#FFF8DC"))    # Bright
            crown_gradient.setColorAt(1, QColor("#DAA520"))      # Dark gold
            painter.setBrush(QBrush(crown_gradient))
            painter.setPen(QPen(QColor("#B8860B"), 2))
            painter.drawRect(int(cx - 15), int(cy - (55*size_mult)), 30, 10) # Crown
            # Crown points
            for i in range(3):
                x = cx - 10 + (i * 10)
                painter.drawPolygon([
                    QPointF(x - 3, cy - (55*size_mult)),
                    QPointF(x, cy - (60*size_mult)),
                    QPointF(x + 3, cy - (55*size_mult))
                ])
            painter.restore()

        # Face (Simple Cute)
        self.draw_simple_face(painter, cx, cy - (20*size_mult))
        
        self.draw_equipped_item(painter, cx, cy, 60*size_mult, 50*size_mult, 0, floating=True)

    def draw_rock(self, painter):
        stage = self.pet_state.evolution_stage
        
        # Try to use sprite image first
        sprite_key = f"rock_{stage}"
        if sprite_key in self.sprites:
            cx = self.width() / 2
            cy = self.height() - 50
            bob_offset = math.sin(self.anim_tick * 0.05) * 1
            
            pixmap = self.sprites[sprite_key]
            scaled = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            x = int(cx - scaled.width() / 2)
            y = int(cy - scaled.height() / 2 - bob_offset)
            painter.drawPixmap(x, y, scaled)
            
            self.draw_equipped_item(painter, cx, cy, 80, 50, bob_offset, floating=True)
            return
        
        # Fallback to QPainter rendering
        cx = self.width() / 2
        cy = self.height() - 50 
        bob_offset = math.sin(self.anim_tick * 0.05) * 1 
        
        size = 1.0
        if stage == 3: size = 1.4 # Titan
        
        fill_color = "#808080"
        line_color = "#2F4F4F"
        
        if stage == 3: # Magma
            fill_color = "#404040" # Dark Grey
            line_color = "#FF4500" # Orange Red Glow
            
        body_color, outline_color = self.get_state_colors(fill_color, line_color)
        
        pen_width = 4
        if stage == 3: pen_width = 6
        
        painter.setPen(QPen(outline_color, pen_width))
        painter.setBrush(QBrush(body_color))
        
        # Angular Body (Scaled)
        points = [
            QPointF(cx - 25*size, cy - 40*size - bob_offset),
            QPointF(cx + 20*size, cy - 45*size - bob_offset),
            QPointF(cx + 35*size, cy - 10*size - bob_offset),
            QPointF(cx + 10*size, cy + 10*size - bob_offset),
            QPointF(cx - 30*size, cy + 5*size - bob_offset)
        ]
        painter.drawPolygon(points)
        
        # Magma Cracks (Stage 3)
        if stage == 3:
            painter.save()
            painter.setPen(QPen(QColor("#FF4500"), 2)) # Magma
            painter.drawLine(int(cx), int(cy - 20*size), int(cx - 10), int(cy + 5))
            painter.drawLine(int(cx), int(cy - 20*size), int(cx + 15), int(cy - 10))
            painter.restore()

        # Face 
        eye_color = Qt.GlobalColor.black
        if stage >= 2: eye_color = Qt.GlobalColor.yellow # Glowing eyes for Golem
        
        # Custom face drawing for Rock since we need color control
        painter.save()
        painter.setBrush(QBrush(eye_color))
        # Angled Eyes
        eye_y = cy - 20*size - bob_offset
        painter.drawLine(int(cx - 10*size), int(eye_y - 2), int(cx - 2*size), int(eye_y + 2))
        painter.drawLine(int(cx + 10*size), int(eye_y - 2), int(cx + 2*size), int(eye_y + 2))
        painter.restore()
        
        # Arms (Floating Rocks)
        arm_y = cy - 20*size - bob_offset
        painter.drawEllipse(QPointF(cx - 40*size, arm_y), 8*size, 8*size)
        painter.drawEllipse(QPointF(cx + 40*size, arm_y), 8*size, 8*size)
        
        self.draw_equipped_item(painter, cx, cy, 80*size, 50*size, bob_offset, floating=True)

    def draw_dog(self, painter):
        stage = self.pet_state.evolution_stage
        
        # Try to use sprite image first
        sprite_key = f"dog_{stage}"
        if sprite_key in self.sprites:
            cx = self.width() / 2
            cy = self.height() - 50
            bob_offset = math.sin(self.anim_tick * 0.1) * 2
            
            sprite = self.sprites[sprite_key]
            x = int(cx - sprite.width() / 2)
            y = int(cy - sprite.height() + bob_offset)
            painter.drawPixmap(x, y, sprite)
            self.draw_equipped_item(painter, cx, cy, sprite.width(), sprite.height(), bob_offset)
            return
        
        # Fallback to QPainter rendering
        cx = self.width() / 2
        cy = self.height() - 50 
        bob_offset = math.sin(self.anim_tick * 0.1) * 2
        
        # Colors
        base = "#D2691E" # Brown
        out = "#8B4513"
        size_mult = 1.0
        
        if stage == 2: # Wolf
             base = "#A9A9A9" # Dark Grey
             out = "#2F4F4F"
             size_mult = 1.2
        elif stage == 3: # Fenrir
             base = "#191970" # Midnight Blue
             out = "#00FFFF" # Cyan Glow
             size_mult = 1.5  # Much bigger!
        
        body_color, outline_color = self.get_state_colors(base, out)
        
        # Fenrir Aura - MUCH MORE IMPRESSIVE!
        if stage == 3:
            painter.save()
            # Multiple layered auras
            for i in range(4):
                aura_gradient = QRadialGradient(cx, cy - 20, 70 + i*15)
                aura_gradient.setColorAt(0, QColor(0, 255, 255, 120 - i*25))
                aura_gradient.setColorAt(0.5, QColor(0, 200, 255, 80 - i*15))
                aura_gradient.setColorAt(1, QColor(0, 255, 255, 0))
                painter.setBrush(QBrush(aura_gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(cx, cy - 20), 70 + i*15, 55 + i*12)
            # Blue flame particles
            for j in range(6):
                angle = (self.anim_tick * 0.05 + j * 60) % 360
                rad = math.radians(angle)
                px = cx + math.cos(rad) * 60
                py = cy - 20 + math.sin(rad) * 45
                flame_grad = QRadialGradient(px, py, 8)
                flame_grad.setColorAt(0, QColor(100, 200, 255, 200))
                flame_grad.setColorAt(1, QColor(0, 150, 255, 0))
                painter.setBrush(QBrush(flame_grad))
                painter.drawEllipse(QPointF(px, py), 8, 8)
            painter.restore()
        
        painter.setPen(QPen(outline_color, 2))
        
        # Body (Horizontal Oval) with gradient
        body_gradient = QLinearGradient(cx, cy - 10 - bob_offset - 20, cx, cy - 10 - bob_offset + 20)
        body_gradient.setColorAt(0, QColor(body_color).lighter(120))
        body_gradient.setColorAt(1, QColor(body_color).darker(120))
        painter.setBrush(QBrush(body_gradient))
        painter.drawEllipse(QPointF(cx, cy - 10 - bob_offset), 30, 20)
        
        # Head with gradient
        head_cx = cx - 20
        head_cy = cy - 25 - bob_offset
        head_gradient = QRadialGradient(head_cx, head_cy, 20)
        head_gradient.setColorAt(0, QColor(body_color).lighter(130))
        head_gradient.setColorAt(1, QColor(body_color))
        painter.setBrush(QBrush(head_gradient))
        painter.drawEllipse(QPointF(head_cx, head_cy), 20, 18)
        
        # Ears (Sharpness increases)
        ear_h = 10
        if stage >= 2: ear_h = 15 # Wolf ears
        
        painter.setBrush(QBrush(body_color)) # Solid color for ears
        painter.drawPolygon([QPointF(head_cx - 15, head_cy - 5), QPointF(head_cx - 5, head_cy - 15 - ear_h), QPointF(head_cx + 5, head_cy - 15)])
        painter.drawPolygon([QPointF(head_cx + 5, head_cy - 15), QPointF(head_cx + 15, head_cy - 15 - ear_h), QPointF(head_cx + 15, head_cy - 5)])
        
        # Legs (More defined)
        leg_y = cy + 5 - bob_offset
        painter.setPen(QPen(outline_color, 3)) # Thicker pen for legs
        painter.drawLine(int(cx - 15), int(leg_y - 10), int(cx - 15), int(leg_y + 5))
        painter.drawLine(int(cx - 5), int(leg_y - 8), int(cx - 5), int(leg_y + 5))
        painter.drawLine(int(cx + 15), int(leg_y - 10), int(cx + 15), int(leg_y + 5))
        painter.drawLine(int(cx + 25), int(leg_y - 8), int(cx + 25), int(leg_y + 5))
        
        # Tail
        tail_tick = math.sin(self.anim_tick * 0.5) * 10
        tail_len = 10
        if stage >= 2: tail_len = 20 # Bushy tail
        
        painter.setPen(QPen(outline_color, 2))
        painter.drawLine(int(cx + 30), int(cy - 15 - bob_offset), int(cx + 30 + tail_len), int(cy - 25 - bob_offset + tail_tick))
        
        self.draw_simple_face(painter, head_cx + 5, head_cy + 2) 
        self.draw_equipped_item(painter, cx, cy, 60, 40, bob_offset, floating=True) 

    def draw_ghost(self, painter):
        stage = self.pet_state.evolution_stage
        
        # Try to use sprite image first
        sprite_key = f"ghost_{stage}"
        if sprite_key in self.sprites:
            cx = self.width() / 2
            cy = self.height() - 50
            float_y = math.sin(self.anim_tick * 0.1) * 5
            
            sprite = self.sprites[sprite_key]
            x = int(cx - sprite.width() / 2)
            y = int(cy - sprite.height() + float_y)
            painter.drawPixmap(x, y, sprite)
            self.draw_equipped_item(painter, cx, cy, sprite.width(), sprite.height(), float_y, floating=True)
            return
        
        # Fallback to QPainter rendering
        cx = self.width() / 2
        cy = self.height() - 50
        float_y = math.sin(self.anim_tick * 0.08) * 5
        
        base = "#F8F8FF"
        size_mult = 1.0
        if stage == 2: 
            base = "#E6E6FA" # Lavender
            size_mult = 1.2
        if stage == 3: 
            base = "#2F4F4F" # Dark Slate Gray (Grim Reaper)
            size_mult = 1.5
        
        body_color, outline_color = self.get_state_colors(base, "#000000")
        
        # Stage 3: Dark aura and red energy
        if stage == 3:
            painter.save()
            # Dark purple aura
            for i in range(3):
                aura_gradient = QRadialGradient(cx, cy - 30 + float_y, 60 + i*15)
                aura_gradient.setColorAt(0, QColor(128, 0, 128, 100 - i*25))
                aura_gradient.setColorAt(1, QColor(75, 0, 130, 0))
                painter.setBrush(QBrush(aura_gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(cx, cy - 30 + float_y), 60 + i*15, 55 + i*12)
            # Red soul particles
            for j in range(5):
                angle = (self.anim_tick * 0.08 + j * 72) % 360
                rad = math.radians(angle)
                px = cx + math.cos(rad) * 50
                py = cy - 30 + float_y + math.sin(rad) * 40
                soul_grad = QRadialGradient(px, py, 6)
                soul_grad.setColorAt(0, QColor(255, 50, 50, 200))
                soul_grad.setColorAt(1, QColor(200, 0, 0, 0))
                painter.setBrush(QBrush(soul_grad))
                painter.drawEllipse(QPointF(px, py), 6, 6)
            painter.restore()
        
        painter.setPen(QPen(outline_color, 2))
        
        # Stage 3 Wings (Behind)
        if stage == 3:
            painter.save()
            wing_gradient = QLinearGradient(cx, cy - 40 + float_y, cx, cy + 10 + float_y)
            wing_gradient.setColorAt(0, QColor("black").lighter(150))
            wing_gradient.setColorAt(1, QColor("black").darker(150))
            painter.setBrush(QBrush(wing_gradient))
            painter.setPen(QPen(QColor("#444444"), 1)) # Darker outline for wings
            # Simple wing shapes
            painter.drawPolygon([QPointF(cx, cy), QPointF(cx - 60, cy - 40 + float_y), QPointF(cx - 30, cy + 10 + float_y)])
            painter.drawPolygon([QPointF(cx, cy), QPointF(cx + 60, cy - 40 + float_y), QPointF(cx + 30, cy + 10 + float_y)])
            painter.restore()

        painter.setPen(QPen(outline_color, 1))
        
        # Body with gradient
        body_gradient = QLinearGradient(cx, cy - 40 + float_y, cx, cy + 20 + float_y)
        body_gradient.setColorAt(0, QColor(body_color).lighter(120))
        body_gradient.setColorAt(1, QColor(body_color).darker(120))
        painter.setBrush(QBrush(body_gradient))

        # Body
        path = QPainterPath()
        path.moveTo(cx - 20 * size_mult, cy + 20 * size_mult + float_y)
        path.lineTo(cx - 20 * size_mult, cy - 20 * size_mult + float_y)
        path.arcTo(cx - 20 * size_mult, cy - 40 * size_mult + float_y, 40 * size_mult, 40 * size_mult, 180, -180) 
        path.lineTo(cx + 20 * size_mult, cy + 20 * size_mult + float_y)
        
        # Hood for Stage 2+
        if stage >= 2:
             painter.drawChord(int(cx - 22 * size_mult), int(cy - 42 * size_mult + float_y), int(44 * size_mult), int(44 * size_mult), 30 * 16, 120 * 16)

        # Tail (more defined curves)
        for i in range(4):
            x_offset = (i % 2) * 5 * size_mult # Alternate left/right for more organic look
            path.quadTo(cx + 20 * size_mult - (i * 10 * size_mult) - x_offset, cy + 30 * size_mult + float_y + (i*2*size_mult), cx + 20 * size_mult - ((i+1) * 10 * size_mult) + x_offset, cy + 20 * size_mult + float_y + (i*2*size_mult))
            
        painter.drawPath(path)
        
        # Scythe (Stage 2+)
        if stage >= 2:
            painter.save()
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.setBrush(QBrush(QColor("#555555"))) # Scythe handle color
            painter.drawLine(int(cx + 25 * size_mult), int(cy + 10 * size_mult + float_y), int(cx + 35 * size_mult), int(cy - 40 * size_mult + float_y)) # Handle
            
            scythe_blade_gradient = QLinearGradient(cx + 15 * size_mult, cy - 60 * size_mult + float_y, cx + 55 * size_mult, cy - 20 * size_mult + float_y)
            scythe_blade_gradient.setColorAt(0, QColor("#AAAAAA"))
            scythe_blade_gradient.setColorAt(1, QColor("#333333"))
            painter.setBrush(QBrush(scythe_blade_gradient))
            painter.drawArc(int(cx + 15 * size_mult), int(cy - 60 * size_mult + float_y), int(40 * size_mult), int(40 * size_mult), 200 * 16, 120 * 16) # Blade
            painter.restore()

        self.draw_simple_face(painter, cx, cy - 10 + float_y)
        self.draw_equipped_item(painter, cx, cy, 40, 40, -float_y, floating=True)

    def draw_robot(self, painter):
        stage = self.pet_state.evolution_stage
        
        # Try to use sprite image first
        sprite_key = f"robot_{stage}"
        if sprite_key in self.sprites:
            cx = self.width() / 2
            cy = self.height() - 50
            bob_offset = math.sin(self.anim_tick * 0.1) * 2
            
            sprite = self.sprites[sprite_key]
            x = int(cx - sprite.width() / 2)
            y = int(cy - sprite.height() + bob_offset)
            painter.drawPixmap(x, y, sprite)
            self.draw_equipped_item(painter, cx, cy, sprite.width(), sprite.height(), bob_offset)
            return
        
        # Fallback to QPainter rendering
        cx = self.width() / 2
        cy = self.height() - 50 
        bob_offset = math.sin(self.anim_tick * 0.1) * 2
        
        base = "#C0C0C0"
        size_mult = 1.0
        if stage == 2: 
            base = "#FFFFFF" # White Android
            size_mult = 1.2
        if stage == 3: 
            base = "#8B0000" # Dark Red Mecha
            size_mult = 1.5
        
        body_color, outline_color = self.get_state_colors(base, "#000000")
        
        # Stage 3: Red energy field and thrusters
        if stage == 3:
            painter.save()
            # Red energy field
            for i in range(3):
                energy_gradient = QRadialGradient(cx, cy - 20, 65 + i*12)
                energy_gradient.setColorAt(0, QColor(255, 0, 0, 90 - i*20))
                energy_gradient.setColorAt(1, QColor(139, 0, 0, 0))
                painter.setBrush(QBrush(energy_gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(cx, cy - 20), 65 + i*12, 50 + i*10)
            # Thruster flames
            for j in range(4):
                offset = math.sin(self.anim_tick * 0.2 + j) * 3
                fx = cx - 20 + j * 13
                fy = cy + 10 + offset
                flame_grad = QLinearGradient(fx, fy, fx, fy + 15)
                flame_grad.setColorAt(0, QColor(255, 200, 0, 220))
                flame_grad.setColorAt(0.5, QColor(255, 100, 0, 180))
                flame_grad.setColorAt(1, QColor(255, 0, 0, 0))
                painter.setBrush(QBrush(flame_grad))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(fx, fy), 4, 8 + offset)
            painter.restore() 
        
        painter.setPen(QPen(outline_color, 2))
        
        # Shoulder Cannons (Stage 3)
        if stage == 3:
            painter.save()
            cannon_gradient = QLinearGradient(cx - 35 * size_mult, cy - 55 * size_mult - bob_offset, cx - 35 * size_mult, cy - 35 * size_mult - bob_offset)
            cannon_gradient.setColorAt(0, QColor("#2F4F4F").lighter(120))
            cannon_gradient.setColorAt(1, QColor("#2F4F4F").darker(120))
            painter.setBrush(QBrush(cannon_gradient))
            painter.drawRect(int(cx - 35 * size_mult), int(cy - 55 * size_mult - bob_offset), int(15 * size_mult), int(20 * size_mult))
            painter.drawRect(int(cx + 20 * size_mult), int(cy - 55 * size_mult - bob_offset), int(15 * size_mult), int(20 * size_mult))
            painter.restore()

        # Head with gradient
        head_shape = QRectF(cx - 20 * size_mult, cy - 50 * size_mult - bob_offset, 40 * size_mult, 35 * size_mult)
        head_gradient = QLinearGradient(head_shape.topLeft(), head_shape.bottomRight())
        head_gradient.setColorAt(0, QColor(body_color).lighter(130))
        head_gradient.setColorAt(1, QColor(body_color).darker(130))
        painter.setBrush(QBrush(head_gradient))

        if stage >= 2: # Rounded head
            painter.drawRoundedRect(head_shape, 10 * size_mult, 10 * size_mult)
        else:
            painter.drawRect(head_shape)
            
        # Left Eye Scope (Stage 3)
        if stage == 3:
            painter.save()
            painter.setBrush(QBrush(Qt.GlobalColor.red))
            painter.drawEllipse(QPointF(cx - 10 * size_mult, cy - 40 * size_mult - bob_offset), 6 * size_mult, 6 * size_mult)
            painter.restore()

        # Antenna
        if stage == 1:
            painter.drawLine(int(cx), int(cy - 50 - bob_offset), int(cx), int(cy - 65 - bob_offset))
            painter.setBrush(QBrush(Qt.GlobalColor.red))
            painter.drawEllipse(QPointF(cx, cy - 65 - bob_offset), 3, 3)
        
        # Body with gradient
        body_rect = QRectF(cx - 15 * size_mult, cy - 15 * size_mult - bob_offset, 30 * size_mult, 25 * size_mult)
        body_gradient = QLinearGradient(body_rect.topLeft(), body_rect.bottomRight())
        body_gradient.setColorAt(0, QColor(body_color).lighter(120))
        body_gradient.setColorAt(1, QColor(body_color).darker(120))
        painter.setBrush(QBrush(body_gradient))
        painter.drawRect(body_rect)
        
        # Face (Digital)
        self.draw_digital_face(painter, cx, cy - 35 * size_mult - bob_offset)
        
        # Limbs (more robust)
        painter.setPen(QPen(outline_color, 3)) # Thicker lines for limbs
        painter.drawLine(int(cx - 15 * size_mult), int(cy - 10 * size_mult - bob_offset), int(cx - 25 * size_mult), int(cy + 5 * size_mult - bob_offset))
        painter.drawLine(int(cx + 15 * size_mult), int(cy - 10 * size_mult - bob_offset), int(cx + 25 * size_mult), int(cy + 5 * size_mult - bob_offset))
        
        self.draw_equipped_item(painter, cx, cy, 50 * size_mult, 50 * size_mult, bob_offset)

    def draw_cloud(self, painter):
        stage = self.pet_state.evolution_stage
        
        # Try to use sprite image first
        sprite_key = f"cloud_{stage}"
        if sprite_key in self.sprites:
            cx = self.width() / 2
            cy = self.height() - 50
            bob = math.sin(self.anim_tick * 0.08) * 4
            
            pixmap = self.sprites[sprite_key]
            scaled = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            x = int(cx - scaled.width() / 2)
            y = int(cy - scaled.height() / 2 - bob)
            painter.drawPixmap(x, y, scaled)
            
            self.draw_equipped_item(painter, cx, cy, 80, 50, bob, floating=True)
            return
        
        # Fallback to QPainter rendering
        cx = self.width() / 2
        cy = self.height() - 50
        bob = math.sin(self.anim_tick * 0.08) * 4 # Use bob for vertical movement
        
        base = "#E0FFFF"
        out = "#87CEEB"
        size_mult = 1.0
        
        if stage == 2: # Thunder
             base = "#778899"
             out = "#2F4F4F"
             size_mult = 1.2
        if stage == 3: # Storm
             base = "#483D8B"
             out = "#000080"
             size_mult = 1.5

        body_color, outline_color = self.get_state_colors(base, out)
        
        # Stage 3: Tornado wind effects and lightning
        if stage == 3:
            painter.save()
            # Swirling wind lines
            painter.setPen(QPen(QColor(200, 200, 255, 150), 1))
            for i in range(5):
                angle_offset = (self.anim_tick * 0.1 + i * 0.5) % (2 * math.pi)
                start_x = cx + math.cos(angle_offset) * (10 * size_mult)
                start_y = cy - bob + math.sin(angle_offset) * (5 * size_mult)
                end_x = cx + math.cos(angle_offset + math.pi/2) * (30 * size_mult)
                end_y = cy - bob + math.sin(angle_offset + math.pi/2) * (20 * size_mult)
                painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))
            
            # Ground swirl
            ground_swirl_gradient = QRadialGradient(cx, cy + 20, 40)
            ground_swirl_gradient.setColorAt(0, QColor(body_color).darker(150).lighter(50))
            ground_swirl_gradient.setColorAt(1, QColor(body_color).darker(150).lighter(0))
            painter.setBrush(QBrush(ground_swirl_gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(cx, cy + 20), 40, 10)
            painter.restore()
        
        painter.setPen(QPen(outline_color, 2))
        
        # Stage 3 Tornado Body with gradient
        if stage == 3:
            tornado_gradient = QLinearGradient(cx, cy - 30 * size_mult - bob, cx, cy + 30 * size_mult - bob)
            tornado_gradient.setColorAt(0, QColor(body_color).lighter(150))
            tornado_gradient.setColorAt(1, QColor(body_color).darker(150))
            painter.setBrush(QBrush(tornado_gradient))

            path = QPainterPath()
            path.moveTo(cx - 25 * size_mult, cy - 30 * size_mult - bob)
            path.lineTo(cx + 25 * size_mult, cy - 30 * size_mult - bob)
            path.lineTo(cx, cy + 30 * size_mult - bob) # Pointy bottom
            path.closeSubpath()
            painter.drawPath(path)
        
        # Cloud puffs with radial gradient
        cloud_gradient = QRadialGradient(cx, cy - bob, 25 * size_mult)
        cloud_gradient.setColorAt(0, QColor(body_color).lighter(150))
        cloud_gradient.setColorAt(1, QColor(body_color).darker(120))
        painter.setBrush(QBrush(cloud_gradient))

        painter.drawEllipse(QPointF(cx - 20 * size_mult, cy - bob), 20 * size_mult, 20 * size_mult)
        painter.drawEllipse(QPointF(cx + 10 * size_mult, cy - 5 * size_mult - bob), 25 * size_mult, 25 * size_mult)
        painter.drawEllipse(QPointF(cx - 5 * size_mult, cy - 20 * size_mult - bob), 25 * size_mult, 25 * size_mult)
        
        # Lightning (Stage 2+)
        if stage >= 2:
            painter.save()
            painter.setPen(QPen(Qt.GlobalColor.yellow, 2))
            lx = cx + 25 * size_mult
            ly = cy - 10 * size_mult - bob
            painter.drawLine(int(lx), int(ly), int(lx-10 * size_mult), int(ly+10 * size_mult))
            painter.drawLine(int(lx-10 * size_mult), int(ly+10 * size_mult), int(lx * size_mult), int(ly+20 * size_mult))
            painter.restore()

        self.draw_simple_face(painter, cx, cy - 10 * size_mult - bob)
        self.draw_equipped_item(painter, cx, cy, 50 * size_mult, 50 * size_mult, -bob, floating=True)

    def draw_egg(self, painter):
        stage = self.pet_state.evolution_stage
        
        # Try to use sprite image first
        sprite_key = f"egg_{stage}"
        if sprite_key in self.sprites:
            cx = self.width() / 2
            cy = self.height() - 50
            bob_offset = math.sin(self.anim_tick * 0.1) * 2
            
            sprite = self.sprites[sprite_key]
            x = int(cx - sprite.width() / 2)
            y = int(cy - sprite.height() + bob_offset)
            painter.drawPixmap(x, y, sprite)
            self.draw_equipped_item(painter, cx, cy, sprite.width(), sprite.height(), bob_offset)
            return
        
        # Fallback to QPainter rendering
        cx = self.width() / 2
        cy = self.height() - 50
        angle = math.sin(self.anim_tick * 0.1) * 5 
        
        # Stage 3 Dragon is not an egg anymore, handled separately? 
        # Or just transform logic here. 
        if stage >= 2: # Hatchling/Dragon
             self.draw_dragon_form(painter, cx, cy, stage)
             return

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(angle)
        
        body_color, outline_color = self.get_state_colors("#FFFAF0", "#DEB887") 
        
        painter.setPen(QPen(outline_color, 2))
        painter.setBrush(QBrush(body_color))
        
        # Egg shape
        painter.drawEllipse(QPointF(0, -20), 25, 35)
        
        # Cracks
        if self.pet_state.level > 5:
            painter.drawLine(-10, -30, -5, -25)
            painter.drawLine(-5, -25, 0, -35)
            
        self.draw_simple_face(painter, 0, -20)
        painter.restore()
        
        self.draw_equipped_item(painter, cx, cy, 50, 50, 0, floating=True)
        
    def draw_dragon_form(self, painter, cx, cy, stage):
        # Shared logic for Hatchling and Dragon Lord
        bob = math.sin(self.anim_tick * 0.1) * 3
        scale = 1.0
        if stage == 2: scale = 1.4 # Hatchling - bigger
        if stage == 3: scale = 1.8 # Dragon - much bigger!
        
        # Stage 3: Dragon fire aura
        if stage == 3:
            painter.save()
            # Fire aura
            for i in range(4):
                fire_gradient = QRadialGradient(cx, cy - 20, 70 + i*15)
                fire_gradient.setColorAt(0, QColor(255, 150, 0, 100 - i*20))
                fire_gradient.setColorAt(0.5, QColor(255, 100, 0, 70 - i*15))
                fire_gradient.setColorAt(1, QColor(255, 0, 0, 0))
                painter.setBrush(QBrush(fire_gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(cx, cy - 20), 70 + i*15, 55 + i*12)
            # Ember particles
            for j in range(8):
                angle = (self.anim_tick * 0.1 + j * 45) % 360
                rad = math.radians(angle)
                ex = cx + math.cos(rad) * 55
                ey = cy - 20 + math.sin(rad) * 45
                ember_grad = QRadialGradient(ex, ey, 5)
                ember_grad.setColorAt(0, QColor(255, 200, 0, 220))
                ember_grad.setColorAt(1, QColor(255, 100, 0, 0))
                painter.setBrush(QBrush(ember_grad))
                painter.drawEllipse(QPointF(ex, ey), 5, 5)
            painter.restore()
        
        base = "#90EE90" # Light Green
        if stage == 3: base = "#228B22" # Forest Green
        
        body_color, outline_color = self.get_state_colors(base, "#006400")
        
        painter.setPen(QPen(outline_color, 2))
        
        # Wings
        wing_span = 30 * scale
        painter.save()
        wing_gradient = QLinearGradient(cx, cy - 50*scale - bob, cx, cy - 10 - bob)
        wing_gradient.setColorAt(0, QColor("orange").lighter(150))
        wing_gradient.setColorAt(1, QColor("orange").darker(150))
        painter.setBrush(QBrush(wing_gradient)) # Wing membrane
        painter.drawPolygon([QPointF(cx, cy - 20*scale - bob), QPointF(cx - wing_span, cy - 50*scale - bob), QPointF(cx - 10, cy - 10 - bob)])
        painter.drawPolygon([QPointF(cx, cy - 20*scale - bob), QPointF(cx + wing_span, cy - 50*scale - bob), QPointF(cx + 10, cy - 10 - bob)])
        painter.restore()
        
        # Body
        painter.drawEllipse(QPointF(cx, cy - 10 - bob), 25*scale, 25*scale)
        
        # Head
        painter.drawEllipse(QPointF(cx, cy - 35*scale - bob), 20*scale, 18*scale)
        
        # Horns (Stage 3)
        if stage == 3:
             painter.drawLine(int(cx - 10*scale), int(cy - 45*scale - bob), int(cx - 20*scale), int(cy - 60*scale - bob))
             painter.drawLine(int(cx + 10*scale), int(cy - 45*scale - bob), int(cx + 20*scale), int(cy - 60*scale - bob))
             
        # Breath (Fire) - Randomly?
        if stage == 3 and random.random() < 0.05:
             painter.save()
             painter.setBrush(QBrush(Qt.GlobalColor.red))
             painter.setPen(Qt.PenStyle.NoPen)
             painter.drawEllipse(QPointF(cx + 30, cy - 40 - bob), 10, 10)
             painter.restore()

        self.draw_derpy_face(painter, cx, cy - 35*scale - bob)
        self.draw_equipped_item(painter, cx, cy, 50*scale, 50*scale, bob, floating=True)

    # --- Helpers ---
    
    def get_state_colors(self, base, outline):
        if self.pet_state.health < 30:
            return QColor("#708090"), QColor("#2F4F4F") # Sick Slate colors
        if self.pet_state.mood > 80:
            # Slightly brighter/pinker? For simplicity just return base/outline but maybe flash?
            pass
        return QColor(base), QColor(outline)

    def draw_derpy_face(self, painter, cx, cy):
        # Eyes
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.drawEllipse(QPointF(cx - 15, cy - 5), 12, 12) # Left Big
        painter.drawEllipse(QPointF(cx + 20, cy - 5), 8, 8) # Right Small
        
        # Pupils
        painter.setBrush(QBrush(Qt.GlobalColor.black))
        if not self.is_blinking:
            painter.drawEllipse(QPointF(cx - 18, cy - 5), 3, 3) 
            painter.drawEllipse(QPointF(cx + 22, cy - 7), 2, 2)
            
        # Mouth
        painter.setBrush(Qt.BrushStyle.NoBrush)
        mouth_y = cy + 15
        if self.pet_state.mood > 80:
             painter.drawArc(int(cx - 10), int(mouth_y - 5), 20, 15, 0, -180 * 16)
        else:
             painter.drawLine(int(cx - 5), int(mouth_y), int(cx + 5), int(mouth_y))
             painter.setBrush(QBrush(QColor("pink")))
             painter.drawEllipse(QPointF(cx + 2, mouth_y + 2), 4, 6)

    def draw_simple_face(self, painter, cx, cy):
        # Eyes
        painter.setBrush(QBrush(Qt.GlobalColor.black))
        if self.is_blinking:
            painter.drawLine(int(cx - 8), int(cy), int(cx - 2), int(cy))
            painter.drawLine(int(cx + 2), int(cy), int(cx + 8), int(cy))
        else:
            painter.drawEllipse(QPointF(cx - 5, cy), 3, 3)
            painter.drawEllipse(QPointF(cx + 5, cy), 3, 3)
            
        # Mouth
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if self.pet_state.mood > 50:
             painter.drawArc(int(cx - 3), int(cy + 3), 6, 4, 0, -180 * 16)
        else:
             painter.drawLine(int(cx - 3), int(cy + 5), int(cx + 3), int(cy + 5))

    def draw_tough_face(self, painter, cx, cy):
        # Angled Eyes
        painter.setBrush(QBrush(Qt.GlobalColor.black))
        painter.drawLine(int(cx - 10), int(cy - 2), int(cx - 2), int(cy + 2))
        painter.drawLine(int(cx + 10), int(cy - 2), int(cx + 2), int(cy + 2))
        
        # Gritted teeth / Line
        painter.drawLine(int(cx - 5), int(cy + 10), int(cx + 5), int(cy + 10))

    def draw_digital_face(self, painter, cx, cy):
        # Green LED eyes
        painter.setBrush(QBrush(Qt.GlobalColor.green))
        painter.drawRect(int(cx - 10), int(cy), 5, 5)
        painter.drawRect(int(cx + 5), int(cy), 5, 5)
        
    def draw_limbs(self, painter, cx, cy, w, h, bob, body_rect, stick=True):
        # Re-use the stick limb logic for Default type
        arm_y = body_rect.top() + 5
        leg_y = body_rect.bottom() - 5
        arm_swing = math.sin(self.anim_tick * 0.2) * 5
        
        # Left Arm
        if self.current_action == "stretch":
             painter.drawLine(int(cx - w/2), int(arm_y), int(cx - w/2 - 20), int(arm_y - 30))
        else:
             painter.drawLine(int(cx - w/2), int(arm_y), int(cx - w/2 - 15), int(arm_y + 10 + arm_swing))

        # Right Arm (Handled by draw_equipped_item generally, but for simple limbs we draw base arm)
        right_hand_x = cx + w/2 + 15
        right_hand_y = arm_y + 10 - arm_swing
        
        if self.current_action == "stretch":
            right_hand_x = cx + w/2 + 20
            right_hand_y = arm_y - 30
            painter.drawLine(int(cx + w/2), int(arm_y), int(right_hand_x), int(right_hand_y))
        else:
            painter.drawLine(int(cx + w/2), int(arm_y), int(right_hand_x), int(right_hand_y))

        # Legs
        painter.drawLine(int(cx - 10), int(leg_y), int(cx - 10), int(leg_y + 15))
        painter.drawLine(int(cx + 10), int(leg_y), int(cx + 10), int(leg_y + 15))

    def draw_equipped_item(self, painter, cx, cy, w, h, bob, floating=False):
        if self.equipped_item != "sword":
            return
            
        # Calculate Hand Position based on Type
        # Default right hand pos approx
        if floating:
            cutoff_x = cx + 40
            cutoff_y = cy - bob # Roughly float aside
        else:
            # Linked to arm logic mostly, approximate here
            bg = self.height() - 50
            cutoff_x = cx + w/2 + 15
            cutoff_y = cy - h/2 - bob + 30 # Rough guess
            
        self.draw_sword(painter, cutoff_x, cutoff_y)

    def draw_sword(self, painter, hand_x, hand_y):
        painter.save()
        painter.translate(hand_x, hand_y)
        painter.rotate(-45) 
        
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.setBrush(QBrush(QColor("brown")))
        painter.drawRect(-2, -5, 4, 10) 
        
        painter.setBrush(QBrush(QColor("gold")))
        painter.drawRect(-6, -5, 12, 3)
        
        painter.setBrush(QBrush(QColor("silver")))
        painter.drawPolygon(
            QPointF(-3, -5),
            QPointF(-3, -35),
            QPointF(0, -40), 
            QPointF(3, -35),
            QPointF(3, -5)
        )
        painter.restore()

    # Mouse Interaction (Same as before)
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
            self.clicked.emit()
            self.anim_tick = 0 
            self.current_action = "jump"
            QTimer.singleShot(500, lambda: setattr(self, 'current_action', 'idle'))

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()

    def set_action(self, action_name, duration_ms=2000):
        self.current_action = action_name
        QTimer.singleShot(duration_ms, lambda: setattr(self, 'current_action', 'idle'))

    def set_equip(self, item_name):
        self.equipped_item = item_name
