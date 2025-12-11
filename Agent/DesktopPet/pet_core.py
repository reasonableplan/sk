import json
import os
from datetime import datetime

class PetState:
    def __init__(self):
        self.name = "DesktopPet"
        self.level = 1
        self.exp = 0
        self.max_exp = 100
        
        # Stats
        self.health = 100.0 # 체력 (자세/휴식)
        self.max_health = 100.0
        self.intellect = 10.0 # 지능 (영어 퀴즈)
        self.mood = 50.0 # 기분 (0~100)
        self.hunger = 50.0 # 배고픔 (0~100, 100이면 배부름)
        self.gold = 0 # 재화
        self.character_type = "default" # default, slime, rock, dog, ghost, robot, cloud, egg
        
        # Evolution Stats
        self.evolution_stage = 1 # 1: 기본, 2: 1차 진화, 3: 2차 진화
        
        # Dungeon Stats
        self.dungeon_stage = 1
        self.max_mana = 100.0
        self.mana = 100.0
        self.attack = 10.0
        self.defense = 0.0
        self.evasion = 5.0 # percentage
        
        self.last_update = datetime.now()
        self.load_state()
        self.sync_evolution_stage() # Ensure stage matches level
        self.recalc_stats() # Load 후 스탯 재계산
    
    def sync_evolution_stage(self):
        """레벨에 맞춰 진화 단계 동기화"""
        if self.level >= 20:
            self.evolution_stage = 3
        elif self.level >= 10:
            self.evolution_stage = 2
        else:
            self.evolution_stage = 1

    def get_evolution_name(self):
        """현재 캐릭터 타입과 단계에 따른 이름 반환"""
        evo_map = {
            "default": {1: "감자", 2: "감자 전사", 3: "제왕 감자"},
            "slime":   {1: "슬라임", 2: "메가 슬라임", 3: "슬라임 킹"},
            "rock":    {1: "조약돌", 2: "골렘", 3: "마그마 타이탄"},
            "dog":     {1: "멍멍이", 2: "늑대", 3: "푸른 불꽃 펜릴"},
            "ghost":   {1: "꼬마 유령", 2: "팬텀", 3: "죽음의 리퍼"},
            "robot":   {1: "깡통 로봇", 2: "안드로이드", 3: "메카 워로드"},
            "cloud":   {1: "솜사탕", 2: "먹구름", 3: "폭풍의 정령"},
            "egg":     {1: "알", 2: "해츨링", 3: "드래곤 로드"},
        }
        type_map = evo_map.get(self.character_type, evo_map["default"])
        return type_map.get(self.evolution_stage, "알 수 없음")

    # ... (recalc_stats, update_time_based_stats 생략: 변경 없음) ...

    def recalc_stats(self):
        """레벨과 지능에 따라 전투 스탯 재계산"""
        # 기본 스탯 + (레벨 보정) + (지능 보정)
        # 진화 단계에 따른 보너스 추가
        evo_bonus = (self.evolution_stage - 1) * 10
        
        self.max_health = 100 + (self.level * 10) + evo_bonus
        self.max_mana = 50 + (self.intellect * 2) + evo_bonus
        self.attack = 5 + (self.level * 2) + (self.intellect * 0.5) + (evo_bonus / 2)
        self.defense = self.level * 1 + (evo_bonus / 2)
        self.evasion = 5 + (self.intellect * 0.1) # 지능 높으면 회피율 소폭 상승

    def update_time_based_stats(self):
        """시간 경과에 따른 상태 변화 (배고픔 증가, 기분 감소 등)"""
        now = datetime.now()
        delta = (now - self.last_update).total_seconds()
        self.last_update = now

        # 예: 10분에 배고픔 1 감소, 기분 0.5 감소
        # delta는 초 단위
        minutes_passed = delta / 60
        
        self.hunger = max(0, self.hunger - (minutes_passed * 0.1))
        self.health = max(0, self.health - (minutes_passed * 0.05)) # 시간이 지나면 피로도 쌓임(체력 감소)
        self.mana = min(self.max_mana, self.mana + (minutes_passed * 0.5)) # 마나 자연 회복
        
        # 배고프거나 아프면 기분 나빠짐
        if self.hunger < 30 or self.health < 30:
            self.mood = max(0, self.mood - (minutes_passed * 0.2))

    def gain_exp(self, amount):
        self.exp += amount
        if self.exp >= self.max_exp:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.exp -= self.max_exp
        self.max_exp = int(self.max_exp * 1.2)
        self.intellect += 2
        
        # 진화 체크
        old_stage = self.evolution_stage
        if self.level >= 20:
            self.evolution_stage = 3
        elif self.level >= 10:
            self.evolution_stage = 2
        
        # 진화 시 추가 보상 (UI에서 체크 가능하도록 로직은 분리하면 좋지만 일단 여기서)
        if self.evolution_stage > old_stage:
            # 진화 축하 (추후 UI 연동)
            pass

        self.recalc_stats()
        self.health = self.max_health
        self.mana = self.max_mana

    def feed(self, food_value):
        self.hunger = min(100, self.hunger + food_value)
        self.mood = min(100, self.mood + (food_value * 0.5))

    def study(self, int_gain):
        self.intellect += int_gain
        self.gain_exp(int_gain * 2)
        self.hunger = max(0, self.hunger - 5) # 공부하면 배고픔

    def exercise(self, hp_gain):
        self.health = min(self.max_health, self.health + hp_gain)
        self.gain_exp(hp_gain)
        self.hunger = max(0, self.hunger - 5) # 운동하면 배고픔

    def save_state(self):
        data = {
            "name": self.name,
            "level": self.level,
            "exp": self.exp,
            "max_exp": self.max_exp,
            "health": self.health,
            "max_health": self.max_health,
            "intellect": self.intellect,
            "mood": self.mood,
            "hunger": self.hunger,
            "gold": self.gold,
            "character_type": self.character_type,
            "evolution_stage": self.evolution_stage, # 추가
            "dungeon_stage": self.dungeon_stage,
            "last_update": self.last_update.isoformat()
        }
        try:
            with open("pet_state.json", "w", encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Save failed: {e}")

    def load_state(self):
        if not os.path.exists("pet_state.json"):
            return

        try:
            with open("pet_state.json", "r", encoding='utf-8') as f:
                data = json.load(f)
            
            self.name = data.get("name", "DesktopPet")
            self.level = data.get("level", 1)
            self.exp = data.get("exp", 0)
            self.max_exp = data.get("max_exp", 100)
            self.health = data.get("health", 100.0)
            self.max_health = data.get("max_health", 100.0)
            self.intellect = data.get("intellect", 10.0)
            self.mood = data.get("mood", 50.0)
            self.hunger = data.get("hunger", 50.0)
            self.gold = data.get("gold", 0)
            self.character_type = data.get("character_type", "default")
            self.evolution_stage = data.get("evolution_stage", 1) # 추가
            self.dungeon_stage = data.get("dungeon_stage", 1)
            
            last_update_str = data.get("last_update")
            if last_update_str:
                self.last_update = datetime.fromisoformat(last_update_str)
                self.last_update = datetime.now() # 재접속 시점부터 다시 계산
                
        except Exception as e:
            print(f"Load failed: {e}")
