import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, 
                             QProgressBar, QHBoxLayout, QGridLayout)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer

class Monster:
    def __init__(self, name, hp, damage, is_boss=False):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.damage = damage
        self.is_boss = is_boss

class DungeonGame(QWidget):
    # 전투 종료 시그널 (승리 여부, 골드 보상)
    battle_finished = pyqtSignal(bool, int)

    def __init__(self, pet_state):
        super().__init__()
        self.pet_state = pet_state
        self.monster = None
        self.is_defending = False # 방어 태세
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("⚔️ 미니 던전 2.0 ⚔️")
        self.setGeometry(350, 350, 450, 400)
        
        layout = QVBoxLayout()
        
        # 스테이지 정보
        self.stage_label = QLabel(f"STAGE {self.pet_state.dungeon_stage}")
        self.stage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stage_label.setStyleSheet("font-size: 20px; font-weight: bold; color: blue;")
        layout.addWidget(self.stage_label)

        # 몬스터 정보
        self.monster_label = QLabel("야생의 버그가 나타났다!")
        self.monster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.monster_label.setStyleSheet("font-size: 16px; font-weight: bold; color: red;")
        layout.addWidget(self.monster_label)
        
        self.monster_hp_bar = QProgressBar()
        self.monster_hp_bar.setStyleSheet("QProgressBar::chunk { background-color: purple; }")
        self.monster_hp_bar.setFixedHeight(20)
        layout.addWidget(self.monster_hp_bar)
        
        layout.addSpacing(10)

        # 펫 정보
        self.pet_label = QLabel(f"나의 펫 (Lv.{self.pet_state.level})")
        self.pet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.pet_label)
        
        # HP Bar
        self.pet_hp_bar = QProgressBar()
        self.pet_hp_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")
        self.pet_hp_bar.setFormat("HP: %v/%m")
        self.pet_hp_bar.setFixedHeight(20)
        layout.addWidget(self.pet_hp_bar)

        # MP Bar
        self.pet_mp_bar = QProgressBar()
        self.pet_mp_bar.setStyleSheet("QProgressBar::chunk { background-color: #00BFFF; }") # Deep Sky Blue
        self.pet_mp_bar.setFormat("MP: %v/%m")
        self.pet_mp_bar.setFixedHeight(20)
        layout.addWidget(self.pet_mp_bar)

        # 로그
        self.log_label = QLabel("전투 대기 중...")
        self.log_label.setWordWrap(True)
        self.log_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.log_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        self.log_label.setFixedHeight(60)
        layout.addWidget(self.log_label)

        # 액션 버튼 그리드
        btn_layout = QGridLayout()
        
        self.btn_attack = QPushButton("⚔️ 공격")
        self.btn_attack.clicked.connect(self.action_attack)
        btn_layout.addWidget(self.btn_attack, 0, 0)

        self.btn_defend = QPushButton("🛡️ 방어")
        self.btn_defend.clicked.connect(self.action_defend)
        btn_layout.addWidget(self.btn_defend, 0, 1)

        self.btn_skill1 = QPushButton("🔥 파이어볼 (20MP)")
        self.btn_skill1.clicked.connect(lambda: self.action_skill("fireball"))
        btn_layout.addWidget(self.btn_skill1, 1, 0)

        self.btn_skill2 = QPushButton("💊 힐 (15MP)")
        self.btn_skill2.clicked.connect(lambda: self.action_skill("heal"))
        btn_layout.addWidget(self.btn_skill2, 1, 1)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def start_battle(self):
        stage = self.pet_state.dungeon_stage
        self.stage_label.setText(f"STAGE {stage}")
        self.is_defending = False
        
        # 보스 스테이지 확인 (5의 배수)
        is_boss_stage = (stage % 5 == 0)
        
        if is_boss_stage:
            self.monster = self.generate_boss(stage)
            self.log_label.setStyleSheet("background-color: #ffcccc; padding: 10px; border-radius: 5px;") # 붉은 배경
            self.log(f"⚠️ 경고! 보스 '{self.monster.name}'(이)가 나타났다!")
        else:
            self.monster = self.generate_monster(stage)
            self.log_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
            self.log(f"야생의 '{self.monster.name}'(이)가 나타났다!")

        # 펫 스탯 재계산 (최신 상태 반영)
        self.pet_state.recalc_stats()
        self.refresh_ui()
        self.show()
        self.enable_buttons(True)

    def generate_monster(self, stage):
        # 스테이지가 오를수록 강해짐 (+10% per stage approx)
        scale = 1.0 + (stage * 0.1)
        
        monsters = [
            ("Null Pointer", 40, 5),
            ("Infinite Loop", 60, 8),
            ("Glitched Slime", 80, 10),
            ("Memory Leak", 100, 12),
            ("Spaghetti Code", 120, 15)
        ]
        name, base_hp, base_dmg = random.choice(monsters)
        
        hp = int(base_hp * scale)
        dmg = int(base_dmg * scale)
        
        return Monster(name, hp, dmg)

    def generate_boss(self, stage):
        scale = 1.0 + (stage * 0.15) # 보스는 스케일링이 더 큼
        
        bosses = [
            ("Blue Screen Dragon", 300, 25),
            ("Ransomware King", 400, 30),
            ("The Deadline", 500, 40)
        ]
        name, base_hp, base_dmg = random.choice(bosses)
        
        hp = int(base_hp * scale)
        dmg = int(base_dmg * scale)
        
        return Monster(f"[BOSS] {name}", hp, dmg, is_boss=True)

    def refresh_ui(self):
        if self.monster:
            self.monster_label.setText(f"👾 {self.monster.name}")
            self.monster_hp_bar.setRange(0, self.monster.max_hp)
            self.monster_hp_bar.setValue(max(0, self.monster.hp))
            self.monster_hp_bar.setFormat(f"HP: {self.monster.hp}/{self.monster.max_hp}")

        self.pet_hp_bar.setRange(0, int(self.pet_state.max_health))
        self.pet_hp_bar.setValue(int(max(0, self.pet_state.health)))
        
        self.pet_mp_bar.setRange(0, int(self.pet_state.max_mana))
        self.pet_mp_bar.setValue(int(max(0, self.pet_state.mana)))

    def log(self, text):
        self.log_label.setText(text)

    # --- Actions ---

    def action_attack(self):
        # 기본 공격
        dmg = int(self.pet_state.attack) + random.randint(-2, 2)
        # 치명타 확률 (지능/행운?)
        if random.random() < 0.1: # 10% Critical
            dmg = int(dmg * 1.5)
            self.log(f"💥 치명타! {dmg}의 데미지를 입혔다!")
        else:
            self.log(f"⚔️ 공격! {dmg}의 데미지를 입혔다.")
            
        self.monster.hp -= dmg
        self.end_player_turn()

    def action_defend(self):
        # 방어 (다음 턴 데미지 감소)
        self.is_defending = True
        self.log("🛡️ 방어 태세를 취했다! (피해량 감소)")
        self.end_player_turn()

    def action_skill(self, skill_name):
        if skill_name == "fireball":
            cost = 20
            if self.pet_state.mana < cost:
                self.log("마나가 부족합니다!")
                return
            
            self.pet_state.mana -= cost
            dmg = int(self.pet_state.attack * 2.5) # 강력한 한방
            self.monster.hp -= dmg
            self.log(f"🔥 파이어볼!! {dmg}의 화염 데미지!")
            self.end_player_turn()
            
        elif skill_name == "heal":
            cost = 15
            if self.pet_state.mana < cost:
                self.log("마나가 부족합니다!")
                return

            self.pet_state.mana -= cost
            heal = int(self.pet_state.max_health * 0.3)
            self.pet_state.health = min(self.pet_state.max_health, self.pet_state.health + heal)
            self.log(f"💉 자가수복! 체력을 {heal} 회복했다.")
            self.end_player_turn()

    def end_player_turn(self):
        self.refresh_ui()
        self.enable_buttons(False) # 버튼 비활성화
        
        if self.monster.hp <= 0:
            self.win_battle()
        else:
            QTimer.singleShot(1000, self.monster_turn)

    def monster_turn(self):
        # 회피 체크
        evasion_chance = self.pet_state.evasion / 100.0
        if random.random() < evasion_chance:
            self.log(f"⚡ {self.monster.name}의 공격을 날렵하게 피했다!")
            self.enable_buttons(True)
            self.is_defending = False
            return

        damage = self.monster.damage + random.randint(-2, 2)
        
        # 보스 스킬 (가끔 2배 데미지)
        if self.monster.is_boss and random.random() < 0.3:
            damage = int(damage * 1.5)
            self.log(f"🐲 {self.monster.name}의 강력한 스킬 공격!")
        
        # 방어 감소
        if self.is_defending:
            damage = int(damage * 0.5)
            self.is_defending = False
        
        # 펫 방어력(Defense Stat) 적용
        damage = max(1, damage - int(self.pet_state.defense))

        self.pet_state.health -= damage
        self.log(f"💥 '{self.monster.name}'에게 {damage}의 피해를 입었다!")
        self.refresh_ui()
        
        if self.pet_state.health <= 0:
            self.lose_battle()
        else:
            self.enable_buttons(True)

    def enable_buttons(self, enable):
        self.btn_attack.setEnabled(enable)
        self.btn_defend.setEnabled(enable)
        
        # 마나 없으면 스킬 버튼 비활성화 체크
        self.btn_skill1.setEnabled(enable and self.pet_state.mana >= 20)
        self.btn_skill2.setEnabled(enable and self.pet_state.mana >= 15)

    def win_battle(self):
        # 스테이지 클리어
        gold = random.randint(20, 50) * self.pet_state.dungeon_stage
        exp = 30 * self.pet_state.dungeon_stage
        
        if self.monster.is_boss:
            gold *= 5
            exp *= 5
            QMessageBox.information(self, "BOSS CLEARED!", f"보스를 처치했습니다!\n엄청난 보상!\n{gold} G, {exp} Exp")
        else:
            # 일반 몬스터 잡으면 확률로 마나 회복?
            pass

        self.pet_state.gold += gold
        self.pet_state.gain_exp(exp)
        
        # 다음 스테이지로
        self.pet_state.dungeon_stage += 1
        
        self.battle_finished.emit(True, gold)
        self.close()

    def lose_battle(self):
        QMessageBox.critical(self, "패배...", "펫이 기절했습니다.\n(스테이지는 유지됩니다)")
        self.battle_finished.emit(False, 0)
        self.close()
